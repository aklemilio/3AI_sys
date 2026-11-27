"""Recuento propio de palabras y elementos (SPEC §7, lección 3).

Nunca se aceptan los recuentos que declaran los modelos.

Método de palabras (documentado también en el informe):
1. Se sustituyen por espacios los símbolos de Markdown ``|``, ``*``, ``#`` y la comilla invertida.
2. Se separa el texto por espacios en blanco.
3. Se descartan las piezas formadas solo por guiones ASCII (``-``): viñetas de lista
   y separadores de tabla (``---``). Las rayas tipográficas (``—``, ``–``) sí cuentan
   como palabra, porque en el texto hacen de signo con valor propio.
4. Lo que queda es el recuento.

Con este método, ``v42.md`` da 1590 palabras de cuerpo y 798 de anexo (A–F).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_SIMBOLOS = re.compile(r"[|*#`]")
_SOLO_GUIONES = re.compile(r"-+")
_ENCABEZADO_MD = re.compile(r"^\s{0,3}#{1,6}\s")
_VINETA = re.compile(r"^\s*(?:[-*+•]|\d+[.)])\s+\S")
_FILA_TABLA = re.compile(r"^\s*\|.*\|\s*$")
_SEPARADOR_TABLA = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)*\|?\s*$")
_URL = re.compile(r"https?://[^\s<>\"'`|\])]+[^\s<>\"'`|\]).,;:!?]")

METODO = (
    "Se sustituyen por espacios los símbolos | * # y la comilla invertida; se separa por espacios; "
    "se descartan las piezas formadas solo por guiones ASCII (viñetas y separadores de tabla). "
    "Las rayas tipográficas (—, –) cuentan como palabra."
)


def palabras(texto: str) -> int:
    return sum(1 for p in _SIMBOLOS.sub(" ", texto).split() if not _SOLO_GUIONES.fullmatch(p))


def urls(texto: str) -> list[str]:
    """URL en orden de aparición, sin repetir."""
    return list(dict.fromkeys(_URL.findall(texto)))


@dataclass
class Elementos:
    palabras: int
    encabezados: int
    vinetas: int
    filas_tabla: int
    urls: int


def elementos(texto: str) -> Elementos:
    lineas = texto.splitlines()
    filas = [l for l in lineas if _FILA_TABLA.match(l) and not _SEPARADOR_TABLA.match(l)]
    return Elementos(
        palabras=palabras(texto),
        encabezados=sum(bool(_ENCABEZADO_MD.match(l)) for l in lineas),
        vinetas=sum(bool(_VINETA.match(l)) for l in lineas),
        filas_tabla=len(filas),
        urls=len(urls(texto)),
    )


def _buscar(texto: str, marcador: str, inicio: int = 0) -> int:
    """Posición del marcador. Un marcador que es un título Markdown se busca como
    título al principio de una línea, con cualquier nivel y en negrita o no («# Annex»
    encuentra «# **Annex**» y «## Annex A–F»). Los demás, literales.
    Si no aparece, ``ValueError``."""
    if not marcador.lstrip().startswith("#"):
        return texto.index(marcador, inicio)
    nucleo = marcador.strip().lstrip("#").strip().strip("*").strip()
    fin = r"\b" if nucleo[-1:].isalnum() else ""      # «Annex» no encuentra «Annexed»
    m = re.compile(rf"(?mi)^#+[ \t]*\**[ \t]*{re.escape(nucleo)}{fin}").search(texto, inicio)
    if not m:
        raise ValueError(f"No aparece el título «{marcador}».")
    return m.start()


def tramo(texto: str, desde: str | None = None, hasta: str | None = None) -> str:
    """Parte del texto desde el primer marcador ``desde`` (incluido) hasta antes de
    ``hasta``. Si un marcador no aparece se lanza ``ValueError``."""
    i = 0 if desde is None else _buscar(texto, desde)
    j = len(texto) if hasta is None else _buscar(texto, hasta, i)
    return texto[i:j]


def recuento_por_partes(texto: str, partes: dict[str, tuple[str | None, str | None]],
                        limites: dict[str, int] | None = None) -> dict:
    """``partes``: nombre -> (marcador inicial, marcador final). Devuelve palabras,
    límite y si se pasa, para cada parte."""
    limites = limites or {}
    salida = {}
    for nombre, (desde, hasta) in partes.items():
        n = palabras(tramo(texto, desde, hasta))
        lim = limites.get(nombre)
        salida[nombre] = {"palabras": n, "limite": lim, "excede": lim is not None and n > lim}
    salida["metodo"] = METODO
    return salida
