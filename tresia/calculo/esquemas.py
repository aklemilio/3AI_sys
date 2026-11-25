"""Validación de salidas de los papeles contra ``schemas/*.schema.json``."""

from __future__ import annotations

import json
from functools import lru_cache

from jsonschema import Draft202012Validator

from tresia import SCHEMAS


@lru_cache(maxsize=None)
def _validador(nombre: str) -> Draft202012Validator:
    ruta = SCHEMAS / f"{nombre}.schema.json"
    with open(ruta, encoding="utf-8") as f:
        return Draft202012Validator(json.load(f))


def errores(nombre: str, datos) -> list[str]:
    """Lista de errores legibles (vacía si es válido)."""
    salida = []
    for e in sorted(_validador(nombre).iter_errors(datos), key=lambda e: list(e.absolute_path)):
        ruta = "/".join(str(p) for p in e.absolute_path) or "(raíz)"
        salida.append(f"{ruta}: {e.message}")
    return salida


def disponibles() -> list[str]:
    return sorted(p.name.removesuffix(".schema.json") for p in SCHEMAS.glob("*.schema.json"))
