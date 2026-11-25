"""Adaptador para CLI de modelos (``claude -p``, ``codex exec``) como subproceso.

- El prompt va siempre por stdin, en UTF-8; nunca como argumento.
- Se ejecuta en una carpeta temporal vacía: el modelo no ve ni toca el proyecto.
- Si se agota el tiempo se termina el árbol de procesos (los .cmd de npm lanzan node).

Patrón inspirado en el manejo de subprocesos de ``the-llm-council`` (licencia MIT);
código escrito de nuevo para este proyecto.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from tresia.adaptadores.base import Adaptador, AdaptadorError

_ES_WINDOWS = sys.platform == "win32"


def _terminar_arbol(proceso: subprocess.Popen) -> None:
    if _ES_WINDOWS:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proceso.pid)], capture_output=True)
    else:
        proceso.kill()


class AdaptadorCLI(Adaptador):
    def __init__(self, definicion: dict):
        super().__init__(definicion)
        self.ejecutable = definicion["ejecutable"]
        self.argumentos = list(definicion.get("argumentos", []))
        self.salida = definicion.get("salida", "texto")   # texto | claude_json | archivo

    def _ruta(self) -> str | None:
        if Path(self.ejecutable).is_file():
            return str(self.ejecutable)
        return shutil.which(self.ejecutable)

    def disponible(self) -> tuple[bool, str]:
        if self._ruta():
            return True, ""
        return False, f"No se encuentra «{self.ejecutable}». Instálalo o indica la ruta en perfiles/pc.local.toml."

    def _llamar(self, prompt: str) -> tuple[str, str]:
        ruta = self._ruta()
        if not ruta:
            raise AdaptadorError(self.disponible()[1])
        with tempfile.TemporaryDirectory(prefix="tresia-") as carpeta:
            archivo_salida = os.path.join(carpeta, "respuesta.txt")
            args = [a.replace("{archivo_salida}", archivo_salida) for a in self.argumentos]
            entorno = dict(os.environ, NO_COLOR="1", PYTHONIOENCODING="utf-8")
            try:
                proceso = subprocess.Popen(
                    [ruta, *args], cwd=carpeta, env=entorno,
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                )
            except OSError as e:
                raise AdaptadorError(f"No se pudo lanzar «{self.ejecutable}»: {e}") from e
            try:
                out, err = proceso.communicate(prompt.encode("utf-8"), timeout=self.tiempo_maximo)
            except subprocess.TimeoutExpired:
                _terminar_arbol(proceso)
                proceso.communicate()
                raise AdaptadorError(f"«{self.ejecutable}» no respondió en {self.tiempo_maximo:.0f} s.")
            stdout = out.decode("utf-8", errors="replace")
            stderr = err.decode("utf-8", errors="replace")
            if proceso.returncode != 0:
                raise AdaptadorError(f"«{self.ejecutable}» terminó con código {proceso.returncode}: {stderr.strip()[-500:]}")

            if self.salida == "archivo":
                if os.path.exists(archivo_salida):
                    texto = Path(archivo_salida).read_text(encoding="utf-8", errors="replace")
                    return texto, texto
                return stdout, stdout
            if self.salida == "claude_json":
                try:
                    datos = json.loads(stdout)
                except json.JSONDecodeError as e:
                    raise AdaptadorError(f"La salida de «{self.ejecutable}» no es el JSON esperado: {e}") from e
                if datos.get("is_error"):
                    raise AdaptadorError(f"«{self.ejecutable}» devolvió un error: {str(datos.get('result', ''))[:500]}")
                return str(datos.get("result", "")), stdout
            return stdout, stdout
