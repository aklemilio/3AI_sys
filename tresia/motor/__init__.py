"""Motor determinista: estado en disco, fases, puertas del dueño y modo manual."""

from tresia.motor.ejecucion import Ejecucion, FASES, PuertaCerrada
from tresia.motor.manual import ResultadoRespuesta

__all__ = ["Ejecucion", "FASES", "PuertaCerrada", "ResultadoRespuesta"]
