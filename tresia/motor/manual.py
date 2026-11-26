"""Modo manual (SPEC §3): el motor genera la ficha, el dueño la copia en la web
del modelo y pega la respuesta. Sirve igual para los adaptadores automáticos:
ellos solo sustituyen el «copiar y pegar» por una llamada.

Cada ficha enviada y cada respuesta bruta se guardan en ``prompts/`` y ``respuestas/``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from tresia import papeles
from tresia.calculo import esquemas
from tresia.calculo.limpieza_json import INSTRUCCION_REINTENTO, JSONIrrecuperable, extraer_json
from tresia.calculo.versiones import separar_registro
from tresia.motor.ejecucion import Ejecucion

MAX_REINTENTOS = 1


@dataclass
class ResultadoRespuesta:
    ok: bool
    datos: dict | None = None
    errores: list[str] = field(default_factory=list)
    ficha_reintento: str | None = None   # si no es válida y queda reintento
    agotado: bool = False                # sin reintentos: hace falta intervención


_BLOQUE_JSON = re.compile(r"```(?:json|JSON)?[ \t]*\r?\n.*?```", re.DOTALL)
MIN_TEXTO_ENTREGABLE = 200


def separar_entregable(texto: str) -> str:
    """Parte en Markdown de una respuesta del constructor: todo lo anterior al
    registro de cambios o, si no lo hay, el texto sin el bloque JSON."""
    documento, registro = separar_registro(texto)
    if registro:
        return documento.strip()
    bloques = list(_BLOQUE_JSON.finditer(texto))
    if bloques:
        ultimo = bloques[-1]
        return (texto[: ultimo.start()] + texto[ultimo.end():]).strip()
    return texto.strip()


def preparar_ficha(run: Ejecucion, paso: str, ranura: str, papel: str, entradas: dict,
                   destino: str, tarea: str | None = None, asignado: str | None = None,
                   destino_texto: str | None = None) -> str:
    """Compone la ficha, la guarda y deja la ranura pendiente de respuesta.
    ``asignado``: letra del modelo de la rotación («A», «B», «C») o «verificador»;
    ``None`` = solo modo manual. ``destino_texto``: dónde guardar el entregable en
    Markdown que acompaña al JSON (papel constructor)."""
    ficha = papeles.componer_ficha(papel, entradas, tarea)
    with run.cerrojo:
        run.escribir(f"prompts/{paso}/{ranura}.md", ficha)
        run.estado["pendientes"].setdefault(paso, {})[ranura] = {
            "papel": papel, "tarea": tarea, "destino": destino, "destino_texto": destino_texto,
            "asignado": asignado, "esquema": papeles.esquema_de(papel, tarea),
            "intentos": 0, "estado": "esperando",
        }
        run.guardar()
    return ficha


def recibir_respuesta(run: Ejecucion, paso: str, ranura: str, texto: str) -> ResultadoRespuesta:
    """Limpia, valida y guarda la respuesta pegada. Si falla, prepara un reintento
    que pide solo el JSON (una vez); después marca la ranura como agotada."""
    with run.cerrojo:
        return _recibir(run, paso, ranura, texto)


def _recibir(run: Ejecucion, paso: str, ranura: str, texto: str) -> ResultadoRespuesta:
    pend = run.estado["pendientes"][paso][ranura]
    pend["intentos"] += 1
    run.escribir(f"respuestas/{paso}/{ranura}_intento{pend['intentos']}.txt", texto)

    # El entregable del constructor se conserva aunque el JSON falle: el reintento
    # pide solo el JSON y no debe perderse el texto ya escrito.
    if pend.get("destino_texto"):
        libre = separar_entregable(texto)
        if len(libre) >= MIN_TEXTO_ENTREGABLE:
            pend["texto_entregable"] = libre

    try:
        datos = extraer_json(texto)
        errores = esquemas.errores(pend["esquema"], datos) if pend["esquema"] else []
    except JSONIrrecuperable as e:
        datos, errores = None, [str(e)]
    if not errores and pend.get("destino_texto") and not pend.get("texto_entregable"):
        errores = ["The deliverable in Markdown is missing: answer with the full deliverable and then the JSON block."]

    if not errores:
        run.escribir(pend["destino"], datos)
        if pend.get("destino_texto"):
            run.escribir(pend["destino_texto"], pend.pop("texto_entregable") + "\n")
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


def paso_preparado(run: Ejecucion, paso: str) -> bool:
    return bool(run.estado["pendientes"].get(paso))


def ranuras_sin_respuesta(run: Ejecucion, paso: str) -> list[str]:
    return [r for r, p in run.estado["pendientes"].get(paso, {}).items() if p["estado"] != "recibida"]
