"""Pasos del flujo que ya están implementados (hito 1): fusión, criba,
agregación y cartera. Cada paso lee y escribe en la carpeta de la ejecución."""

from __future__ import annotations

from dataclasses import asdict

from tresia.calculo.agregacion import CRITERIOS_POR_DEFECTO, PRIORITARIOS_POR_DEFECTO, agregar
from tresia.calculo.cartera import cartera_por_regla
from tresia.calculo.fusion import comprobar_fusion, indexar_exploradores, normalizar_grupos
from tresia.motor import manual
from tresia.motor.ejecucion import Ejecucion

EXPLORADORES = ["E1", "E2", "E3"]
CRIBADORES = ["S1", "S2", "S3"]


def _ficha(run: Ejecucion) -> dict:
    return run.leer("ficha.json") if run.existe("ficha.json") else {}


def _exploradores(run: Ejecucion) -> dict[str, dict]:
    return {e: run.leer(f"faseA/{e}.json") for e in EXPLORADORES if run.existe(f"faseA/{e}.json")}


def _cribas(run: Ejecucion) -> dict[str, dict]:
    return {s: run.leer(f"criba/{s}.json") for s in CRIBADORES if run.existe(f"criba/{s}.json")}


# --- fusión --------------------------------------------------------------------
def registrar_fusion(run: Ejecucion, grupos) -> dict:
    """Guarda los grupos (del verificador o hechos a mano), los comprueba y
    escribe las métricas. Devuelve el informe; si no es válido, no se avanza."""
    G = normalizar_grupos(grupos)
    run.escribir("grupos.json", G)
    informe = comprobar_fusion(G, _exploradores(run))
    datos = asdict(informe) | {"valido": informe.valido, "errores": informe.errores(), "avisos": informe.avisos()}
    run.actualizar_metricas("fusion", datos)
    return datos


# --- criba ciega ---------------------------------------------------------------
def opciones_para_criba(grupos: dict, exploradores: dict[str, dict]) -> list[dict]:
    """Lista ciega para los cribadores: sin explorador ni ids de la fase A."""
    opciones = indexar_exploradores(exploradores)
    salida = []
    for gid, g in normalizar_grupos(grupos).items():
        miembros = [opciones[m] for m in g["members"] if m in opciones]
        if not miembros:
            continue
        principal = miembros[0]
        salida.append({
            "id": gid,
            "name": g["name"],
            "description": principal.get("description", ""),
            "variants": [m["name"] for m in miembros[1:]],
            "depends_on_ai": any(m.get("depends_on_ai") for m in miembros),
            "main_risk": principal.get("what_would_make_it_fail", ""),
        })
    return salida


def preparar_criba(run: Ejecucion) -> dict[str, str]:
    ficha = _ficha(run)
    criterios = ficha.get("criterios_criba") or {c: "" for c in CRITERIOS_POR_DEFECTO}
    entradas = {
        "objective": ficha.get("objetivo", ""),
        "priority_groups": ficha.get("destinatarios", ""),
        "criteria": criterios,
        "options": opciones_para_criba(run.leer("grupos.json"), _exploradores(run)),
    }
    return {s: manual.preparar_ficha(run, "criba", s, "screener", entradas, f"criba/{s}.json") for s in CRIBADORES}


# --- agregación ----------------------------------------------------------------
def agregar_criba(run: Ejecucion) -> dict:
    ficha = _ficha(run)
    criterios = list((ficha.get("criterios_criba") or {c: "" for c in CRITERIOS_POR_DEFECTO}).keys())
    prioritarios = ficha.get("criterios_prioritarios") or PRIORITARIOS_POR_DEFECTO
    r = agregar(run.leer("grupos.json"), _exploradores(run), _cribas(run), criterios, prioritarios)
    run.escribir("ranking.json", r.ranking)
    if r.eliminadas:
        run.escribir("criba/eliminadas.json", r.eliminadas)
    nuevas = [dict(o, propuesta_por=s) for s, c in _cribas(run).items() for o in c.get("new_options", [])]
    run.escribir("criba/opciones_nuevas.json", nuevas)
    metricas = {
        "opciones_evaluadas": len(r.ranking) + len(r.eliminadas),
        "eliminadas": len(r.eliminadas),
        "votos_fatales": r.votos_fatales,
        "con_desacuerdo": sum(bool(f["dis"]) for f in r.ranking),
        "opciones_nuevas_propuestas": len(nuevas),
        "evaluaciones_incompletas": r.incompletas,
    }
    run.actualizar_metricas("agregacion", metricas)
    return metricas


# --- cartera -------------------------------------------------------------------
def proponer_cartera(run: Ejecucion, n: int | None = None, combinaciones: list[dict] | None = None) -> dict:
    """Aplica la regla y deja la cartera esperando al dueño (⛔)."""
    ficha = _ficha(run)
    n = n or ficha.get("cartera_n", 10)
    etapas = ficha.get("etapas", [])
    prioritarios = ficha.get("criterios_prioritarios") or PRIORITARIOS_POR_DEFECTO
    decisiones = run.decisiones("cartera")
    anadir = [i for d in decisiones if d["tipo"] == "anadir" for i in d["ids"]]
    quitar = [i for d in decisiones if d["tipo"] == "quitar" for i in d["ids"]]
    cartera = cartera_por_regla(run.leer("ranking.json"), n, etapas, prioritarios, combinaciones, anadir, quitar)
    run.escribir("cartera.json", cartera)
    sel = cartera["seleccion"]
    ranking = {f["id"]: f for f in run.leer("ranking.json")}
    run.actualizar_metricas("cartera", {
        "seleccionadas": len(sel),
        "por_origen": {o: sum(s["origen"] == o for s in sel) for o in dict.fromkeys(s["origen"] for s in sel)},
        "nuevas_frente_a_linea_base": sum(ranking.get(s["id"], {}).get("new", False) for s in sel),
        "archivadas": len(cartera["archivo"]),
    })
    return cartera


def decidir_cartera(run: Ejecucion, anadir: list[str] = (), quitar: list[str] = (), motivo: str = "") -> dict:
    """Decisión del dueño sobre la cartera: prevalece y queda marcada."""
    if anadir:
        run.registrar_decision("cartera", "anadir", {"ids": list(anadir), "motivo": motivo})
    if quitar:
        run.registrar_decision("cartera", "quitar", {"ids": list(quitar), "motivo": motivo})
    return proponer_cartera(run)
