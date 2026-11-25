"""Avance de una ejecución completa (SPEC §4). Un solo punto de entrada:

    estado = avanzar(run, recursos)

Avanza todo lo que pueda sin el dueño y se detiene en tres casos:
- ``espera == "dueno"``: una puerta ⛔ o un dato que solo puede dar el dueño;
- ``espera == "respuestas"``: fichas sin respuesta (modo manual o modelo caído);
- ``terminada``: informe aprobado.
La interfaz (hito 4) solo tiene que mostrar este estado y llamar a las funciones
de decisión del dueño.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tresia.motor import encuadre, fase_a, fase_b, manual, pasos
from tresia.motor.ejecucion import HECHA, Ejecucion
from tresia.motor.informe import generar_informe


@dataclass
class Estado:
    fase: str
    paso: str = ""
    espera: str | None = None        # "dueno" | "respuestas" | None
    detalle: str = ""
    terminada: bool = False
    pendientes: list[str] = field(default_factory=list)


def _aprobada(run: Ejecucion, fase: str) -> bool:
    return any(d["tipo"] == "aprobacion" for d in run.decisiones(fase))


def _paso_con_modelo(run: Ejecucion, paso: str, preparar, recursos) -> Estado | None:
    """Prepara, envía y comprueba un paso con modelo. ``None`` = completo."""
    from tresia.motor.llamadas import ejecutar_paso
    if not manual.paso_preparado(run, paso):
        preparar(run)
    if recursos is not None and not manual.paso_completo(run, paso):
        ejecutar_paso(run, paso, recursos)
    if manual.paso_completo(run, paso):
        return None
    faltan = manual.ranuras_sin_respuesta(run, paso)
    return Estado(run.fase_actual, paso, "respuestas", "Faltan respuestas de los modelos o pegadas a mano.", pendientes=faltan)


def avanzar(run: Ejecucion, recursos=None) -> Estado:
    while True:
        fase = run.fase_actual
        if fase == "ingesta":
            if not run.decisiones("ingesta"):
                return Estado(fase, espera="dueno", detalle="Añade los materiales con su etiqueta y cierra la ingesta.")
            run.avanzar()

        elif fase == "encuadre":
            if not run.existe("ficha.json"):
                return Estado(fase, espera="dueno", detalle="Responde a las preguntas del encuadre.")
            if not _aprobada(run, fase):
                run.pedir_aprobacion()
                return Estado(fase, espera="dueno", detalle="Confirma la ficha del caso.")
            run.avanzar()

        elif fase == "linea_base":
            if not run.existe("linea_base.json"):
                return Estado(fase, espera="dueno", detalle="Escribe la lista de opciones obvias (línea base).")
            run.avanzar()

        elif fase == "fase_a":
            if (e := _paso_con_modelo(run, fase_a.PASO_FASE_A, fase_a.preparar_fase_a, recursos)):
                return e
            run.avanzar()

        elif fase == "verificacion_a":
            fase_a.verificar_fase_a(run)
            run.avanzar()

        elif fase == "fusion":
            if (e := _paso_con_modelo(run, fase_a.PASO_FUSION, fase_a.preparar_fusion, recursos)):
                return e
            informe = fase_a.cerrar_fusion(run)
            if not informe["valido"]:
                run.pedir_aprobacion()
                return Estado(fase, espera="dueno",
                              detalle="La agrupación no es válida: " + " ".join(informe["errores"])
                              + " Corrígela (corregir_fusion) o vuelve a pedirla.")
            run.avanzar()

        elif fase == "criba":
            if (e := _paso_con_modelo(run, "criba", pasos.preparar_criba, recursos)):
                return e
            run.avanzar()

        elif fase == "agregacion":
            pasos.agregar_criba(run)
            run.avanzar()

        elif fase == "cartera":
            if not run.existe("cartera.json"):
                pasos.proponer_cartera(run)
            if not _aprobada(run, fase):
                run.pedir_aprobacion()
                return Estado(fase, espera="dueno", detalle="Revisa la cartera: añade o quita opciones y apruébala.")
            run.avanzar()

        elif fase == "fase_b":
            eb = fase_b.avanzar_fase_b(run, recursos)
            if eb.espera:
                pend = manual.ranuras_sin_respuesta(run, fase_b.nombre_paso(eb.ciclo, eb.paso))
                return Estado(fase, f"ciclo {eb.ciclo}: {eb.paso}", eb.espera, eb.detalle, pendientes=pend)
            run.avanzar()

        elif fase == "informe":
            if not run.existe("informe.md"):
                generar_informe(run)
            if run.estado["fases"]["informe"] == HECHA:
                return Estado(fase, terminada=True, detalle="Ejecución terminada. Nada se envía ni se publica sin aprobación.")
            if not _aprobada(run, fase):
                run.pedir_aprobacion()
                return Estado(fase, espera="dueno", detalle="Revisa el informe y apruébalo.")
            run.avanzar()
            run.estado["fases"]["informe"] = HECHA
            run.guardar()
        else:
            raise RuntimeError(f"Fase desconocida: {fase}")


def corregir_fusion(run: Ejecucion, grupos) -> dict:
    """El dueño corrige la agrupación (o pega otra); se vuelve a comprobar."""
    run.escribir("fusion_verificador.json", grupos)
    run.registrar_decision("fusion", "correccion_grupos", {"grupos": len(grupos.get("groups", grupos))})
    return fase_a.cerrar_fusion(run)
