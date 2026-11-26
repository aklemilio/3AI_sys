"""El motor avanza en segundo plano: las llamadas a los modelos pueden tardar minutos.
Una tarea por ejecución; mientras corre, la interfaz no acepta decisiones sobre ella."""

from __future__ import annotations

import threading
import traceback
from dataclasses import asdict
from pathlib import Path
from typing import Callable

from tresia.motor import Ejecucion
from tresia.motor.ejecucion import _ahora
from tresia.motor.flujo import avanzar

ARCHIVO = "interfaz.json"     # último estado devuelto por avanzar(), para mostrarlo sin volver a calcular


class Trabajos:
    def __init__(self, recursos_para: Callable[[Ejecucion], object]):
        self.recursos_para = recursos_para
        self._hilos: dict[str, threading.Thread] = {}
        self._cerrojo = threading.Lock()

    def trabajando(self, carpeta: Path) -> bool:
        with self._cerrojo:
            h = self._hilos.get(str(carpeta))
            return bool(h and h.is_alive())

    def lanzar(self, carpeta: Path) -> bool:
        """Avanza la ejecución hasta la próxima espera. False si ya estaba trabajando."""
        with self._cerrojo:
            h = self._hilos.get(str(carpeta))
            if h and h.is_alive():
                return False
            h = threading.Thread(target=self._correr, args=(Path(carpeta),), daemon=True, name=f"tresia:{carpeta.name}")
            self._hilos[str(carpeta)] = h
            h.start()
            return True

    def esperar(self, carpeta: Path, segundos: float = 60) -> None:
        with self._cerrojo:
            h = self._hilos.get(str(carpeta))
        if h:
            h.join(segundos)

    def _correr(self, carpeta: Path) -> None:
        run = Ejecucion.abrir(carpeta)
        try:
            estado = avanzar(run, self.recursos_para(run))
            datos = {"estado": asdict(estado), "error": None}
        except Exception as e:  # se muestra en pantalla; el detalle queda en disco
            run.escribir("interfaz_error.txt", traceback.format_exc())
            datos = {"estado": None, "error": f"{type(e).__name__}: {e}"}
        datos["fecha"] = _ahora()
        run.escribir(ARCHIVO, datos)


def ultimo_estado(run: Ejecucion) -> dict:
    return run.leer(ARCHIVO) if run.existe(ARCHIVO) else {"estado": None, "error": None, "fecha": None}
