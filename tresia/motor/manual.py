"""Modo manual (SPEC §3): el motor genera la ficha, el dueño la copia en la web
del modelo y pega la respuesta. Sirve igual para los adaptadores automáticos:
ellos solo sustituyen el «copiar y pegar» por una llamada.

Cada ficha enviada y cada respuesta bruta se guardan en ``prompts/`` y ``respuestas/``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tresia import papeles
from tresia.calculo import esquemas
from tresia.calculo.limpieza_json import INSTRUCCION_REINTENTO, JSONIrrecuperable, extraer_json
from tresia.motor.ejecucion import Ejecucion

MAX_REINTENTOS = 1


@dataclass
class ResultadoRespuesta:
    ok: bool
    datos: dict | None = None
    errores: list[str] = field(default_factory=list)
    ficha_reintento: str | None = None   # si no es válida y queda reintento
    agotado: bool = False                # sin reintentos: hace falta intervención


def preparar_ficha(run: Ejecucion, paso: str, ranura: str, papel: str, entradas: dict,
                   destino: str, tarea: str | None = None) -> str:
    """Compone la ficha, la guarda y deja la ranura pendiente de respuesta."""
    ficha = papeles.componer_ficha(papel, entradas, tarea)
    run.escribir(f"prompts/{paso}/{ranura}.md", ficha)
    run.estado["pendientes"].setdefault(paso, {})[ranura] = {
        "papel": papel, "tarea": tarea, "destino": destino,
        "esquema": papeles.esquema_de(papel, tarea), "intentos": 0, "estado": "esperando",
    }
    run.guardar()
    return ficha


def recibir_respuesta(run: Ejecucion, paso: str, ranura: str, texto: str) -> ResultadoRespuesta:
    """Limpia, valida y guarda la respuesta pegada. Si falla, prepara un reintento
    que pide solo el JSON (una vez); después marca la ranura como agotada."""
    pend = run.estado["pendientes"][paso][ranura]
    pend["intentos"] += 1
    run.escribir(f"respuestas/{paso}/{ranura}_intento{pend['intentos']}.txt", texto)

    try:
        datos = extraer_json(texto)
        errores = esquemas.errores(pend["esquema"], datos) if pend["esquema"] else []
    except JSONIrrecuperable as e:
        datos, errores = None, [str(e)]

    if not errores:
        run.escribir(pend["destino"], datos)
        pend["estado"] = "recibida"
        run.guardar()
        return ResultadoRespuesta(ok=True, datos=datos)

    if pend["intentos"] <= MAX_REINTENTOS:
        detalle = "\n".join(f"- {e}" for e in errores[:10])
        ficha = f"{INSTRUCCION_REINTENTO}\n\nProblems found:\n{detalle}\n"
        run.escribir(f"prompts/{paso}/{ranura}_reintento{pend['intentos']}.md", ficha)
        pend["estado"] = "reintento"
        run.guardar()
        return ResultadoRespuesta(ok=False, errores=errores, ficha_reintento=ficha)

    pend["estado"] = "agotado"
    run.guardar()
    return ResultadoRespuesta(ok=False, errores=errores, agotado=True)


def paso_completo(run: Ejecucion, paso: str) -> bool:
    ranuras = run.estado["pendientes"].get(paso, {})
    return bool(ranuras) and all(r["estado"] == "recibida" for r in ranuras.values())
