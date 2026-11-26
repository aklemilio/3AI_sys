"""Lo que ve el dueño: nombres legibles, sin identidad de modelos y sin códigos sueltos.

Funciones puras sobre la carpeta de la ejecución; el servidor solo las pasa a las
plantillas. Nada de aquí escribe en disco.
"""

from __future__ import annotations

import html
import re
import unicodedata

from tresia.motor import Ejecucion
from tresia.motor.ejecucion import FASES

NOMBRE_FASE = {k: n for k, n, _ in FASES}
ESTADO_FASE = {"pendiente": "Pendiente", "en_curso": "En curso", "espera_dueno": "Espera tu decisión", "hecha": "Hecha"}
ESTADO_RANURA = {"esperando": "Esperando respuesta", "reintento": "Falta el JSON corregido",
                 "agotado": "Respuesta no válida", "recibida": "Recibida"}
TAREA = {"merge": "fusión de opciones", "claims": "afirmaciones", "timeline": "orden temporal",
         "compliance": "cumplimiento de tus decisiones", "arbitrate": "tarjetas del árbitro", "premises": "premisas"}
ETIQUETAS = {"objeto": "Objeto a validar", "contexto": "Contexto (nunca llega a los modelos)",
             "restriccion": "Restricción", "evidencia": "Evidencia"}
RESPALDO = {"source": ("🔗", "Fuente con fragmento"), "reasoning": ("🧠", "Razonamiento con premisas"),
            "owner": ("👤", "Conocimiento del dueño"), "position": ("⚖️", "Postura declarada")}
SOLIDEZ = {"strong": "sólida", "weak": "débil", "unsupported": "sin respaldo"}
ESTADO_FUENTE = {"verificada": "verificada", "no_coincide": "el fragmento no coincide", "inaccesible": "inaccesible",
                 "sin_fragmento": "sin fragmento", "sin_comprobar": "sin comprobar"}
CRITERIO = {"impact": "Impacto", "feasibility": "Viabilidad", "evidence": "Evidencia", "safety": "Seguridad",
            "inclusion": "Inclusión"}
ORIGEN_CARTERA = {"corte": "Por regla", "regla": "Por regla", "empate": "Empate en el corte", "etapa": "Cubre una etapa",
                  "combinacion": "Combinación", "dueno": "Decisión tuya"}


# --- nombres de las ranuras ------------------------------------------------------------------------
def nombre_ranura(paso: str, ranura: str) -> str:
    """«Explorador 2», «Verificador: afirmaciones (ciclo 1)»… Nunca el modelo."""
    n = ranura[1:] if ranura[1:].isdigit() else ""
    if paso == "fase_a":
        return f"Explorador {n}"
    if paso == "criba":
        return f"Cribador {n}"
    if paso == "fusion":
        return "Verificador: fusión de opciones"
    if paso.startswith("verificador_"):
        return "Verificador: " + TAREA.get(paso.removeprefix("verificador_"), "tarea")
    if m := re.fullmatch(r"b(\d+)_(\w+)", paso):
        ciclo, sub = m.groups()
        nombre = {
            "constructor": "Constructor", "correccion": "Constructor: corrección",
            "ultima_pasada": "Constructor: última pasada", "ataque": "Atacante", "arbitraje": "Árbitro",
            "veredicto": f"Evaluador {n}", "verificacion": "Verificador: " + TAREA.get(ranura, "tarea"),
        }.get(sub, "Paso de la fase B")
        return f"{nombre} (ciclo {ciclo})"
    return "Paso del motor"


def nombre_participante(clave: str) -> str:
    """Claves de métricas (E1, S2…) a nombre legible."""
    if m := re.fullmatch(r"E(\d)", clave):
        return f"Explorador {m[1]}"
    if m := re.fullmatch(r"S(\d)", clave):
        return f"Cribador {m[1]}"
    if m := re.fullmatch(r"E(\d)-E(\d)", clave):
        return f"Exploradores {m[1]} y {m[2]}"
    return clave


# --- identidad de los modelos -----------------------------------------------------------------------
GENERICOS = ["claude", "anthropic", "codex", "chatgpt", "openai", "gpt", "gemini", "google"]


class Ocultador:
    """Quita de los textos visibles los nombres de los modelos de la rotación
    (proveedor, ejecutable, modelo e identidades guardadas)."""

    def __init__(self, perfil: dict | None = None):
        palabras = set(GENERICOS)
        for d in (perfil or {}).get("modelos", {}).values():
            palabras |= {str(d.get(k, "")) for k in ("proveedor", "ejecutable", "modelo")}
        self.base = {p.lower() for p in palabras if len(p) >= 3}

    def __call__(self, texto: str, run: Ejecucion | None = None) -> str:
        palabras = set(self.base)
        if run is not None:
            palabras |= {str(v).lower() for v in run.estado.get("identidades", {}).values() if len(str(v)) >= 3}
        for p in sorted(palabras, key=len, reverse=True):
            texto = re.sub(rf"(?i)(?<![\w-]){re.escape(p)}(?![\w])[\w.:-]*", "[modelo]", texto)
        return texto


def aviso_legible(texto: str, run: Ejecucion, ocultar: Ocultador) -> str:
    """Los avisos del motor empiezan por «<paso> <ranura>:»; se traduce a nombre legible."""
    if m := re.match(r"(\S+) (\S+): ", texto):
        paso, ranura = m.groups()
        if ranura in run.estado.get("pendientes", {}).get(paso, {}):
            texto = nombre_ranura(paso, ranura) + ": " + texto[m.end():]
    return ocultar(texto, run)


# --- markdown mínimo --------------------------------------------------------------------------------
def _en_linea(s: str) -> str:
    s = html.escape(s, quote=True)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
               r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', s)
    s = re.sub(r'(?<![">])(https?://[^\s<)\]]+)', r'<a href="\1" target="_blank" rel="noopener noreferrer">\1</a>', s)
    return s


def _celdas(linea: str) -> list[str]:
    return [c.strip() for c in linea.strip().strip("|").split("|")]


def md_a_html(texto: str) -> str:
    """Encabezados, listas, tablas, negrita, código y enlaces. Todo lo demás, párrafos."""
    salida, parrafo, lista = [], [], None
    lineas = texto.splitlines()

    def cerrar():
        nonlocal lista
        if parrafo:
            salida.append("<p>" + "<br>".join(_en_linea(l) for l in parrafo) + "</p>")
            parrafo.clear()
        if lista:
            salida.append(f"</{lista}>")
            lista = None

    i = 0
    while i < len(lineas):
        linea = lineas[i].rstrip()
        if not linea.strip():
            cerrar()
        elif m := re.match(r"(#{1,6})\s+(.*)", linea):
            cerrar()
            nivel = min(len(m[1]) + 1, 6)
            salida.append(f"<h{nivel}>{_en_linea(m[2].strip('* '))}</h{nivel}>")
        elif re.fullmatch(r"\s*(-{3,}|\*{3,})\s*", linea):
            cerrar()
            salida.append("<hr>")
        elif linea.lstrip().startswith("|"):
            cerrar()
            filas = []
            while i < len(lineas) and lineas[i].lstrip().startswith("|"):
                filas.append(lineas[i])
                i += 1
            cuerpo = [f for f in filas if not re.fullmatch(r"\s*\|[\s:|-]+\|?\s*", f)]
            if cuerpo:
                salida.append("<table><thead><tr>" + "".join(f"<th>{_en_linea(c)}</th>" for c in _celdas(cuerpo[0]))
                              + "</tr></thead><tbody>"
                              + "".join("<tr>" + "".join(f"<td>{_en_linea(c)}</td>" for c in _celdas(f)) + "</tr>"
                                        for f in cuerpo[1:]) + "</tbody></table>")
            continue
        elif m := re.match(r"\s*(?:[-*+]|(\d+)[.)])\s+(.*)", linea):
            if parrafo:
                cerrar()
            tipo = "ol" if m[1] else "ul"
            if lista != tipo:
                if lista:
                    salida.append(f"</{lista}>")
                salida.append(f"<{tipo}>")
                lista = tipo
            salida.append(f"<li>{_en_linea(m[2])}</li>")
        else:
            if lista:
                cerrar()
            parrafo.append(linea)
        i += 1
    cerrar()
    return "\n".join(salida)


# --- métricas -----------------------------------------------------------------------------------------
METRICA = {
    "opciones": "Opciones", "sin_ia": "Sin IA", "fuentes_citadas": "Fuentes citadas", "avisos": "Avisos",
    "grupos": "Grupos", "nuevos": "Nuevos frente a la línea base", "novedad": "Novedad", "jaccard": "Solapamiento (Jaccard)",
    "aportes_unicos": "Aportes únicos", "en_los_tres": "En los tres exploradores", "grupos_con_ia": "Grupos que dependen de IA",
    "opciones_por_explorador": "Opciones por explorador", "opciones_evaluadas": "Opciones evaluadas",
    "eliminadas": "Eliminadas", "votos_fatales": "Votos fatales", "con_desacuerdo": "Con desacuerdo",
    "opciones_nuevas_propuestas": "Opciones nuevas propuestas", "evaluaciones_incompletas": "Evaluaciones incompletas",
    "seleccionadas": "Seleccionadas", "por_origen": "Por origen", "nuevas_frente_a_linea_base": "Nuevas frente a la línea base",
    "archivadas": "Archivadas (pueden volver)", "valido": "Agrupación válida",
}
OCULTAS = {"errores", "sin_asignar", "repetidas", "desconocidas", "sin_nombre", "nombres_largos", "por_explorador"}


def _valor(v) -> str:
    if isinstance(v, bool):
        return "sí" if v else "no"
    if isinstance(v, float):
        return f"{v:.0%}" if 0 <= v <= 1 else f"{v:.2f}"
    if isinstance(v, dict):
        return "; ".join(f"{nombre_participante(str(k))}: {_valor(x)}" for k, x in v.items())
    if isinstance(v, list):
        return ", ".join(_valor(x) for x in v) or "—"
    return str(v)


def metricas_legibles(run: Ejecucion) -> list[dict]:
    """[{fase, filas: [(nombre, valor)]}] en el orden de las fases."""
    todas = run.leer("metricas.json") if run.existe("metricas.json") else {}
    salida = []
    for clave, nombre, _ in FASES:
        if not (m := todas.get(clave)):
            continue
        filas = [(METRICA.get(k, k.replace("_", " ").capitalize()), _valor(v)) for k, v in m.items() if k not in OCULTAS]
        salida.append({"fase": nombre, "clave": clave, "filas": filas})
    return salida


# --- resultados ------------------------------------------------------------------------------------------
def _opciones_exploradores(run: Ejecucion) -> dict[str, dict]:
    salida = {}
    for e in ("E1", "E2", "E3"):
        if run.existe(f"faseA/{e}.json"):
            for o in run.leer(f"faseA/{e}.json").get("options", []):
                salida[f"{e}:{o.get('id')}"] = {**o, "explorador": nombre_participante(e)}
    return salida


def resultados(run: Ejecucion) -> dict:
    """Tabla de grupos por nombre con puntuaciones, novedad, desacuerdos y detalle."""
    grupos = run.leer("grupos.json") if run.existe("grupos.json") else {}
    ranking = run.leer("ranking.json") if run.existe("ranking.json") else []
    cartera = run.leer("cartera.json") if run.existe("cartera.json") else {"seleccion": [], "archivo": []}
    en_cartera = {s["id"]: ORIGEN_CARTERA.get(s["origen"], s["origen"]) for s in cartera["seleccion"]}
    opciones = _opciones_exploradores(run)
    notas: dict[str, list[str]] = {}
    for s in ("S1", "S2", "S3"):
        if run.existe(f"criba/{s}.json"):
            for a in run.leer(f"criba/{s}.json").get("assessments", []):
                partes = [x for x in (a.get("note"), f"Rescate: {a['rescue']}" if a.get("rescue") else "",
                                      f"Voto fatal: {a.get('fatal_reason') or a.get('fatal')}" if a.get("fatal") else "") if x]
                if partes:
                    notas.setdefault(a["id"], []).append(f"{nombre_participante(s)}: " + " · ".join(map(str, partes)))
    criterios = list(ranking[0]["med"]) if ranking else []
    filas = []
    vistos = set()
    for pos, f in enumerate(ranking, 1):
        g = grupos.get(f["id"], {})
        vistos.add(f["id"])
        filas.append({
            "pos": pos, "id": f["id"], "nombre": f["name"], "etapa": f.get("stage", ""), "total": f["tot"],
            "medianas": [f["med"].get(c) for c in criterios], "desacuerdo": [CRITERIO.get(c, c) for c in f.get("dis", [])],
            "nuevo": f.get("new", False), "ia": f.get("ai", False), "cartera": en_cartera.get(f["id"]),
            "miembros": [{"nombre": opciones.get(m, {}).get("name", "Opción sin nombre"),
                          "descripcion": opciones.get(m, {}).get("description", ""),
                          "explorador": opciones.get(m, {}).get("explorador", "")} for m in g.get("members", [])],
            "notas": notas.get(f["id"], []),
        })
    for gid, g in grupos.items():      # antes de la criba, o grupos eliminados
        if gid not in vistos:
            filas.append({"pos": None, "id": gid, "nombre": g["name"], "etapa": "", "total": None, "medianas": [],
                          "desacuerdo": [], "nuevo": not g.get("baseline", False), "ia": False, "cartera": None,
                          "miembros": [{"nombre": opciones.get(m, {}).get("name", "Opción sin nombre"),
                                        "descripcion": opciones.get(m, {}).get("description", ""),
                                        "explorador": opciones.get(m, {}).get("explorador", "")} for m in g.get("members", [])],
                          "notas": notas.get(gid, [])})
    eliminadas = run.leer("criba/eliminadas.json") if run.existe("criba/eliminadas.json") else []
    nuevas = run.leer("criba/opciones_nuevas.json") if run.existe("criba/opciones_nuevas.json") else []
    return {"criterios": [CRITERIO.get(c, c) for c in criterios], "filas": filas,
            "eliminadas": eliminadas, "nuevas": [{**o, "propuesta_por": nombre_participante(o.get("propuesta_por", ""))}
                                                 for o in nuevas],
            "archivo": cartera["archivo"], "sin_grupos": not grupos,
            "opciones_sueltas": [] if grupos else list(opciones.values())}


# --- propuesta final y su porqué --------------------------------------------------------------------
def _normal(t: str) -> str:
    t = unicodedata.normalize("NFKC", t).lower()
    t = re.sub(r"[*_`#>\[\]()|“”\"'’]", " ", t)
    return " ".join(t.split())


def propuesta(run: Ejecucion) -> dict | None:
    """El entregable (adoptado o el último) con sus afirmaciones, su respaldo, la
    fuente y la primera versión en la que aparece cada una."""
    b = run.estado.get("fase_b", {})
    versiones = b.get("versiones", [])
    if not versiones:
        return None
    nombre = b.get("version_adoptada") or versiones[-1]["nombre"]
    version = next(v for v in versiones if v["nombre"] == nombre)
    texto = run.leer(version["ruta"])
    indice = versiones.index(version)

    claims, de_version = [], None
    for v in reversed(versiones[: indice + 1]):
        ruta = f"faseB/ciclo_{v['ciclo']}/verificador_claims_{v['nombre']}.json"
        if run.existe(ruta):
            claims, de_version = run.leer(ruta).get("claims", []), v["nombre"]
            break

    fuentes = {e["url"]: e for e in (run.leer("fuentes.json").values() if run.existe("fuentes.json") else [])}
    textos = [(v["nombre"], v["ciclo"], v["paso"], _normal(run.leer(v["ruta"]))) for v in versiones[: indice + 1]
              if run.existe(v["ruta"])]
    cuerpo = md_a_html(texto)
    salida = []
    for i, c in enumerate(claims, 1):
        norm = _normal(c.get("text", ""))
        origen = next((f"{n} (ciclo {ci}, {'construcción' if p == 'constructor' else 'corrección'})"
                       for n, ci, p, t in textos if norm and norm in t), None)
        icono, tipo = RESPALDO.get(c.get("type"), ("•", c.get("type", "")))
        if not re.match(r"https?://", c.get("url") or ""):   # nada de javascript: ni rutas raras en los enlaces
            c = {**c, "url": ""}
        fuente = fuentes.get(c["url"]) if c["url"] else None
        marca = False
        literal = html.escape(c.get("text", ""), quote=True)
        if literal and literal in cuerpo:
            cuerpo = cuerpo.replace(literal, f'<mark id="af{i}" title="{tipo}">{icono} {literal}</mark>', 1)
            marca = True
        salida.append({"n": i, "texto": c.get("text", ""), "icono": icono, "tipo": tipo,
                       "solidez": SOLIDEZ.get(c.get("strength"), c.get("strength", "")), "url": c.get("url", ""),
                       "fragmento": c.get("fragment", ""), "premisas": c.get("premises", []), "nota": c.get("note", ""),
                       "estado_fuente": ESTADO_FUENTE.get(fuente["estado"], fuente["estado"]) if fuente else
                       ("no está en el registro de fuentes" if c.get("url") else ""),
                       "origen": origen or "no localizada literalmente en ninguna versión", "marcada": marca})
    return {"version": nombre, "adoptada": bool(b.get("version_adoptada")), "html": cuerpo, "afirmaciones": salida,
            "afirmaciones_de": de_version}
