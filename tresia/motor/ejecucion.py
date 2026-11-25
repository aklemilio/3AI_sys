"""Estado de una ejecución en disco (SPEC §4 y §10).

Una carpeta por ejecución con ``run.json`` (estado y configuración) y los
artefactos de cada fase en JSON o Markdown. Todo se reescribe en el momento,
así que la ejecución se puede cerrar y reanudar en cualquier punto.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

# (clave, nombre legible, necesita aprobación del dueño para cerrarse)
FASES: list[tuple[str, str, bool]] = [
    ("ingesta", "Ingesta de materiales", False),
    ("encuadre", "Encuadre y ficha del caso", True),
    ("linea_base", "Línea base", False),
    ("fase_a", "Fase A: abrir opciones", False),
    ("verificacion_a", "Verificación de la fase A", False),
    ("fusion", "Fusión de opciones", False),
    ("criba", "Criba ciega", False),
    ("agregacion", "Agregación", False),
    ("cartera", "Cartera por regla", True),
    ("fase_b", "Fase B: validar", True),
    ("informe", "Informe y entregable final", True),
]
_CLAVES = [f[0] for f in FASES]
_NECESITA_DUENO = {f[0] for f in FASES if f[2]}

PENDIENTE, EN_CURSO, ESPERA_DUENO, HECHA = "pendiente", "en_curso", "espera_dueno", "hecha"


class PuertaCerrada(RuntimeError):
    """Se intentó avanzar sin la aprobación del dueño."""


def _ahora() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _slug(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()[:50] or "ejecucion"


def _escribir_atomico(ruta: Path, contenido: str) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_name(ruta.name + ".tmp")
    tmp.write_text(contenido, encoding="utf-8", newline="\n")
    os.replace(tmp, ruta)


class Ejecucion:
    def __init__(self, carpeta: Path):
        self.carpeta = Path(carpeta)
        self.estado = json.loads((self.carpeta / "run.json").read_text(encoding="utf-8"))

    # --- creación y persistencia -------------------------------------------------
    @classmethod
    def crear(cls, base: Path, nombre: str, config: dict | None = None) -> "Ejecucion":
        base = Path(base)
        fecha = datetime.now().strftime("%Y%m%d-%H%M%S")
        carpeta = base / f"{fecha}_{_slug(nombre)}"
        carpeta.mkdir(parents=True, exist_ok=False)
        for sub in ("materiales", "faseA", "criba", "faseB", "prompts", "respuestas"):
            (carpeta / sub).mkdir()
        estado = {
            "nombre": nombre,
            "creada": _ahora(),
            "actualizada": _ahora(),
            "fase_actual": _CLAVES[0],
            "fases": {k: PENDIENTE for k in _CLAVES},
            "config": config or {},
            "identidades": {},   # ranura ("E1", "S2"...) -> modelo; la interfaz no lo muestra
            "pendientes": {},    # paso -> {ranura: estado} del modo manual
        }
        estado["fases"][_CLAVES[0]] = EN_CURSO
        _escribir_atomico(carpeta / "run.json", json.dumps(estado, ensure_ascii=False, indent=1))
        (carpeta / "decisiones.jsonl").touch()
        return cls(carpeta)

    @classmethod
    def abrir(cls, carpeta: Path) -> "Ejecucion":
        return cls(carpeta)

    def guardar(self) -> None:
        self.estado["actualizada"] = _ahora()
        _escribir_atomico(self.carpeta / "run.json", json.dumps(self.estado, ensure_ascii=False, indent=1))

    # --- artefactos -------------------------------------------------------------
    def escribir(self, relativa: str, datos) -> Path:
        ruta = self.carpeta / relativa
        if isinstance(datos, str):
            _escribir_atomico(ruta, datos)
        else:
            _escribir_atomico(ruta, json.dumps(datos, ensure_ascii=False, indent=1))
        return ruta

    def leer(self, relativa: str):
        ruta = self.carpeta / relativa
        texto = ruta.read_text(encoding="utf-8")
        return json.loads(texto) if ruta.suffix == ".json" else texto

    def existe(self, relativa: str) -> bool:
        return (self.carpeta / relativa).exists()

    def actualizar_metricas(self, fase: str, metricas: dict) -> None:
        todas = self.leer("metricas.json") if self.existe("metricas.json") else {}
        todas[fase] = metricas
        self.escribir("metricas.json", todas)

    # --- decisiones del dueño ---------------------------------------------------
    def registrar_decision(self, fase: str, tipo: str, contenido: dict, origen: str = "dueno") -> dict:
        entrada = {"fecha": _ahora(), "fase": fase, "tipo": tipo, "origen": origen, **contenido}
        with open(self.carpeta / "decisiones.jsonl", "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(entrada, ensure_ascii=False) + "\n")
        return entrada

    def decisiones(self, fase: str | None = None) -> list[dict]:
        lineas = (self.carpeta / "decisiones.jsonl").read_text(encoding="utf-8").splitlines()
        todas = [json.loads(l) for l in lineas if l.strip()]
        return [d for d in todas if fase is None or d["fase"] == fase]

    # --- fases ------------------------------------------------------------------
    @property
    def fase_actual(self) -> str:
        return self.estado["fase_actual"]

    def espera_dueno(self) -> bool:
        return self.estado["fases"][self.fase_actual] == ESPERA_DUENO

    def pedir_aprobacion(self) -> None:
        self.estado["fases"][self.fase_actual] = ESPERA_DUENO
        self.guardar()

    def aprobar(self, comentario: str = "") -> None:
        """El dueño aprueba la fase actual (⛔ en la SPEC)."""
        self.registrar_decision(self.fase_actual, "aprobacion", {"comentario": comentario})
        self.estado["fases"][self.fase_actual] = HECHA
        self.guardar()

    def avanzar(self) -> str:
        """Cierra la fase actual y pasa a la siguiente. Las fases con ⛔ no se
        cierran sin una aprobación registrada del dueño."""
        fase = self.fase_actual
        if fase in _NECESITA_DUENO and not any(d["tipo"] == "aprobacion" for d in self.decisiones(fase)):
            self.estado["fases"][fase] = ESPERA_DUENO
            self.guardar()
            raise PuertaCerrada(f"La fase «{dict((k, n) for k, n, _ in FASES)[fase]}» necesita la aprobación del dueño.")
        self.estado["fases"][fase] = HECHA
        i = _CLAVES.index(fase)
        if i + 1 < len(_CLAVES):
            self.estado["fase_actual"] = _CLAVES[i + 1]
            self.estado["fases"][_CLAVES[i + 1]] = EN_CURSO
        self.guardar()
        return self.fase_actual

    def ir_a(self, fase: str) -> None:
        """Salta a una fase (para reanudar o probar con datos ya existentes).
        Las fases saltadas quedan marcadas como hechas y se registra el salto."""
        if fase not in _CLAVES:
            raise ValueError(f"Fase desconocida: {fase}")
        destino = _CLAVES.index(fase)
        for k in _CLAVES[:destino]:
            if self.estado["fases"][k] != HECHA:
                self.estado["fases"][k] = HECHA
        self.estado["fase_actual"] = fase
        self.estado["fases"][fase] = EN_CURSO
        self.registrar_decision(fase, "salto_de_fase", {"destino": fase}, origen="motor")
        self.guardar()
