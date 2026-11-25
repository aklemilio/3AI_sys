"""Agregación determinista de la criba ciega (SPEC §4.8, §11.1).

- Se elimina una opción solo con 2 de 3 votos fatales verificados.
- Mediana por criterio, total de medianas, desacuerdo cuando el rango es >= 2.
- Orden: total, luego los dos criterios prioritarios (por defecto impacto e inclusión).
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from tresia.calculo.fusion import indexar_exploradores, normalizar_grupos

CRITERIOS_POR_DEFECTO = ["impact", "feasibility", "evidence", "safety", "inclusion"]
PRIORITARIOS_POR_DEFECTO = ["impact", "inclusion"]
VOTOS_PARA_ELIMINAR = 2
RANGO_DESACUERDO = 2


@dataclass
class ResultadoCriba:
    ranking: list[dict]          # filas ordenadas, mismo formato que ranking_c4.json
    eliminadas: list[dict]       # opciones con >= 2 votos fatales verificados, con motivos y rescates
    incompletas: dict[str, list[str]]  # cribador -> ids sin evaluar
    votos_fatales: int


def voto_fatal_valido(evaluacion: dict) -> bool:
    """Un voto fatal solo cuenta con motivo, respaldo y rescate (SPEC §4.7)."""
    return bool(
        evaluacion.get("fatal")
        and evaluacion.get("fatal_reason", "").strip()
        and evaluacion.get("support")
        and evaluacion.get("rescue", "").strip()
    )


def clave_orden(fila: dict, prioritarios: list[str]) -> tuple:
    return (-fila["tot"], *(-fila["med"][c] for c in prioritarios))


def _num(x):
    return int(x) if float(x).is_integer() else x


def agregar(
    grupos,
    exploradores: dict[str, dict],
    cribas: dict[str, dict],
    criterios: list[str] | None = None,
    prioritarios: list[str] | None = None,
    votos_verificados: set[tuple[str, str]] | None = None,
) -> ResultadoCriba:
    """``votos_verificados``: pares (cribador, id) que el verificador dio por
    respaldados. Si es ``None`` cuentan los votos con motivo, respaldo y rescate."""
    criterios = criterios or CRITERIOS_POR_DEFECTO
    prioritarios = prioritarios or PRIORITARIOS_POR_DEFECTO
    G = normalizar_grupos(grupos)
    opciones = indexar_exploradores(exploradores)
    S = {s: {a["id"]: a for a in salida["assessments"]} for s, salida in cribas.items()}

    incompletas = {s: [g for g in G if g not in S[s]] for s in S}
    incompletas = {s: ids for s, ids in incompletas.items() if ids}
    total_fatales = sum(bool(a.get("fatal")) for s in S for a in S[s].values())

    filas, eliminadas = [], []
    for gid, g in G.items():
        evals = {s: S[s][gid] for s in S if gid in S[s]}
        fatales = [
            (s, a) for s, a in evals.items()
            if voto_fatal_valido(a) and (votos_verificados is None or (s, gid) in votos_verificados)
        ]
        med = {c: _num(statistics.median(a["scores"][c] for a in evals.values() if c in a["scores"])) for c in criterios}
        dis = [
            c for c in criterios
            if (vals := [a["scores"][c] for a in evals.values() if c in a["scores"]]) and max(vals) - min(vals) >= RANGO_DESACUERDO
        ]
        primero = opciones.get(g["members"][0], {}) if g["members"] else {}
        fila = dict(
            id=gid,
            name=g["name"],
            tot=_num(sum(med.values())),
            med=med,
            dis=dis,
            stage=primero.get("chain_stage", ""),
            new=not g["baseline"],
            ai=any(opciones.get(m, {}).get("depends_on_ai", False) for m in g["members"]),
        )
        if len(fatales) >= VOTOS_PARA_ELIMINAR:
            fila["fatal"] = [
                {"cribador": s, "motivo": a["fatal_reason"], "rescate": a["rescue"]} for s, a in fatales
            ]
            eliminadas.append(fila)
        else:
            filas.append(fila)

    filas.sort(key=lambda f: clave_orden(f, prioritarios))  # orden estable ante empates
    return ResultadoCriba(ranking=filas, eliminadas=eliminadas, incompletas=incompletas, votos_fatales=total_fatales)
