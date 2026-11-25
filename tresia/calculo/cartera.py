"""Cartera por regla (SPEC §4.9, lección 16).

1. Las N primeras del ranking.
2. Si en el corte hay empate en las tres claves con la N-ésima, entran todas las empatadas.
3. La mejor de cada etapa de la cadena que falte.
4. Las opciones nuevas que dos cribadores proponen por separado entran como combinaciones
   (la coincidencia la señala el verificador; aquí llega ya emparejada).
5. El resto se archiva con su motivo y puede volver.
6. El dueño puede añadir o quitar; su decisión prevalece y queda marcada.
"""

from __future__ import annotations

from tresia.calculo.agregacion import PRIORITARIOS_POR_DEFECTO, clave_orden

MOTIVOS = {
    "corte": "Entre las {n} primeras",
    "empate": "Empatada en el corte en las tres claves",
    "etapa": "Mejor opción de la etapa «{etapa}», que faltaba",
    "combinacion": "Opción nueva propuesta por separado por dos cribadores",
    "dueno": "Añadida por decisión del dueño",
}


def cartera_por_regla(
    ranking: list[dict],
    n: int,
    etapas: list[str],
    prioritarios: list[str] | None = None,
    combinaciones: list[dict] | None = None,
    anadir_dueno: list[str] | None = None,
    quitar_dueno: list[str] | None = None,
) -> dict:
    """Devuelve ``{"seleccion": [...], "archivo": [...]}``. Cada elemento lleva
    ``id``, ``name``, ``origen`` (corte, empate, etapa, combinacion, dueno) y ``motivo``."""
    prioritarios = prioritarios or PRIORITARIOS_POR_DEFECTO
    por_id = {f["id"]: f for f in ranking}
    seleccion: list[dict] = []

    def meter(fila, origen, **fmt):
        seleccion.append({"id": fila["id"], "name": fila["name"], "stage": fila.get("stage", ""),
                          "origen": origen, "motivo": MOTIVOS[origen].format(n=n, **fmt)})

    for fila in ranking[:n]:
        meter(fila, "corte")
    if len(ranking) > n and n > 0:
        clave_corte = clave_orden(ranking[n - 1], prioritarios)
        for fila in ranking[n:]:
            if clave_orden(fila, prioritarios) == clave_corte:
                meter(fila, "empate")
            else:
                break

    elegidas = {s["id"] for s in seleccion}
    for etapa in etapas:
        if any(por_id[i].get("stage") == etapa for i in elegidas):
            continue
        mejor = next((f for f in ranking if f.get("stage") == etapa), None)
        if mejor:
            meter(mejor, "etapa", etapa=etapa)
            elegidas.add(mejor["id"])

    for comb in combinaciones or []:
        seleccion.append({"id": comb["id"], "name": comb["name"], "stage": comb.get("stage", ""),
                          "origen": "combinacion", "motivo": MOTIVOS["combinacion"],
                          "propuesta_por": comb.get("propuesta_por", [])})

    # Decisiones del dueño: prevalecen sobre la regla y quedan marcadas.
    quitar = set(quitar_dueno or [])
    archivo = []
    if quitar:
        for s in [s for s in seleccion if s["id"] in quitar]:
            seleccion.remove(s)
            archivo.append({**s, "origen": "dueno", "motivo": "Quitada por decisión del dueño"})
    for gid in anadir_dueno or []:
        if gid in por_id and gid not in {s["id"] for s in seleccion}:
            meter(por_id[gid], "dueno")

    dentro = {s["id"] for s in seleccion} | {a["id"] for a in archivo}
    for pos, fila in enumerate(ranking, 1):
        if fila["id"] not in dentro:
            archivo.append({"id": fila["id"], "name": fila["name"], "stage": fila.get("stage", ""),
                            "origen": "regla", "motivo": f"Fuera del corte (puesto {pos}); puede volver"})
    return {"seleccion": seleccion, "archivo": archivo}
