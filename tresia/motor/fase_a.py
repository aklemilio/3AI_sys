"""Fase A (abrir opciones), verificación A y fusión (SPEC §4.4–4.6).

Los tres modelos exploran a ciegas y en paralelo. La verificación A es determinista:
cuotas, técnicas T1–T7, etapas de la cadena, nombres legibles y registro de fuentes.
La fusión la propone el verificador y el motor la comprueba (asignación única).
"""

from __future__ import annotations

from tresia.calculo.fusion import indexar_exploradores, MAX_PALABRAS_NOMBRE
from tresia.motor import manual, pasos
from tresia.motor.encuadre import materiales_para_papeles
from tresia.motor.ejecucion import Ejecucion
from tresia.motor.llamadas import asignacion_ciega
from tresia.calculo.fuentes import VERIFICADA
from tresia.motor.verificador import NO_VERIFICADAS, registrar_fuentes_de_salida

EXPLORADORES = ["E1", "E2", "E3"]
TECNICAS = [f"T{i}" for i in range(1, 8)]
PASO_FASE_A = "fase_a"
PASO_FUSION = "fusion"


def _encuadre_para_papeles(ficha: dict) -> dict:
    """Lo que ven los papeles del encuadre (nunca el contexto ni la línea base)."""
    return {
        "decision": ficha.get("decision"),
        "fixed_and_questionable": ficha.get("fijo_y_cuestionable"),
        "must_cover": ficha.get("cobertura_obligatoria"),
        "for_whom_and_who_could_be_left_out": ficha.get("destinatarios"),
        "faces": ficha.get("caras"),
        "must_not_use_or_reveal": ficha.get("prohibiciones"),
        "critical": ficha.get("criticos"),
    }


def preparar_fase_a(run: Ejecucion) -> dict[str, str]:
    ficha = run.leer("ficha.json")
    cuotas = ficha.get("cuotas_fase_a", {})
    entradas = {
        "objective": ficha["objetivo"],
        "framing": _encuadre_para_papeles(ficha),
        "chain_stages": ficha.get("etapas", []),
        "quotas": {
            "number_of_options": f"{cuotas.get('opciones_min', 15)}–{cuotas.get('opciones_max', 25)}",
            "minimum_share_not_depending_on_ai": f"{cuotas.get('min_sin_ia', 1 / 3):.0%}",
            "at_least_one_option_per_chain_stage": bool(cuotas.get("una_por_etapa", True)),
        },
        "materials": materiales_para_papeles(run, para_fase_a=True),
    }
    asignacion = asignacion_ciega(run, "fase_a", EXPLORADORES)
    return {e: manual.preparar_ficha(run, PASO_FASE_A, e, "explorer", entradas, f"faseA/{e}.json",
                                     asignado=asignacion[e]) for e in EXPLORADORES}


def verificar_fase_a(run: Ejecucion) -> dict:
    """Verificación A determinista. No bloquea: deja avisos visibles para el dueño."""
    ficha = run.leer("ficha.json")
    cuotas = ficha.get("cuotas_fase_a", {})
    etapas = ficha.get("etapas", [])
    informe, avisos = {}, []
    for e in EXPLORADORES:
        if not run.existe(f"faseA/{e}.json"):
            avisos.append(f"Explorador {e[1]}: sin respuesta.")
            continue
        salida = run.leer(f"faseA/{e}.json")
        ops = salida["options"]
        n = len(ops)
        sin_ia = sum(not o.get("depends_on_ai") for o in ops)
        tecnicas = sorted({o["technique"] for o in ops})
        etapas_cubiertas = sorted({o["chain_stage"] for o in ops})
        fuera = sorted({o["chain_stage"] for o in ops} - set(etapas)) if etapas else []
        largos = [o["id"] for o in ops if len(o["name"].split()) > MAX_PALABRAS_NOMBRE]
        n_fuentes = registrar_fuentes_de_salida(run, salida, f"faseA:{e}")
        informe[e] = {"opciones": n, "sin_ia": sin_ia, "tecnicas": tecnicas, "etapas": etapas_cubiertas,
                      "etapas_desconocidas": fuera, "nombres_largos": largos, "fuentes_citadas": n_fuentes}
        nombre = f"Explorador {e[1]}"
        if n < cuotas.get("opciones_min", 0) or n > cuotas.get("opciones_max", 10**6):
            avisos.append(f"{nombre}: {n} opciones, fuera de la cuota "
                          f"({cuotas.get('opciones_min')}–{cuotas.get('opciones_max')}).")
        if n and sin_ia / n < cuotas.get("min_sin_ia", 0) - 1e-9:
            avisos.append(f"{nombre}: solo {sin_ia} de {n} opciones no dependen de IA.")
        if faltan := [t for t in TECNICAS if t not in tecnicas]:
            avisos.append(f"{nombre}: faltan las técnicas {', '.join(faltan)}.")
        if cuotas.get("una_por_etapa", True) and (faltan_e := [s for s in etapas if s not in etapas_cubiertas]):
            avisos.append(f"{nombre}: no cubre las etapas {', '.join(faltan_e)}.")
        if fuera:
            avisos.append(f"{nombre}: usa etapas que no están en la ficha: {', '.join(fuera)}.")
        if largos:
            avisos.append(f"{nombre}: nombres de más de {MAX_PALABRAS_NOMBRE} palabras en {', '.join(largos)}.")
    # Fuentes de la fase A comprobadas en línea por el motor (no por quien las cita).
    de_fase_a = [e for e in (run.leer("fuentes.json").values() if run.existe("fuentes.json") else [])
                 if any(c.startswith("faseA:") for c in e["citada_en"])]
    verificadas = sum(e["estado"] == VERIFICADA for e in de_fase_a)
    no_verificadas = sum(e["estado"] in NO_VERIFICADAS for e in de_fase_a)
    if no_verificadas:
        avisos.append(f"{no_verificadas} de {len(de_fase_a)} fuentes citadas en la fase A no se pudieron verificar "
                      "(fragmento ausente o página inaccesible).")
    resultado = {"por_explorador": informe, "avisos": avisos}
    run.escribir("faseA/verificacion.json", resultado)
    run.actualizar_metricas("fase_a", {
        "opciones": sum(v["opciones"] for v in informe.values()),
        "por_explorador": {e: v["opciones"] for e, v in informe.items()},
        "sin_ia": sum(v["sin_ia"] for v in informe.values()),
        "fuentes_citadas": sum(v["fuentes_citadas"] for v in informe.values()),
        "fuentes_verificadas": verificadas,
        "fuentes_no_verificadas": no_verificadas,
        "avisos": len(avisos),
    })
    return resultado


def preparar_fusion(run: Ejecucion) -> str:
    """Ficha de la tarea «merge» para el verificador."""
    exploradores = {e: run.leer(f"faseA/{e}.json") for e in EXPLORADORES if run.existe(f"faseA/{e}.json")}
    opciones = [{"ref": ref, "name": o["name"], "description": o["description"], "chain_stage": o["chain_stage"],
                 "depends_on_ai": o.get("depends_on_ai", False)}
                for ref, o in indexar_exploradores(exploradores).items()]
    linea_base = run.leer("linea_base.json")["opciones"] if run.existe("linea_base.json") else []
    entradas = {"baseline": [b["name"] for b in linea_base], "options": opciones,
                "group_ids": "Use C01, C02, … in order."}
    return manual.preparar_ficha(run, PASO_FUSION, "V", "verifier", entradas, "fusion_verificador.json",
                                 tarea="merge", asignado="verificador")


def cerrar_fusion(run: Ejecucion) -> dict:
    """Comprueba los grupos del verificador (o corregidos por el dueño) y mide."""
    return pasos.registrar_fusion(run, run.leer("fusion_verificador.json"))
