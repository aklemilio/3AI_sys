"""Interfaz común de los adaptadores de modelos."""

from __future__ import annotations

import time
from dataclasses import dataclass


class AdaptadorError(RuntimeError):
    """La llamada falló: no disponible, tiempo agotado o respuesta de error."""


@dataclass
class Respuesta:
    texto: str           # texto que se pasa a la limpieza de JSON
    bruto: str           # salida tal cual, para guardarla en respuestas/
    segundos: float


class Adaptador:
    """Un modelo concreto. ``llamar`` recibe el prompt completo y devuelve el texto."""

    def __init__(self, definicion: dict):
        self.definicion = definicion
        self.proveedor = definicion.get("proveedor", "")
        self.tiempo_maximo = float(definicion.get("tiempo_maximo", 600))

    def disponible(self) -> tuple[bool, str]:
        """Comprobación rápida sin coste (no llama al modelo)."""
        return True, ""

    def llamar(self, prompt: str) -> Respuesta:
        inicio = time.monotonic()
        texto, bruto = self._llamar(prompt)
        return Respuesta(texto=texto, bruto=bruto, segundos=round(time.monotonic() - inicio, 1))

    def _llamar(self, prompt: str) -> tuple[str, str]:  # pragma: no cover - lo implementa cada adaptador
        raise NotImplementedError
