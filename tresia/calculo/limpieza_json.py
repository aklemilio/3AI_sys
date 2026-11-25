"""Extrae y limpia el bloque JSON de una respuesta de modelo (SPEC §3).

Las respuestas pegadas desde la web traen artefactos: entidades HTML (``&#x20;``),
escapes de Markdown (``\\_``, ``\\[``), comillas tipográficas, el JSON entero
escapado como cadena (``{\\"a\\": 1}``) o texto alrededor del bloque. Se prueba
primero lo menos invasivo y se va reparando paso a paso; si nada funciona se
lanza ``JSONIrrecuperable`` y el motor pide un reintento con solo el JSON.
"""

from __future__ import annotations

import html
import json
import re

INSTRUCCION_REINTENTO = (
    "Your previous answer could not be parsed as JSON. "
    "Reply again with ONLY the JSON object, inside one ```json code block, "
    "with no text before or after it and no Markdown escaping."
)


class JSONIrrecuperable(ValueError):
    """La respuesta no contiene un JSON que se pueda reparar."""


_BLOQUE = re.compile(r"```(?:json|JSON)?[ \t]*\r?\n(.*?)```", re.DOTALL)
# Escapes de Markdown que no son escapes JSON válidos: \_ \* \[ \] \# \- \. \( \) \! \> \< \` \~ \| \+ \=
_ESCAPE_MD = re.compile(r"\\([_*\[\]#\-.()!><`~|+=&{}])")
_COMILLAS = {"\u201c": '"', "\u201d": '"', "\u201e": '"', "\u00ab": '"', "\u00bb": '"'}
_ESPACIOS_RAROS = {"\u00a0": " ", "\u200b": "", "\ufeff": "", "\u2028": " ", "\u2029": " "}
_COMA_FINAL = re.compile(r",(\s*[}\]])")


def _candidatos(texto: str) -> list[str]:
    """Bloques de código y, si no hay, el primer objeto ``{...}`` equilibrado."""
    bloques = [b.strip() for b in _BLOQUE.findall(texto)]
    # Preferir el bloque más largo: suele ser el JSON y no un ejemplo corto.
    bloques.sort(key=len, reverse=True)
    objeto = _primer_objeto(texto)
    if objeto and objeto not in bloques:
        bloques.append(objeto)
    if not bloques:
        bloques.append(texto.strip())
    return bloques


def _primer_objeto(texto: str) -> str | None:
    inicio = texto.find("{")
    if inicio < 0:
        return None
    nivel, en_cadena, escape = 0, False, False
    for i in range(inicio, len(texto)):
        c = texto[i]
        if en_cadena:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                en_cadena = False
            continue
        if c == '"':
            en_cadena = True
        elif c == "{":
            nivel += 1
        elif c == "}":
            nivel -= 1
            if nivel == 0:
                return texto[inicio : i + 1]
    # Sin cierre: devolver desde la llave hasta la última llave de cierre.
    fin = texto.rfind("}")
    return texto[inicio : fin + 1] if fin > inicio else None


def _reparaciones(s: str):
    """Genera versiones cada vez más reparadas del texto."""
    yield s
    s = html.unescape(s)
    yield s
    for k, v in _ESPACIOS_RAROS.items():
        s = s.replace(k, v)
    yield s
    s = _ESCAPE_MD.sub(r"\1", s)
    yield s
    for k, v in _COMILLAS.items():
        s = s.replace(k, v)
    yield s
    s = _COMA_FINAL.sub(r"\1", s)
    yield s
    # JSON entero escapado: {\"a\": \"b\"}
    if '\\"' in s and not re.search(r'(?<!\\)"', s.replace('\\"', "")):
        yield s.replace('\\"', '"')
    # Escapes dobles residuales: \\n -> \n
    yield s.replace("\\\\", "\\")


def extraer_json(texto: str) -> dict | list:
    """Devuelve el objeto JSON de la respuesta o lanza ``JSONIrrecuperable``."""
    if not texto or not texto.strip():
        raise JSONIrrecuperable("Respuesta vacía.")
    texto = html.unescape(texto) if "&#" in texto and "```" not in texto else texto
    ultimo_error = None
    for candidato in _candidatos(texto):
        for version in _reparaciones(candidato):
            try:
                valor = json.loads(version)
            except json.JSONDecodeError as e:
                ultimo_error = e
                continue
            # Una cadena que contiene JSON (respuesta doblemente serializada).
            if isinstance(valor, str):
                try:
                    valor = json.loads(valor)
                except json.JSONDecodeError:
                    continue
            if isinstance(valor, (dict, list)):
                return valor
    raise JSONIrrecuperable(f"No se pudo extraer un JSON válido: {ultimo_error}")
