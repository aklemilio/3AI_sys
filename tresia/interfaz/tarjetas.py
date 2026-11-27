"""Tarjetas de decisión (SPEC §9.3): una por cada puerta del dueño.

``tarjeta(run, estado)`` dice qué tarjeta toca y con qué datos; ``ACCIONES`` aplica
la respuesta del dueño con las funciones del motor (todas dejan registro con fecha
en ``decisiones.jsonl``). Cada tarjeta dice qué pasa si no respondes.
"""

from __future__ import annotations

import json

from tresia.interfaz.vistas import ETIQUETAS, ORIGEN_CARTERA, explicaciones, md_a_html
from tresia.motor import Ejecucion, encuadre, fase_b, pasos
from tresia.motor.flujo import corregir_fusion

MARCA_ANEXO = "# Annex"

ACCION_CIERRE = [
    ("adoptar", "Adoptar esta versión", "Se cierra la fase B y se genera el informe."),
    ("ultima_pasada", "Pedir una última pasada", "El constructor aplica las condiciones de los evaluadores y vuelves a decidir."),
    ("otro_ciclo", "Otro ciclo completo", "Empieza un ciclo nuevo con la rotación siguiente: otro constructor y otro atacante."),
]


def _lineas(texto: str) -> list[str]:
    return [l.strip() for l in (texto or "").splitlines() if l.strip()]


# --- qué tarjeta toca ---------------------------------------------------------------------------
def tarjeta(run: Ejecucion, estado: dict | None) -> dict | None:
    if not estado or estado.get("espera") != "dueno":
        return None
    fase = run.fase_actual
    if fase == "ingesta":
        return {"tipo": "ingesta", "materiales": encuadre.materiales(run, True), "etiquetas": ETIQUETAS}
    if fase == "encuadre":
        preguntas = [p for p in encuadre.preguntas() if p["clave"] != "materiales"]
        if not run.existe("ficha.json"):
            return {"tipo": "encuadre", "preguntas": preguntas, "valores": {}}
        ficha = run.leer("ficha.json")
        valores = {k: ficha.get(k) for k in [p["clave"] for p in preguntas] + ["objetivo"]
                   if k not in ficha.get("valores_por_defecto", [])}
        valores["caras"] = "\n".join(ficha.get("caras", [])) if "caras" in valores else ""
        return {"tipo": "ficha", "ficha": ficha, "preguntas": preguntas, "valores": valores,
                "por_defecto": set(ficha.get("valores_por_defecto", []))}
    if fase == "linea_base":
        return {"tipo": "linea_base"}
    if fase == "fusion":
        m = run.leer("metricas.json").get("fusion", {}) if run.existe("metricas.json") else {}
        return {"tipo": "fusion", "errores": m.get("errores", []), "detalle": estado.get("detalle", "")}
    if fase == "cartera":
        cartera = run.leer("cartera.json")
        return {"tipo": "cartera", "seleccion": cartera["seleccion"], "archivo": cartera["archivo"],
                "origen": ORIGEN_CARTERA, "explicaciones": explicaciones(run)}
    if fase == "fase_b":
        b = fase_b.estado_b(run)
        carpeta = f"faseB/ciclo_{b['ciclo']}"
        if b["paso"] == "disposiciones":
            ataque = run.leer(f"{carpeta}/ataque.json") if run.existe(f"{carpeta}/ataque.json") else {"findings": []}
            nombres = {h["id"]: h for h in ataque.get("findings", [])}
            disp = run.leer(f"{carpeta}/disposiciones.json") if run.existe(f"{carpeta}/disposiciones.json") else {}
            tarjetas = [{**t, "hallazgo": nombres.get(t["finding"], {})} for t in run.leer(f"{carpeta}/tarjetas.json")["cards"]
                        if t["finding"] not in disp]
            return {"tipo": "disposiciones", "ciclo": b["ciclo"], "tarjetas": tarjetas}
        if b["paso"] == "adopcion":
            actual = fase_b.version_actual(run)
            notas_ruta = f"{carpeta}/notas_verificador_{actual['nombre']}.json"
            veredictos = []
            for i in (1, 2):
                r = f"{carpeta}/veredicto_V{i}.json"
                if run.existe(r):
                    v = run.leer(r)
                    veredictos.append({"nombre": f"Evaluador {i}", "veredicto": v.get("verdict", ""),
                                       "motivo": v.get("verdict_reason", ""), "problemas": v.get("new_problems", []),
                                       "pendientes": [f for f in v.get("finding_status", []) if f.get("status") != "resolved"]})
            return {"tipo": "adopcion", "ciclo": b["ciclo"], "version": actual["nombre"],
                    "alertas": run.leer(notas_ruta).get("alertas", []) if run.existe(notas_ruta) else [],
                    "veredictos": veredictos, "acciones": ACCION_CIERRE}
    if fase == "informe":
        return {"tipo": "informe", "html": md_a_html(run.leer("informe.md")) if run.existe("informe.md") else ""}
    return {"tipo": "otra", "detalle": estado.get("detalle", "")}


# --- acciones del dueño ---------------------------------------------------------------------------
def _material(run, f):
    nombre, texto = f.get("nombre", "").strip(), f.get("texto", "")
    if not nombre or not texto.strip():
        raise ValueError("Pon un nombre y el texto del material.")
    encuadre.ingestar(run, nombre, f.get("etiqueta", ""), texto=texto, descripcion=f.get("descripcion", ""),
                      solo_fase_b=f.get("solo_fase_b") == "si")
    return f"Material «{nombre}» añadido."


def _cerrar_ingesta(run, f):
    encuadre.cerrar_ingesta(run)
    return "Ingesta cerrada."


def _encuadre(run, f):
    respuestas = {p["clave"]: f.get(p["clave"], "").strip() for p in encuadre.preguntas() if p["clave"] != "materiales"}
    respuestas["caras"] = _lineas(f.get("caras", ""))
    respuestas["objetivo"] = f.get("objetivo", "").strip()
    config = {}
    if etapas := _lineas(f.get("etapas", "")):
        config["etapas"] = etapas
    limites = {k: int(f[k]) for k in ("limite_cuerpo", "limite_anexo") if f.get(k, "").strip().isdigit()}
    if limites:
        config["limites"] = {k.removeprefix("limite_"): v for k, v in limites.items()}
        # Sin marcas el verificador no sabe qué contar. El anexo empieza en el título «Annex».
        config["partes"] = ({"cuerpo": [None, MARCA_ANEXO], "anexo": [MARCA_ANEXO, None]}
                            if "limite_anexo" in limites else {"cuerpo": [None, None]})
    if f.get("cartera_n", "").strip().isdigit():
        config["cartera_n"] = int(f["cartera_n"])
    encuadre.responder_encuadre(run, respuestas, config)
    return "Ficha creada. Revísala y confírmala."


def _confirmar_ficha(run, f):
    if not run.existe("ficha.json"):
        raise ValueError("Todavía no hay ficha.")
    run.aprobar(f.get("comentario", "").strip() or "Ficha confirmada")
    return "Ficha confirmada."


def _linea_base(run, f):
    encuadre.registrar_linea_base(run, _lineas(f.get("opciones", "")))
    return "Línea base guardada."


def _corregir_fusion(run, f):
    try:
        grupos = json.loads(f.get("grupos", ""))
    except json.JSONDecodeError as e:
        raise ValueError(f"El JSON de los grupos no es válido: {e}") from e
    informe = corregir_fusion(run, grupos)
    if not informe["valido"]:
        raise ValueError("La agrupación sigue sin ser válida: " + " ".join(informe["errores"]))
    return "Agrupación corregida y comprobada."


def _repetir_fusion(run, f):
    with run.cerrojo:
        run.estado["pendientes"].pop("fusion", None)
        run.guardar()
    run.registrar_decision("fusion", "repetir_fusion", {})
    return "Se vuelve a pedir la fusión al verificador."


def _cartera_cambiar(run, f, listas):
    anadir, quitar = listas.get("anadir", []), listas.get("quitar", [])
    if not anadir and not quitar:
        raise ValueError("Marca alguna opción para añadir o quitar.")
    pasos.decidir_cartera(run, anadir=anadir, quitar=quitar, motivo=f.get("motivo", "").strip())
    return "Cartera actualizada con tu decisión."


def _cartera_aprobar(run, f):
    run.aprobar(f.get("comentario", "").strip() or "Cartera confirmada")
    return "Cartera aprobada."


def _disposiciones(run, f):
    elegidas = {k.removeprefix("d_"): v for k, v in f.items() if k.startswith("d_") and v}
    decisiones = {h: {"opcion": o, "nota": f.get(f"n_{h}", "").strip()} for h, o in elegidas.items()}
    fase_b.decidir_tarjetas(run, decisiones, usar_por_defecto=True)
    return f"Decididas {len(decisiones)} tarjetas; el resto toma su valor por defecto."


def _cierre(run, f):
    fase_b.decidir_cierre_ciclo(run, f.get("accion", ""), f.get("motivo", "").strip())
    return "Decisión del ciclo registrada."


def _aprobar_informe(run, f):
    run.aprobar(f.get("comentario", "").strip() or "Informe aprobado")
    return "Informe aprobado."


ACCIONES = {
    "material": _material, "cerrar_ingesta": _cerrar_ingesta, "encuadre": _encuadre,
    "confirmar_ficha": _confirmar_ficha, "linea_base": _linea_base, "corregir_fusion": _corregir_fusion,
    "repetir_fusion": _repetir_fusion, "cartera_cambiar": _cartera_cambiar, "cartera_aprobar": _cartera_aprobar,
    "disposiciones": _disposiciones, "cierre": _cierre, "aprobar_informe": _aprobar_informe,
}
CON_LISTAS = {"cartera_cambiar"}
# En qué fase vale cada acción: una pestaña vieja no puede decidir otra puerta.
FASE_DE_ACCION = {
    "material": "ingesta", "cerrar_ingesta": "ingesta", "encuadre": "encuadre", "confirmar_ficha": "encuadre",
    "linea_base": "linea_base", "corregir_fusion": "fusion", "repetir_fusion": "fusion",
    "cartera_cambiar": "cartera", "cartera_aprobar": "cartera", "disposiciones": "fase_b", "cierre": "fase_b",
    "aprobar_informe": "informe",
}
