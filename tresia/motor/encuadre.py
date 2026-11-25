"""Ingesta, encuadre y línea base (SPEC §4.1–4.3 y §6).

- Cada material lleva una etiqueta: contexto, objeto, restricción o evidencia.
  El contexto nunca llega a los papeles (lección 1).
- El encuadre son las 11 preguntas universales con valores por defecto; producen
  ``ficha.json``, que el dueño confirma (⛔).
- La línea base (opciones obvias) se escribe antes de la fase A y no se entrega a
  los papeles: sirve para medir la novedad.
"""

from __future__ import annotations

import re
from pathlib import Path

from tresia.motor.ejecucion import Ejecucion

ETIQUETAS = ("contexto", "objeto", "restriccion", "evidencia")

ETAPAS_POR_DEFECTO = ["find", "create_or_rescue", "preserve", "describe", "access", "use", "transmit"]
CRITERIOS_POR_DEFECTO = {
    "impact": "effect on the objective",
    "feasibility": "doable now with the means described",
    "evidence": "strength of precedent or reasoning",
    "safety": "low risk to the people involved",
    "inclusion": "reaches the priority groups",
}

# (clave en la ficha, pregunta para el dueño, valor por defecto)
PREGUNTAS: list[tuple[str, str, object]] = [
    ("materiales", "¿Qué es cada material: contexto, objeto a validar, restricción o evidencia?", "Se toma de la ingesta."),
    ("decision", "¿Qué decisión tomarás con el resultado: abrir opciones, validar o ambas?", "ambas"),
    ("fijo_y_cuestionable", "¿Qué es fijo y qué se puede cuestionar, incluida la premisa?",
     "Fijo: el objetivo. Todo lo demás, incluida la premisa, se puede cuestionar."),
    ("prohibiciones", "¿Qué no se puede tocar, usar ni revelar?", "Datos personales y nombres de particulares."),
    ("destinatarios", "¿Para quién es, a quién afecta y quién podría quedar fuera?", ""),
    ("exposicion", "¿Qué relación tienes con el objeto y cuánto quieres exponerte?", "Uso interno; no se publica nada sin aprobación."),
    ("criterios_prueba", "¿Cómo sabremos que está bien y qué cuenta como prueba?",
     "Fuentes con fragmento verificado, razonamientos con premisas explícitas y conocimiento del dueño marcado como tal."),
    ("criticos", "¿Qué es crítico y detiene el proceso, y cuánto inviertes?", ""),
    ("cobertura_obligatoria", "¿Qué tiene que cubrir sí o sí?", "Toda la cadena, hasta el uso real."),
    ("caras", "¿Qué caras tiene el problema, qué manda en cada una y cuál obliga?",
     ["La práctica real del mercado (qué hacen hoy los actores grandes)."]),
    ("sin_intervencion", "¿Cómo evoluciona el problema si no hacemos nada y qué valor queda entonces?",
     "Lo explora la fase A con la técnica T7."),
]

# Campos de configuración de la ficha que no son preguntas (SPEC §6), con sus valores por defecto.
CONFIGURACION_POR_DEFECTO = {
    "objetivo": "",
    "fuentes_aceptadas": ["source", "reasoning", "owner", "position"],
    "principios": ["Proportionality: protect what can really be protected; give an honest warning about the rest."],
    "criterios_criba": CRITERIOS_POR_DEFECTO,
    "criterios_prioritarios": ["impact", "inclusion"],
    "etapas": ETAPAS_POR_DEFECTO,
    "cuotas_fase_a": {"opciones_min": 15, "opciones_max": 25, "min_sin_ia": 1 / 3, "una_por_etapa": True},
    "limites": {},       # p. ej. {"cuerpo": 1600, "anexo": 800}
    "partes": {},        # p. ej. {"cuerpo": [null, "# Annex"], "anexo": ["# Annex", null]}
    "cartera_n": 10,
    "foco_ataque": [],
    "ciclos_max": 3,
}


# --- ingesta -----------------------------------------------------------------------------
def _nombre_archivo(nombre: str) -> str:
    base = re.sub(r"[^\w.-]+", "_", nombre, flags=re.UNICODE).strip("_") or "material"
    return base if "." in base else base + ".md"


def ingestar(run: Ejecucion, nombre: str, etiqueta: str, texto: str | None = None,
             ruta: str | Path | None = None, descripcion: str = "") -> dict:
    """Guarda un material en ``materiales/`` con su etiqueta."""
    if etiqueta not in ETIQUETAS:
        raise ValueError(f"Etiqueta no válida: {etiqueta!r}. Usa una de {', '.join(ETIQUETAS)}.")
    if texto is None:
        if ruta is None:
            raise ValueError("Hace falta el texto o la ruta del material.")
        texto = Path(ruta).read_text(encoding="utf-8")
    with run.cerrojo:
        indice = run.leer("materiales/indice.json") if run.existe("materiales/indice.json") else []
        archivo = _nombre_archivo(nombre)
        if any(m["archivo"] == archivo for m in indice):
            archivo = f"{len(indice) + 1:02d}_{archivo}"
        run.escribir(f"materiales/{archivo}", texto)
        entrada = {"nombre": nombre, "archivo": archivo, "etiqueta": etiqueta, "descripcion": descripcion,
                   "palabras": len(texto.split())}
        indice.append(entrada)
        run.escribir("materiales/indice.json", indice)
    return entrada


def materiales(run: Ejecucion, incluir_contexto: bool = False) -> list[dict]:
    if not run.existe("materiales/indice.json"):
        return []
    return [m for m in run.leer("materiales/indice.json") if incluir_contexto or m["etiqueta"] != "contexto"]


def materiales_para_papeles(run: Ejecucion) -> list[dict]:
    """Lo que sí reciben los papeles: objeto, restricciones y evidencia. Nunca el contexto."""
    return [{"name": m["nombre"], "kind": {"objeto": "object to validate", "restriccion": "constraint",
                                            "evidencia": "evidence"}[m["etiqueta"]],
             "text": run.leer(f"materiales/{m['archivo']}")}
            for m in materiales(run)]


def cerrar_ingesta(run: Ejecucion) -> None:
    if not any(m["etiqueta"] == "objeto" for m in materiales(run)):
        raise ValueError("Falta al menos un material marcado como «objeto».")
    run.registrar_decision("ingesta", "ingesta_cerrada", {"materiales": len(materiales(run, True))})


# --- encuadre ----------------------------------------------------------------------------
def preguntas() -> list[dict]:
    return [{"clave": k, "pregunta": p, "por_defecto": d} for k, p, d in PREGUNTAS]


def responder_encuadre(run: Ejecucion, respuestas: dict, configuracion: dict | None = None) -> dict:
    """Construye ``ficha.json`` con las respuestas del dueño y los valores por defecto,
    marca qué campos usan el valor por defecto y deja la fase esperando su confirmación."""
    if not (respuestas.get("objetivo") or (configuracion or {}).get("objetivo")):
        raise ValueError("Falta el objetivo.")
    ficha: dict = {}
    por_defecto: list[str] = []
    for clave, _, defecto in PREGUNTAS:
        if respuestas.get(clave) not in (None, "", []):
            ficha[clave] = respuestas[clave]
        else:
            ficha[clave] = defecto
            por_defecto.append(clave)
    ficha["materiales"] = [{"nombre": m["nombre"], "etiqueta": m["etiqueta"]} for m in materiales(run, True)]
    config = {**CONFIGURACION_POR_DEFECTO, **(configuracion or {})}
    config["objetivo"] = respuestas.get("objetivo") or config["objetivo"]
    for clave, valor in CONFIGURACION_POR_DEFECTO.items():
        ficha[clave] = config[clave]
        if clave not in (configuracion or {}) and clave != "objetivo":
            por_defecto.append(clave)
    ficha["valores_por_defecto"] = por_defecto
    run.escribir("ficha.json", ficha)
    run.pedir_aprobacion()
    return ficha


# --- línea base ---------------------------------------------------------------------------
def registrar_linea_base(run: Ejecucion, opciones: list[str], origen: str = "dueno") -> list[dict]:
    """Opciones obvias escritas antes de la fase A (por el dueño o el verificador)."""
    lista = [{"id": f"L{i:02d}", "name": o.strip()} for i, o in enumerate(opciones, 1) if o.strip()]
    if not lista:
        raise ValueError("La línea base necesita al menos una opción.")
    run.escribir("linea_base.json", {"origen": origen, "opciones": lista})
    run.registrar_decision("linea_base", "linea_base", {"opciones": len(lista)}, origen=origen)
    return lista
