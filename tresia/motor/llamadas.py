"""Llamadas automáticas a los modelos sobre las mismas fichas del modo manual.

- Rotación en cuadrado latino para la fase B (SPEC §5).
- Ranuras en paralelo para la fase A y la criba, a ciegas.
- Un reintento pidiendo solo el JSON; si vuelve a fallar, la ranura queda
  pendiente para el modo manual (no se pierde nada).
- Verificador fijo con respaldo: si el servidor no responde se usa un modelo que
  no está en la rotación y queda un aviso visible en la ejecución.
"""

from __future__ import annotations

import random
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Callable

from tresia import adaptadores, perfiles
from tresia.adaptadores import Adaptador, AdaptadorError
from tresia.motor import consumo, manual, troceo
from tresia.motor.ejecucion import Ejecucion, _ahora

ROTACION = {  # ciclo -> (constructor, atacante, evaluadores del veredicto cruzado)
    1: ("A", "B", ("B", "C")),
    2: ("B", "C", ("C", "A")),
    3: ("C", "A", ("A", "B")),
}


def rotacion(ciclo: int) -> dict:
    """El constructor nunca evalúa su propia versión. Del ciclo 4 en adelante se repite."""
    constructor, atacante, evaluadores = ROTACION[(ciclo - 1) % 3 + 1]
    assert constructor not in evaluadores
    return {"constructor": constructor, "atacante": atacante, "evaluadores": list(evaluadores)}


def asignacion_ciega(run: Ejecucion, fase: str, ranuras: list[str]) -> dict[str, str]:
    """Reparte A, B y C entre las ranuras de una fase en paralelo (E1–E3, S1–S3) al
    azar y lo guarda aparte: ni la interfaz ni los otros papeles saben quién es quién."""
    with run.cerrojo:
        asignaciones = run.estado.setdefault("asignacion", {})
        if fase not in asignaciones:
            letras = ["A", "B", "C"]
            random.Random(f"{run.estado['creada']}:{fase}").shuffle(letras)
            asignaciones[fase] = dict(zip(ranuras, letras))
            run.guardar()
        return asignaciones[fase]


@dataclass
class ResultadoRanura:
    ranura: str
    ok: bool
    errores: list[str] = field(default_factory=list)
    pasa_a_manual: bool = False


def _anotar_aviso(run: Ejecucion, texto: str) -> None:
    with run.cerrojo:
        run.estado.setdefault("avisos", []).append({"fecha": _ahora(), "texto": texto})
        run.guardar()


def ejecutar_ranura(run: Ejecucion, paso: str, ranura: str, adaptador: Adaptador, ficha: str,
                    etiqueta_modelo: str, alternativas: list[tuple[Adaptador, str]] | None = None) -> ResultadoRanura:
    """Envía la ficha ya preparada y procesa la respuesta (con un reintento).
    ``alternativas``: modelos de respaldo si el principal falla (solo el verificador)."""
    alternativas = list(alternativas or [])

    def fijar_identidad(etiqueta):
        with run.cerrojo:
            run.estado["identidades"][f"{paso}:{ranura}"] = etiqueta   # nunca se muestra al dueño
            run.guardar()

    fijar_identidad(etiqueta_modelo)
    prompt = ficha
    while True:
        try:
            r = consumo.llamar(run, paso, ranura, adaptador, prompt, etiqueta_modelo)
        except AdaptadorError as e:
            if alternativas:
                adaptador, etiqueta_modelo = alternativas.pop(0)
                _anotar_aviso(run, f"{paso} {ranura}: el modelo falló ({e}). Se usa el modelo de respaldo, fuera de la rotación.")
                fijar_identidad(etiqueta_modelo)
                prompt = ficha
                continue
            _anotar_aviso(run, f"{paso} {ranura}: el modelo no respondió ({e}). La ficha queda para el modo manual.")
            return ResultadoRanura(ranura, ok=False, errores=[str(e)], pasa_a_manual=True)
        res = manual.recibir_respuesta(run, paso, ranura, r.texto)
        if res.ok:
            return ResultadoRanura(ranura, ok=True)
        if res.ficha_reintento:
            # Las CLI no recuerdan la conversación: se reenvía la ficha con su respuesta y la instrucción.
            prompt = f"{ficha}\n\n---\nYour previous answer:\n{r.texto[:20000]}\n\n---\n{res.ficha_reintento}"
            continue
        _anotar_aviso(run, f"{paso} {ranura}: la respuesta no es válida tras el reintento. Queda para el modo manual.")
        with run.cerrojo:
            run.estado["pendientes"][paso][ranura]["estado"] = "esperando"   # se puede pegar a mano
            run.estado["pendientes"][paso][ranura]["intentos"] = 0
            run.guardar()
        return ResultadoRanura(ranura, ok=False, errores=res.errores, pasa_a_manual=True)


def ejecutar_en_paralelo(run: Ejecucion, paso: str, asignacion: dict[str, tuple[Adaptador, str]],
                         fichas: dict[str, str]) -> list[ResultadoRanura]:
    """``asignacion``: ranura -> (adaptador, etiqueta del modelo). Fase A y criba."""
    with ThreadPoolExecutor(max_workers=len(asignacion)) as pool:
        futuros = {r: pool.submit(ejecutar_ranura, run, paso, r, a, fichas[r], etiqueta)
                   for r, (a, etiqueta) in asignacion.items()}
        return [futuros[r].result() for r in asignacion]


@dataclass
class Recursos:
    """Modelos disponibles para una ejecución. Sin recursos, todo va por modo manual."""
    modelos: dict[str, Adaptador]                                     # «A», «B», «C»
    verificadores: Callable[[Ejecucion, str], list[tuple[Adaptador, str]]]

    @classmethod
    def desde_perfil(cls, perfil: dict) -> "Recursos":
        return cls(modelos={k: adaptadores.crear(d) for k, d in perfil["modelos"].items()},
                   verificadores=lambda run, ficha: candidatos_verificador(run, perfil, ficha))


def ejecutar_paso(run: Ejecucion, paso: str, recursos: Recursos) -> list[ResultadoRanura]:
    """Envía todas las fichas pendientes de un paso a su modelo asignado: las de la
    rotación en paralelo y las del verificador de una en una (el servidor atiende de
    una en una). Las ranuras sin modelo asignado se quedan para el modo manual."""
    pend = run.estado["pendientes"].get(paso, {})
    esperando = [r for r, p in pend.items() if p["estado"] == "esperando" and p.get("asignado")]
    rotacion_ = {r: (recursos.modelos[pend[r]["asignado"]], pend[r]["asignado"])
                 for r in esperando if pend[r]["asignado"] in recursos.modelos}
    fichas = {r: run.leer(f"prompts/{paso}/{r}.md") for r in esperando}
    resultados = ejecutar_en_paralelo(run, paso, rotacion_, fichas) if rotacion_ else []
    for r in esperando:
        if pend[r]["asignado"] != "verificador":
            continue
        # Una tarea troceable no descarta al verificador del servidor por tamaño: se trocea.
        troceable = pend[r].get("tarea") in troceo.TAREAS
        candidatos = recursos.verificadores(run, None if troceable else fichas[r])
        resultados.append(ejecutar_verificador(run, paso, r, fichas[r], candidatos))
    return resultados


def ejecutar_verificador(run: Ejecucion, paso: str, ranura: str, ficha: str,
                         candidatos: list[tuple[Adaptador, str]]) -> ResultadoRanura:
    """Verificador del servidor (troceando si la ficha no cabe) y, si falla, el respaldo
    con la ficha completa. Sin candidatos, la ficha queda para el modo manual."""
    if not candidatos:
        return ResultadoRanura(ranura, ok=False, errores=["Sin verificador disponible."], pasa_a_manual=True)
    (adaptador, etiqueta), *resto = candidatos
    if troceo.hace_falta(run, paso, ranura, adaptador, ficha):
        ok, detalle = troceo.ejecutar(run, paso, ranura, adaptador, etiqueta)
        if ok:
            _anotar_aviso(run, f"{paso} {ranura}: la tarea no cabía en el verificador del servidor y se resolvió "
                               f"por partes ({detalle}).")
            return ResultadoRanura(ranura, ok=True)
        if not resto:
            _anotar_aviso(run, f"{paso} {ranura}: falló la tarea por partes ({detalle}) y no hay respaldo. "
                               "La ficha queda para el modo manual.")
            return ResultadoRanura(ranura, ok=False, errores=[detalle], pasa_a_manual=True)
        _anotar_aviso(run, f"{paso} {ranura}: falló la tarea por partes ({detalle}). "
                           "Se usa el modelo de respaldo, fuera de la rotación.")
        (adaptador, etiqueta), *resto = resto
    return ejecutar_ranura(run, paso, ranura, adaptador, ficha, etiqueta, alternativas=resto)


def tarea_verificador(run: Ejecucion, perfil: dict, tarea: str, entradas: dict, destino: str) -> ResultadoRanura:
    """Prepara la ficha de una tarea del verificador (merge, claims, timeline, arbitrate…)
    y la envía al verificador disponible. Sin verificador, la ficha queda para el modo manual."""
    paso = f"verificador_{tarea}"
    ficha = manual.preparar_ficha(run, paso, "V", "verifier", entradas, destino, tarea=tarea)
    candidatos = candidatos_verificador(run, perfil, None if tarea in troceo.TAREAS else ficha)
    return ejecutar_verificador(run, paso, "V", ficha, candidatos)


# --- verificador fijo con respaldo ------------------------------------------------------
def candidatos_verificador(run: Ejecucion | None, perfil: dict, prompt: str | None = None) -> list[tuple[Adaptador, str]]:
    """Verificadores utilizables, en orden: el del servidor (si está disponible y el
    prompt cabe en su contexto) y el respaldo (si no está en la rotación). Cada
    descarte deja un aviso visible. Lista vacía = el verificador pasa a modo manual."""
    candidatos, motivos = [], []
    principal = adaptadores.crear(perfil["verificador"])
    ok, motivo = principal.disponible()
    if ok and prompt is not None and hasattr(principal, "cabe"):
        ok, motivo = principal.cabe(prompt)
    if ok:
        candidatos.append((principal, perfiles.identidad(perfil["verificador"])))
    else:
        motivos.append(f"verificador del servidor: {motivo}")

    respaldo_def = perfil.get("verificador_respaldo")
    rotacion_ids = {perfiles.identidad(d) for d in perfil.get("modelos", {}).values()}
    if not respaldo_def:
        motivos.append("no hay respaldo configurado")
    elif perfiles.identidad(respaldo_def) in rotacion_ids:
        motivos.append("el respaldo configurado está en la rotación y no se puede usar")
    else:
        respaldo = adaptadores.crear(respaldo_def)
        ok_r, motivo_r = respaldo.disponible()
        if ok_r:
            candidatos.append((respaldo, perfiles.identidad(respaldo_def)))
        else:
            motivos.append(f"respaldo: {motivo_r}")

    if run and motivos:
        if not candidatos:
            _anotar_aviso(run, "Sin verificador automático (" + "; ".join(motivos) + "). El verificador pasa a modo manual.")
        elif not ok:
            _anotar_aviso(run, "Se usa el modelo de respaldo, fuera de la rotación (" + "; ".join(motivos) + ").")
    return candidatos


def elegir_verificador(run: Ejecucion | None, perfil: dict, prompt: str | None = None) -> tuple[Adaptador | None, str]:
    """Primer verificador utilizable, o (None, motivo) si ninguno: modo manual."""
    candidatos = candidatos_verificador(run, perfil, prompt)
    if candidatos:
        return candidatos[0]
    return None, "Sin verificador disponible: el verificador pasa a modo manual (ver avisos; la rotación no puede hacer de verificador)."
