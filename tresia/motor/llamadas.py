"""Llamadas automáticas a los modelos sobre las mismas fichas del modo manual.

- Rotación en cuadrado latino para la fase B (SPEC §5).
- Ranuras en paralelo para la fase A y la criba, a ciegas.
- Un reintento pidiendo solo el JSON; si vuelve a fallar, la ranura queda
  pendiente para el modo manual (no se pierde nada).
- Verificador fijo con respaldo: si el servidor no responde se usa un modelo que
  no está en la rotación y queda un aviso visible en la ejecución.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from tresia import adaptadores, perfiles
from tresia.adaptadores import Adaptador, AdaptadorError
from tresia.motor import manual
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
                    etiqueta_modelo: str) -> ResultadoRanura:
    """Envía la ficha ya preparada y procesa la respuesta (con un reintento)."""
    with run.cerrojo:
        run.estado["identidades"][f"{paso}:{ranura}"] = etiqueta_modelo   # nunca se muestra al dueño
        run.guardar()
    prompt = ficha
    while True:
        try:
            r = adaptador.llamar(prompt)
        except AdaptadorError as e:
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


def tarea_verificador(run: Ejecucion, perfil: dict, tarea: str, entradas: dict, destino: str) -> ResultadoRanura:
    """Prepara la ficha de una tarea del verificador (merge, claims, timeline, arbitrate…)
    y la envía al verificador disponible. Sin verificador, la ficha queda para el modo manual."""
    paso = f"verificador_{tarea}"
    ficha = manual.preparar_ficha(run, paso, "V", "verifier", entradas, destino, tarea=tarea)
    adaptador, etiqueta = elegir_verificador(run, perfil)
    if adaptador is None:
        return ResultadoRanura("V", ok=False, errores=[etiqueta], pasa_a_manual=True)
    return ejecutar_ranura(run, paso, "V", adaptador, ficha, etiqueta)


# --- verificador fijo con respaldo ------------------------------------------------------
def elegir_verificador(run: Ejecucion | None, perfil: dict) -> tuple[Adaptador | None, str]:
    """Devuelve (adaptador, etiqueta). Si el verificador del servidor no está disponible,
    usa el respaldo, que no puede estar en la rotación, y deja un aviso visible.
    Si tampoco hay respaldo devuelve (None, motivo): el verificador pasa a modo manual."""
    principal = adaptadores.crear(perfil["verificador"])
    ok, motivo = principal.disponible()
    if ok:
        return principal, perfiles.identidad(perfil["verificador"])

    respaldo_def = perfil.get("verificador_respaldo")
    rotacion_ids = {perfiles.identidad(d) for d in perfil.get("modelos", {}).values()}
    if not respaldo_def:
        aviso = f"Verificador no disponible ({motivo}) y sin respaldo configurado: el verificador pasa a modo manual."
    elif perfiles.identidad(respaldo_def) in rotacion_ids:
        aviso = f"Verificador no disponible ({motivo}). El respaldo configurado está en la rotación y no se puede usar: modo manual."
    else:
        respaldo = adaptadores.crear(respaldo_def)
        ok_r, motivo_r = respaldo.disponible()
        if ok_r:
            if run:
                _anotar_aviso(run, f"Verificador del servidor no disponible ({motivo}). Se usa el modelo de respaldo, fuera de la rotación.")
            return respaldo, perfiles.identidad(respaldo_def)
        aviso = f"Verificador no disponible ({motivo}) ni respaldo ({motivo_r}): el verificador pasa a modo manual."
    if run:
        _anotar_aviso(run, aviso)
    return None, aviso
