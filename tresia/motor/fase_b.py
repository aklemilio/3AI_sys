"""Ciclo de la fase B (SPEC §4.10), con la rotación en cuadrado latino.

Pasos de cada ciclo:
  constructor → verificacion → ataque → verificacion_ataque → arbitraje →
  disposiciones (⛔ tarjetas) → correccion → verificacion_correccion → veredicto →
  adopcion (⛔: adoptar, última pasada u otro ciclo)

Los pasos con modelo preparan fichas (modo manual o automático); los deterministas
se ejecutan solos; los ⛔ esperan una decisión registrada del dueño.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from tresia.calculo.fuentes import VERIFICADA
from tresia.motor import manual
from tresia.motor.encuadre import materiales_para_papeles
from tresia.motor.ejecucion import Ejecucion
from tresia.motor.llamadas import rotacion
from tresia.motor.pasos import opciones_para_criba
from tresia.motor.verificador import (aplicar_comprobacion_a_afirmaciones, comprobacion_activa, estado_de_fuentes,
                                      registrar_fuentes_de_salida, verificar_version)

PASOS_B = ["constructor", "verificacion", "ataque", "verificacion_ataque", "arbitraje", "disposiciones",
           "correccion", "verificacion_correccion", "veredicto", "adopcion"]
PASOS_CON_MODELO = {"constructor", "verificacion", "ataque", "arbitraje", "correccion", "veredicto", "ultima_pasada"}
PASOS_DUENO = {"disposiciones", "adopcion"}
ACCIONES_CIERRE = ("adoptar", "ultima_pasada", "otro_ciclo")


# --- estado ---------------------------------------------------------------------------------
def estado_b(run: Ejecucion) -> dict:
    with run.cerrojo:
        if "fase_b" not in run.estado:
            run.estado["fase_b"] = {"ciclo": 1, "paso": "constructor", "versiones": []}
            run.guardar()
        return run.estado["fase_b"]


def _carpeta(ciclo: int) -> str:
    return f"faseB/ciclo_{ciclo}"


def nombre_paso(ciclo: int, paso: str) -> str:
    return f"b{ciclo}_{paso}"


def _ir_a(run: Ejecucion, paso: str) -> None:
    with run.cerrojo:
        run.estado["fase_b"]["paso"] = paso
        if run.estado["fases"].get("fase_b") == "espera_dueno":
            run.estado["fases"]["fase_b"] = "en_curso"
        run.guardar()


def version_actual(run: Ejecucion) -> dict | None:
    v = estado_b(run)["versiones"]
    return v[-1] if v else None


def _anterior(run: Ejecucion) -> dict | None:
    v = estado_b(run)["versiones"]
    return v[-2] if len(v) > 1 else None


def _registrar_version(run: Ejecucion, nombre: str, ruta: str, cambios: str, paso: str) -> dict:
    with run.cerrojo:
        b = run.estado["fase_b"]
        entrada = {"nombre": nombre, "ruta": ruta, "cambios": cambios, "ciclo": b["ciclo"], "paso": paso}
        b["versiones"].append(entrada)
        run.guardar()
        return entrada


# --- entradas comunes -------------------------------------------------------------------------
def decisiones_vinculantes(run: Ejecucion) -> list[str]:
    """Decisiones del dueño que obligan a los papeles (lección: son vinculantes)."""
    salida = [d["texto"] for d in run.decisiones() if d["tipo"] == "decision_vinculante"]
    salida += [f"Portfolio: {d['motivo'] or 'owner decision'} ({d['tipo']} {', '.join(d['ids'])})"
               for d in run.decisiones("cartera") if d["tipo"] in ("anadir", "quitar")]
    return salida


def registrar_decision_vinculante(run: Ejecucion, texto: str) -> None:
    run.registrar_decision(run.fase_actual, "decision_vinculante", {"texto": texto})


def _registro_fuentes_verificadas(run: Ejecucion) -> list[dict]:
    if not run.existe("fuentes.json"):
        return []
    return [{"url": e["url"], "fragment": e["fragmento"], "claims": e["afirmaciones"]}
            for e in run.leer("fuentes.json").values() if e["estado"] == VERIFICADA]


def _cartera_para_constructor(run: Ejecucion) -> list[dict]:
    grupos = run.leer("grupos.json")
    exploradores = {e: run.leer(f"faseA/{e}.json") for e in ("E1", "E2", "E3") if run.existe(f"faseA/{e}.json")}
    detalle = {o["id"]: o for o in opciones_para_criba(grupos, exploradores)}
    cribas = [run.leer(f"criba/{s}.json") for s in ("S1", "S2", "S3") if run.existe(f"criba/{s}.json")]
    salida = []
    for s in run.leer("cartera.json")["seleccion"]:
        d = detalle.get(s["id"], {})
        condiciones = []
        for c in cribas:
            for a in c["assessments"]:
                if a["id"] == s["id"]:
                    if a.get("note"):
                        condiciones.append(a["note"])
                    if a.get("rescue"):
                        condiciones.append(f"Rescue: {a['rescue']}")
        salida.append({"id": s["id"], "name": s["name"], "description": d.get("description", s.get("name")),
                       "variants": d.get("variants", []), "chain_stage": s.get("stage", ""),
                       "why_selected": s["motivo"], "conditions_from_screeners": condiciones})
    return salida


def _notas_verificador(run: Ejecucion, ciclo: int, version: str) -> dict:
    ruta = f"{_carpeta(ciclo)}/notas_verificador_{version}.json"
    notas = run.leer(ruta) if run.existe(ruta) else {}
    extra = {}
    for tarea in ("claims", "timeline", "compliance"):
        r = f"{_carpeta(ciclo)}/verificador_{tarea}_{version}.json"
        if run.existe(r):
            extra[tarea] = run.leer(r)
    # Lo que el motor comprobó en línea de las fuentes que cita esta versión.
    v = next((x for x in estado_b(run)["versiones"] if x["nombre"] == version), None)
    texto = texto_completo(run, v) if v else ""
    fuentes = [f for f in estado_de_fuentes(run) if f["url"] in texto]
    return {"deterministic_alerts": notas.get("alertas", []), "word_counts": notas.get("recuento", {}),
            "source_checks_by_engine": fuentes, **extra}


def _hallazgos_con_disposiciones(run: Ejecucion, ciclo: int) -> list[dict]:
    carpeta = _carpeta(ciclo)
    ataque = run.leer(f"{carpeta}/ataque.json") if run.existe(f"{carpeta}/ataque.json") else {"findings": []}
    disp = run.leer(f"{carpeta}/disposiciones.json") if run.existe(f"{carpeta}/disposiciones.json") else {}
    return [{**h, "owner_disposition": disp.get(h["id"], {}).get("opcion", "not decided"),
             "owner_note": disp.get(h["id"], {}).get("nota", "")} for h in ataque.get("findings", [])]


# --- preparación de cada paso con modelo -------------------------------------------------------
def _preparar(run: Ejecucion, paso: str) -> None:
    b = estado_b(run)
    ciclo, carpeta = b["ciclo"], _carpeta(b["ciclo"])
    rot = rotacion(ciclo)
    ficha = run.leer("ficha.json")
    comunes = {"objective": ficha["objetivo"], "owner_decisions": decisiones_vinculantes(run),
               "owner_principles": ficha.get("principios", [])}
    np = nombre_paso(ciclo, paso)
    actual = version_actual(run)

    if paso == "constructor":
        nombre = f"v{ciclo}"
        if ciclo == 1 or actual is None:
            entradas = {"mode": "build", **comunes, "portfolio": _cartera_para_constructor(run),
                        "materials": materiales_para_papeles(run)}
        else:
            entradas = {"mode": "correct", **comunes, "previous_version": run.leer(actual["ruta"]),
                        "findings_with_dispositions": _pendientes_del_ciclo_anterior(run, ciclo - 1)}
        entradas |= {"length_limits": ficha.get("limites", {}), "forbidden_content": ficha.get("prohibiciones"),
                     "source_register": _registro_fuentes_verificadas(run)}
        manual.preparar_ficha(run, np, "constructor", "builder", entradas, f"{carpeta}/cambios_{nombre}.json",
                              asignado=rot["constructor"], destino_texto=f"{carpeta}/version_{nombre}.md")

    elif paso == "verificacion":
        texto = run.leer(actual["ruta"])
        for tarea, entradas in (
            ("claims", {"text": texto}),
            ("timeline", {"text": texto}),
            ("compliance", {"text": texto, "owner_decisions": comunes["owner_decisions"]}),
        ):
            manual.preparar_ficha(run, np, tarea, "verifier", entradas,
                                  f"{carpeta}/verificador_{tarea}_{actual['nombre']}.json",
                                  tarea=tarea, asignado="verificador")

    elif paso == "ataque":
        entradas = {"version": run.leer(actual["ruta"]), "change_register": run.leer(actual["cambios"]),
                    "verifier_notes": _notas_verificador(run, ciclo, actual["nombre"]), **comunes,
                    "faces": ficha.get("caras", []), "focus": ficha.get("foco_ataque", [])}
        manual.preparar_ficha(run, np, "atacante", "attacker", entradas, f"{carpeta}/ataque.json",
                              asignado=rot["atacante"])

    elif paso == "arbitraje":
        ataque = run.leer(f"{carpeta}/ataque.json")
        entradas = {"findings": ataque["findings"], "additions": ataque.get("additions", []), **comunes}
        manual.preparar_ficha(run, np, "arbitro", "verifier", entradas, f"{carpeta}/tarjetas.json",
                              tarea="arbitrate", asignado="verificador")

    elif paso in ("correccion", "ultima_pasada"):
        sufijo = ".1" if paso == "correccion" else f".{sum(v['ciclo'] == ciclo for v in b['versiones'])}"
        nombre = f"v{ciclo}{sufijo}"
        hallazgos = (_hallazgos_con_disposiciones(run, ciclo) if paso == "correccion"
                     else _condiciones_del_veredicto(run, ciclo))
        entradas = {"mode": "correct", **comunes, "previous_version": run.leer(actual["ruta"]),
                    "findings_with_dispositions": hallazgos, "length_limits": ficha.get("limites", {}),
                    "forbidden_content": ficha.get("prohibiciones"),
                    "source_register": _registro_fuentes_verificadas(run)}
        manual.preparar_ficha(run, np, "constructor", "builder", entradas, f"{carpeta}/cambios_{nombre}.json",
                              asignado=rot["constructor"], destino_texto=f"{carpeta}/version_{nombre}.md")

    elif paso == "veredicto":
        cambios = run.leer(actual["cambios"])
        entradas = {"version": run.leer(actual["ruta"]), "change_register": cambios, **comunes,
                    "findings_with_dispositions": _hallazgos_con_disposiciones(run, ciclo),
                    "verifier_notes": _notas_verificador(run, ciclo, actual["nombre"]),
                    "open_items": cambios.get("open_questions_for_owner", [])}
        for i, letra in enumerate(rot["evaluadores"], 1):
            manual.preparar_ficha(run, np, f"V{i}", "cross-verdict", entradas, f"{carpeta}/veredicto_V{i}.json",
                                  asignado=letra)


def _condiciones_del_veredicto(run: Ejecucion, ciclo: int) -> list[dict]:
    salida = []
    for i in (1, 2):
        r = f"{_carpeta(ciclo)}/veredicto_V{i}.json"
        if not run.existe(r):
            continue
        v = run.leer(r)
        salida += [{"id": f"V{i}-{p['id']}", "severity": p.get("severity"), "problem": p["problem"], "fix": p["fix"],
                    "owner_disposition": "apply (last pass)"} for p in v.get("new_problems", [])]
        salida += [{"id": f"V{i}-{f['id']}", "problem": f"Finding {f['id']} {f['status']}: {f.get('why', '')}",
                    "owner_disposition": "apply (last pass)"} for f in v.get("finding_status", [])
                   if f["status"] != "resolved"]
    return salida


def _pendientes_del_ciclo_anterior(run: Ejecucion, ciclo: int) -> list[dict]:
    motivo = [d.get("motivo", "") for d in run.decisiones("fase_b") if d["tipo"] == "cierre_ciclo" and d.get("ciclo") == ciclo]
    return [{"id": "OWNER", "problem": m, "owner_disposition": "apply"} for m in motivo if m] + \
        _condiciones_del_veredicto(run, ciclo)


# --- pasos deterministas ----------------------------------------------------------------------
def texto_completo(run: Ejecucion, version: dict) -> str:
    """Entregable más su registro de cambios: las fuentes de los respaldos viven en el
    registro, y perderlas entre versiones es justo lo que hay que detectar (lección 19)."""
    cambios = run.leer(version["cambios"]) if run.existe(version["cambios"]) else {}
    return run.leer(version["ruta"]) + "\n\nChange register\n" + json.dumps(cambios, ensure_ascii=False, indent=1)


def _verificar_determinista(run: Ejecucion, ciclo: int) -> dict:
    ficha = run.leer("ficha.json")
    actual, anterior = version_actual(run), _anterior(run)
    partes = {k: tuple(v) for k, v in (ficha.get("partes") or {}).items()}
    if run.existe(actual["cambios"]):     # las fuentes con fragmento viven en el registro de cambios
        registrar_fuentes_de_salida(run, run.leer(actual["cambios"]), actual["nombre"], comprobar=False)
    return verificar_version(run, ciclo, actual["nombre"], texto_completo(run, actual),
                             anterior=texto_completo(run, anterior) if anterior else None,
                             partes=partes or None, limites=ficha.get("limites") or None,
                             comprobar_fuentes=comprobacion_activa(run))


def _al_completar(run: Ejecucion, paso: str) -> None:
    """Lo que se hace al recibir todas las respuestas de un paso con modelo."""
    b = estado_b(run)
    ciclo, carpeta = b["ciclo"], _carpeta(b["ciclo"])
    if paso in ("constructor", "correccion", "ultima_pasada"):
        pend = run.estado["pendientes"][nombre_paso(ciclo, paso)]["constructor"]
        nombre = pend["destino_texto"].rsplit("version_", 1)[1].removesuffix(".md")
        _registrar_version(run, nombre, pend["destino_texto"], pend["destino"], paso)
        _verificar_determinista(run, ciclo)
    elif paso == "ataque":
        registrar_fuentes_de_salida(run, run.leer(f"{carpeta}/ataque.json"), f"ataque_ciclo_{ciclo}")
    elif paso == "verificacion":
        nombre = version_actual(run)["nombre"]
        r = f"{carpeta}/verificador_claims_{nombre}.json"
        if run.existe(r):   # fuentes que el verificador encontró en el texto, con su fragmento
            registrar_fuentes_de_salida(run, run.leer(r), f"afirmaciones:{nombre}")
            aplicar_comprobacion_a_afirmaciones(run, r)


SIGUIENTE = {
    "constructor": "verificacion", "verificacion": "ataque", "ataque": "verificacion_ataque",
    "verificacion_ataque": "arbitraje", "arbitraje": "disposiciones", "disposiciones": "correccion",
    "correccion": "verificacion_correccion", "verificacion_correccion": "veredicto", "veredicto": "adopcion",
    "ultima_pasada": "adopcion",
}


@dataclass
class EstadoB:
    ciclo: int
    paso: str
    espera: str | None           # "respuestas" | "dueno" | None (fase B terminada)
    detalle: str = ""


def avanzar_fase_b(run: Ejecucion, recursos=None) -> EstadoB:
    """Avanza todo lo posible. Se detiene cuando faltan respuestas (modo manual o
    modelos caídos) o cuando hace falta una decisión del dueño."""
    from tresia.motor.llamadas import ejecutar_paso
    while True:
        b = estado_b(run)
        ciclo, paso = b["ciclo"], b["paso"]
        if paso == "adoptada":
            return EstadoB(ciclo, paso, None, "Versión adoptada por el dueño.")
        if paso in PASOS_CON_MODELO:
            np = nombre_paso(ciclo, paso)
            if not manual.paso_preparado(run, np):
                _preparar(run, paso)
            if recursos is not None and not manual.paso_completo(run, np):
                ejecutar_paso(run, np, recursos)
            if not manual.paso_completo(run, np):
                faltan = manual.ranuras_sin_respuesta(run, np)
                return EstadoB(ciclo, paso, "respuestas", f"Faltan respuestas: {', '.join(faltan)}.")
            _al_completar(run, paso)
            _ir_a(run, SIGUIENTE[paso])
        elif paso == "verificacion_ataque":
            _ir_a(run, SIGUIENTE[paso])     # las fuentes del ataque ya se registraron al recibirlo
        elif paso == "verificacion_correccion":
            _ir_a(run, SIGUIENTE[paso])     # la verificación determinista se hizo al recibir la corrección
        elif paso == "disposiciones":
            tarjetas = run.leer(f"{_carpeta(ciclo)}/tarjetas.json")["cards"]
            disp = run.leer(f"{_carpeta(ciclo)}/disposiciones.json") if run.existe(f"{_carpeta(ciclo)}/disposiciones.json") else {}
            faltan = [t["finding"] for t in tarjetas if t["finding"] not in disp]
            if faltan:
                run.pedir_aprobacion()
                return EstadoB(ciclo, paso, "dueno", f"Decide las tarjetas: {', '.join(faltan)}.")
            _ir_a(run, SIGUIENTE[paso])
        elif paso == "adopcion":
            run.pedir_aprobacion()
            return EstadoB(ciclo, paso, "dueno", "Adoptar la versión, pedir una última pasada u otro ciclo.")
        else:
            raise RuntimeError(f"Paso desconocido de la fase B: {paso}")


# --- decisiones del dueño ⛔ ----------------------------------------------------------------------
def decidir_tarjetas(run: Ejecucion, decisiones: dict[str, dict] | None = None, usar_por_defecto: bool = False) -> dict:
    """``decisiones``: hallazgo -> {"opcion": etiqueta, "nota": ""}. Con ``usar_por_defecto``,
    las tarjetas sin respuesta toman su valor por defecto y quedan marcadas como tales."""
    ciclo = estado_b(run)["ciclo"]
    ruta = f"{_carpeta(ciclo)}/disposiciones.json"
    disp = run.leer(ruta) if run.existe(ruta) else {}
    for hallazgo, d in (decisiones or {}).items():
        disp[hallazgo] = {"opcion": d["opcion"], "nota": d.get("nota", ""), "origen": "dueno"}
        run.registrar_decision("fase_b", "disposicion", {"ciclo": ciclo, "hallazgo": hallazgo, **d})
    if usar_por_defecto:
        for t in run.leer(f"{_carpeta(ciclo)}/tarjetas.json")["cards"]:
            if t["finding"] not in disp:
                disp[t["finding"]] = {"opcion": t["default"], "nota": "", "origen": "por_defecto"}
                run.registrar_decision("fase_b", "disposicion", {"ciclo": ciclo, "hallazgo": t["finding"],
                                                                 "opcion": t["default"], "por_defecto": True})
    run.escribir(ruta, disp)
    return disp


def decidir_cierre_ciclo(run: Ejecucion, accion: str, motivo: str = "") -> EstadoB:
    """⛔ Al final del ciclo: «adoptar», «ultima_pasada» u «otro_ciclo»."""
    if accion not in ACCIONES_CIERRE:
        raise ValueError(f"Acción no válida: {accion}. Usa {', '.join(ACCIONES_CIERRE)}.")
    b = estado_b(run)
    if b["paso"] != "adopcion":
        raise RuntimeError("El ciclo todavía no ha llegado a la adopción.")
    ciclo = b["ciclo"]
    run.registrar_decision("fase_b", "cierre_ciclo", {"ciclo": ciclo, "accion": accion, "motivo": motivo})
    with run.cerrojo:
        if accion == "adoptar":
            b["paso"] = "adoptada"
            b["version_adoptada"] = version_actual(run)["nombre"]
        elif accion == "ultima_pasada":
            b["paso"] = "ultima_pasada"
            run.estado["pendientes"].pop(nombre_paso(ciclo, "ultima_pasada"), None)
        else:
            b["ciclo"] = ciclo + 1
            b["paso"] = "constructor"
        run.estado["fases"][run.fase_actual] = "en_curso"
        run.guardar()
    if accion == "adoptar":
        run.aprobar(f"Versión {b['version_adoptada']} adoptada. {motivo}".strip())
    return EstadoB(b["ciclo"], b["paso"], None if accion == "adoptar" else "respuestas")
