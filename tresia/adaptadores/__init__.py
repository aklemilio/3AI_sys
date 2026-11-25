"""Adaptadores de modelos. El modo manual no es un adaptador: es la ficha de
``tresia.motor.manual`` que el dueño copia y pega."""

from tresia.adaptadores.base import Adaptador, AdaptadorError, Respuesta
from tresia.adaptadores.cli import AdaptadorCLI
from tresia.adaptadores.http import AdaptadorGemini, AdaptadorOllama

_TIPOS = {"cli": AdaptadorCLI, "gemini": AdaptadorGemini, "ollama": AdaptadorOllama}


def crear(definicion: dict) -> Adaptador:
    try:
        return _TIPOS[definicion["tipo"]](definicion)
    except KeyError as e:
        raise ValueError(f"Tipo de adaptador desconocido: {definicion.get('tipo')!r}") from e


__all__ = ["Adaptador", "AdaptadorError", "Respuesta", "AdaptadorCLI", "AdaptadorGemini", "AdaptadorOllama", "crear"]
