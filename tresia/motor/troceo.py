"""Troceo de las tareas largas del verificador del servidor (SSB-107).

El servidor fija el contexto en 8192 tokens. Cuando una ficha no cabe, el motor
parte la tarea en llamadas que sí caben y une los resultados de forma determinista:

- ``claims`` y ``compliance``: por secciones del texto (y por párrafos si una
  sección sola no cabe). ``claims`` se trocea además cuando el texto es largo,
  porque la respuesta no cabría en ``num_predict``.
- ``timeline``: primero una tabla compacta por parte (subtarea ``timeline-table``)
  y después la tarea ``timeline`` sobre la tabla unida, que ve puertas y
  actividades juntas.
- ``arbitrate``: por lotes de hallazgos.
- ``merge``: por etapas de la cadena y después una segunda fusión de los grupos
  de las distintas etapas, con la misma tarea ``merge``.

El modo manual y el respaldo siguen recibiendo la ficha completa. Si un trozo
falla, el troceo entero se descarta y se pasa al respaldo con un aviso.
"""

from __future__ import annotations

import json
import re
from typing import Callable

from tresia import papeles
from tresia.adaptadores import Adaptador, AdaptadorError
from tresia.adaptadores.http import estimar_tokens
from tresia.calculo import esquemas
from tresia.calculo.limpieza_json import INSTRUCCION_REINTENTO, JSONIrrecuperable, extraer_json
from tresia.motor import manual
from tresia.motor.ejecucion import Ejecucion

TAREAS = {"claims", "compliance", "timeline", "arbitrate", "merge"}
MAX_TEXTO_CLAIMS = 1500     # tokens estimados de texto por llamada: la respuesta debe caber en num_predict
MARGEN = 150                # tokens para la nota de la parte y redondeos


class ErrorTroceo(RuntimeError):
    """Un trozo no cabe, no respondió o no es válido: se descarta el troceo."""


Llamar = Callable[[str, dict], dict]          # (tarea, entradas) -> JSON validado
Cabe = Callable[[str, dict], bool]            # (tarea, entradas) -> ¿cabe la ficha?


# --- partición del texto -------------------------------------------------------------------------
_ENCABEZADO = re.compile(r"^#{1,6}\s", re.MULTILINE)
_PARRAFO = re.compile(r"\n\s*\n")
_FRASE = re.compile(r"(?<=[.!?。؟])\s+")


def _titulo(seccion: str) -> str:
    primera = seccion.strip().splitlines()[0] if seccion.strip() else ""
    if not _ENCABEZADO.match(primera):
        return "(start)"
    return re.sub(r"[#*_`]", "", primera).strip()[:80] or "(untitled)"


def secciones(texto: str) -> list[str]:
    cortes = [m.start() for m in _ENCABEZADO.finditer(texto)]
    if not cortes or cortes[0] != 0:
        cortes = [0] + cortes
    return [s for s in (texto[a:b] for a, b in zip(cortes, cortes[1:] + [len(texto)])) if s.strip()]


def _dividir(pieza: str, max_tokens: int) -> list[str]:
    """Divide una pieza demasiado grande por párrafos, luego por frases y, como
    último recurso, por caracteres."""
    if estimar_tokens(pieza) <= max_tokens:
        return [pieza]
    for separador in (_PARRAFO, _FRASE):
        partes = [p for p in separador.split(pieza) if p.strip()]
        if len(partes) > 1:
            unidas = "\n\n" if separador is _PARRAFO else " "
            return _empaquetar_textos([q for p in partes for q in _dividir(p, max_tokens)], max_tokens, unidas)
    paso = max_tokens * 3 - 3
    return [pieza[i:i + paso] for i in range(0, len(pieza), paso)]


def _empaquetar_textos(piezas: list[str], max_tokens: int, union: str) -> list[str]:
    salida, actual = [], ""
    for p in piezas:
        candidato = f"{actual}{union}{p}" if actual else p
        if actual and estimar_tokens(candidato) > max_tokens:
            salida.append(actual)
            actual = p
        else:
            actual = candidato
    if actual:
        salida.append(actual)
    return salida


def partir_texto(texto: str, max_tokens: int) -> list[tuple[str, str]]:
    """Trozos de como mucho ``max_tokens`` estimados, cortando por secciones
    siempre que se pueda. Devuelve (secciones que cubre, texto)."""
    if max_tokens < 50:
        raise ErrorTroceo("No queda sitio para el texto en el contexto del verificador.")
    piezas = []   # (título, texto) de tamaño válido
    for s in secciones(texto):
        titulo = _titulo(s)
        piezas += [(titulo, p) for p in _dividir(s, max_tokens)]
    trozos, titulos, actual = [], [], ""
    for titulo, p in piezas:
        candidato = f"{actual}\n\n{p}" if actual else p
        if actual and estimar_tokens(candidato) > max_tokens:
            trozos.append((titulos, actual))
            titulos, actual = [], p
        else:
            actual = candidato
        if titulo not in titulos:
            titulos.append(titulo)
    if actual:
        trozos.append((titulos, actual))
    return [("; ".join(t), x) for t, x in trozos]


def _presupuesto_texto(cabe_tokens: Callable[[str, dict], int], max_prompt: int, tarea: str, entradas: dict) -> int:
    base = cabe_tokens(tarea, {**entradas, "text": "", "part": "Part 10 of 10 of the text (sections: …)."})
    return max_prompt - base - MARGEN


def _nota_parte(i: int, n: int, titulos: str) -> str:
    return (f"Part {i} of {n} of the text (sections: {titulos}). Work only on this part; "
            "the engine joins the parts.")


# --- empaquetado de listas -----------------------------------------------------------------------
def empaquetar(elementos: list, cabe_lote: Callable[[list], bool]) -> list[list]:
    """Lotes consecutivos tan grandes como quepan. Un elemento que no cabe solo es un error."""
    lotes, actual = [], []
    for e in elementos:
        if cabe_lote(actual + [e]):
            actual.append(e)
            continue
        if not actual:
            raise ErrorTroceo("Un elemento no cabe solo en el contexto del verificador.")
        lotes.append(actual)
        actual = [e]
        if not cabe_lote(actual):
            raise ErrorTroceo("Un elemento no cabe solo en el contexto del verificador.")
    if actual:
        lotes.append(actual)
    return lotes


def _clave(d) -> str:
    return json.dumps(d, ensure_ascii=False, sort_keys=True)


def unir_generico(resultados: list[dict]) -> dict:
    """Listas concatenadas sin duplicados; otros valores, el primero."""
    salida: dict = {}
    for r in resultados:
        for k, v in r.items():
            if not isinstance(v, list):
                salida.setdefault(k, v)
                continue
            lista = salida.setdefault(k, [])
            vistos = {_clave(x) for x in lista}
            for x in v:
                if _clave(x) not in vistos:
                    vistos.add(_clave(x))
                    lista.append(x)
    return salida


# --- tareas ---------------------------------------------------------------------------------------
def _por_partes(tarea: str, entradas: dict, llamar: Llamar, max_texto: int) -> list[dict]:
    trozos = partir_texto(entradas["text"], max_texto)
    return [llamar(tarea, {**entradas, "text": x, "part": _nota_parte(i, len(trozos), t)})
            for i, (t, x) in enumerate(trozos, 1)]


def claims(entradas, llamar, presupuesto):
    max_texto = min(presupuesto("claims", entradas), MAX_TEXTO_CLAIMS)
    unidas = []
    vistos = set()
    for r in _por_partes("claims", entradas, llamar, max_texto):
        for c in r["claims"]:
            clave = (" ".join(c["text"].split()).lower(), c.get("url", ""))
            if clave not in vistos:
                vistos.add(clave)
                unidas.append(c)
    return {"claims": unidas}


def compliance(entradas, llamar, presupuesto):
    return unir_generico(_por_partes("compliance", entradas, llamar, presupuesto("compliance", entradas)))


def timeline(entradas, llamar, presupuesto):
    filas = unir_generico(_por_partes("timeline-table", entradas, llamar,
                                      presupuesto("timeline-table", entradas))).get("rows", [])
    resto = {k: v for k, v in entradas.items() if k != "text"}
    return llamar("timeline", {**resto, "timeline_table": filas,
                               "table_note": "The table was extracted from the full text, part by part, "
                                             "with dates as written. Check it as you would check the text."})


def arbitrate(entradas, llamar, cabe: Cabe):
    elementos = [("findings", h) for h in entradas.get("findings", [])] + \
                [("additions", a) for a in entradas.get("additions", [])]

    def entradas_de(lote):
        return {**entradas, "findings": [e for k, e in lote if k == "findings"],
                "additions": [e for k, e in lote if k == "additions"]}

    tarjetas, vistas = [], set()
    for lote in empaquetar(elementos, lambda l: cabe("arbitrate", entradas_de(l))):
        for t in llamar("arbitrate", entradas_de(lote))["cards"]:
            if t["finding"] not in vistas:
                vistas.add(t["finding"])
                tarjetas.append(t)
    return {"cards": tarjetas}


def _comprobar_cobertura(grupos: list[dict], refs: list[str], cuando: str) -> None:
    miembros = [m for g in grupos for m in g["members"]]
    if sorted(miembros) != sorted(refs):
        faltan = sorted(set(refs) - set(miembros))
        sobran = sorted({m for m in miembros if miembros.count(m) > 1 or m not in refs})
        raise ErrorTroceo(f"Fusión troceada ({cuando}): faltan {faltan[:5]} y sobran o se repiten {sobran[:5]}.")


def merge(entradas, llamar, cabe: Cabe):
    opciones = entradas["options"]
    etapas: dict[str, list[dict]] = {}
    for o in opciones:
        etapas.setdefault(o.get("chain_stage") or "", []).append(o)

    def entradas_de(lote, prefijo="Pxx"):
        return {**entradas, "options": lote, "group_ids": f"Use {prefijo}-01, {prefijo}-02, … in order."}

    # 1. Dentro de cada etapa (las etapas pequeñas comparten lote; una etapa grande se parte).
    lotes = empaquetar(list(etapas.values()), lambda l: cabe("merge", entradas_de([o for e in l for o in e])))
    lotes = [[o for e in l for o in e] for l in lotes]
    grupos = []
    for i, lote in enumerate(lotes, 1):
        r = llamar("merge", entradas_de(lote, f"P{i:02d}"))["groups"]
        _comprobar_cobertura(r, [o["ref"] for o in lote], f"lote {i}")
        grupos += r

    # 2. Fusión entre etapas: cada grupo es una opción de la segunda pasada.
    nombres = {o["ref"]: o["name"] for o in opciones}
    etapa = {o["ref"]: o.get("chain_stage", "") for o in opciones}
    seudo = {f"E0:O{k}": g for k, g in enumerate(grupos, 1)}
    segunda = [{"ref": ref, "name": g["name"],
                "description": "Group of: " + "; ".join(nombres[m] for m in g["members"])[:400],
                "chain_stage": ", ".join(dict.fromkeys(etapa[m] for m in g["members"]))}
               for ref, g in seudo.items()]
    entradas2 = {**entradas, "options": segunda, "group_ids": "Use C01, C02, … in order.",
                 "merge_note": "Each option here is already a group of options merged by mechanism within one "
                               "stage of the chain. Merge only groups that share the same mechanism."}
    if not cabe("merge", entradas2):
        raise ErrorTroceo("La segunda pasada de la fusión no cabe en el contexto del verificador.")
    r2 = llamar("merge", entradas2)["groups"]
    _comprobar_cobertura(r2, list(seudo), "entre etapas")

    finales = []
    for k, g in enumerate(r2, 1):
        originales = [seudo[m] for m in g["members"]]
        finales.append({"id": f"C{k:02d}", "name": g["name"],
                        "members": [m for o in originales for m in o["members"]],
                        "matches_baseline": bool(g["matches_baseline"] or any(o["matches_baseline"] for o in originales))})
    return {"groups": finales}


def conviene(tarea: str, entradas: dict) -> bool:
    """Trocear aunque la ficha quepa: la respuesta de «claims» a un texto largo no cabe en num_predict."""
    return tarea == "claims" and estimar_tokens(entradas.get("text", "")) > MAX_TEXTO_CLAIMS


def resolver(tarea: str, entradas: dict, llamar: Llamar, max_prompt: int) -> dict:
    """Ejecuta la tarea troceada con ``llamar`` y devuelve el resultado unido."""
    def tokens(t, e):
        return estimar_tokens(papeles.componer_ficha("verifier", e, t))

    def cabe(t, e):
        return tokens(t, e) <= max_prompt

    def presupuesto(t, e):
        return _presupuesto_texto(tokens, max_prompt, t, e)

    if tarea == "claims":
        return claims(entradas, llamar, presupuesto)
    if tarea == "compliance":
        return compliance(entradas, llamar, presupuesto)
    if tarea == "timeline":
        return timeline(entradas, llamar, presupuesto)
    if tarea == "arbitrate":
        return arbitrate(entradas, llamar, cabe)
    if tarea == "merge":
        return merge(entradas, llamar, cabe)
    raise ErrorTroceo(f"La tarea «{tarea}» no se puede trocear.")


# --- ejecución sobre una ranura del motor -------------------------------------------------------
def hace_falta(run: Ejecucion, paso: str, ranura: str, adaptador: Adaptador, ficha: str) -> bool:
    """Solo para el verificador con contexto fijo (tiene ``cabe``) y tareas troceables."""
    pend = run.estado["pendientes"][paso][ranura]
    if not hasattr(adaptador, "cabe") or pend.get("tarea") not in TAREAS:
        return False
    if not run.existe(f"prompts/{paso}/{ranura}.entradas.json"):
        return False
    return not adaptador.cabe(ficha)[0] or conviene(pend["tarea"], run.leer(f"prompts/{paso}/{ranura}.entradas.json"))


def ejecutar(run: Ejecucion, paso: str, ranura: str, adaptador: Adaptador, etiqueta: str) -> tuple[bool, str]:
    """Resuelve la ranura por trozos. Guarda cada ficha y respuesta parcial y, al
    final, entrega el resultado unido por el camino normal (limpieza y esquema)."""
    pend = run.estado["pendientes"][paso][ranura]
    tarea = pend["tarea"]
    entradas = run.leer(f"prompts/{paso}/{ranura}.entradas.json")
    contador = [0]

    def llamar(subtarea: str, sub: dict) -> dict:
        contador[0] += 1
        n = contador[0]
        ficha = papeles.componer_ficha("verifier", sub, subtarea)
        ok, motivo = adaptador.cabe(ficha)
        if not ok:
            raise ErrorTroceo(f"Trozo {n}: {motivo}")
        run.escribir(f"prompts/{paso}/{ranura}_trozo{n:02d}.md", ficha)
        esquema = papeles.esquema_de("verifier", subtarea)
        prompt = ficha
        for intento in (1, 2):
            try:
                r = adaptador.llamar(prompt)
            except AdaptadorError as e:
                raise ErrorTroceo(f"Trozo {n}: {e}") from e
            run.escribir(f"respuestas/{paso}/{ranura}_trozo{n:02d}_intento{intento}.txt", r.texto)
            try:
                datos = extraer_json(r.texto)
                errores = esquemas.errores(esquema, datos) if esquema else []
            except JSONIrrecuperable as e:
                datos, errores = None, [str(e)]
            if not errores and isinstance(datos, dict):
                return datos
            detalle = "\n".join(f"- {e}" for e in (errores or ["The answer is not a JSON object."])[:10])
            prompt = f"{ficha}\n\n---\nYour previous answer:\n{r.texto[:20000]}\n\n---\n{INSTRUCCION_REINTENTO}\n\nProblems found:\n{detalle}\n"
        raise ErrorTroceo(f"Trozo {n}: la respuesta no es válida tras el reintento.")

    try:
        datos = resolver(tarea, entradas, llamar, adaptador.max_prompt)
    except ErrorTroceo as e:
        return False, str(e)
    if pend.get("esquema") and (errores := esquemas.errores(pend["esquema"], datos)):
        return False, "El resultado unido no es válido: " + "; ".join(errores[:3])

    with run.cerrojo:
        run.estado["identidades"][f"{paso}:{ranura}"] = etiqueta   # nunca se muestra al dueño
        pend["troceo"] = {"llamadas": contador[0]}
        run.guardar()
    res = manual.recibir_respuesta(run, paso, ranura, "```json\n" + json.dumps(datos, ensure_ascii=False) + "\n```")
    if not res.ok:
        return False, "El resultado unido no se pudo registrar: " + "; ".join(res.errores[:3])
    return True, f"{contador[0]} llamadas"
