"""Perfiles de modelos: ``perfiles/<nombre>.toml`` más ``<nombre>.local.toml`` encima."""

from __future__ import annotations

import tomllib
from pathlib import Path

from tresia import RAIZ

CARPETA = RAIZ / "perfiles"


def _fusionar(base: dict, encima: dict) -> dict:
    salida = dict(base)
    for k, v in encima.items():
        salida[k] = _fusionar(salida[k], v) if isinstance(v, dict) and isinstance(salida.get(k), dict) else v
    return salida


def cargar(nombre: str = "pc", carpeta: Path = CARPETA) -> dict:
    with open(carpeta / f"{nombre}.toml", "rb") as f:
        perfil = tomllib.load(f)
    local = carpeta / f"{nombre}.local.toml"
    if local.exists():
        with open(local, "rb") as f:
            perfil = _fusionar(perfil, tomllib.load(f))
    perfil["nombre"] = nombre
    return perfil


def identidad(definicion: dict) -> str:
    """Identidad de un modelo para comprobar que el respaldo no está en la rotación."""
    return f"{definicion.get('proveedor', '')}:{definicion.get('modelo', '') or definicion.get('ejecutable', '')}"
