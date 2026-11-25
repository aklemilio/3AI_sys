"""Fusión de la fase A: comprobaciones y métricas (SPEC §4.6, §11.3).

La agrupación la propone el verificador; aquí solo se comprueba y se mide:
cada opción en exactamente un grupo, todo grupo con nombre legible (lección 13),
novedad frente a la línea base, Jaccard y aportes únicos por explorador, y
grupos que dependen de IA.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations

MAX_PALABRAS_NOMBRE = 8


def normalizar_grupos(grupos) -> dict[str, dict]:
    """Acepta el formato del verificador (``{"groups": [...]}`` con
    ``matches_baseline``) o el de los fixtures (``{id: {name, members, baseline}}``).
    Devuelve ``{id: {"name", "members", "baseline"}}`` conservando el orden."""
    if isinstance(grupos, dict) and "groups" in grupos:
        grupos = grupos["groups"]
    if isinstance(grupos, list):
        return {
            g["id"]: {
                "name": g.get("name", ""),
                "members": list(g.get("members", [])),
                "baseline": bool(g.get("matches_baseline", g.get("baseline", False))),
            }
            for g in grupos
        }
    return {
        gid: {
            "name": g.get("name", ""),
            "members": list(g.get("members", [])),
            "baseline": bool(g.get("baseline", g.get("matches_baseline", False))),
        }
        for gid, g in grupos.items()
    }


def indexar_exploradores(exploradores: dict[str, dict]) -> dict[str, dict]:
    """``{"E1": salida_json, ...}`` -> ``{"E1:O3": opcion, ...}``."""
    return {f"{e}:{o['id']}": o for e, salida in exploradores.items() for o in salida["options"]}


@dataclass
class InformeFusion:
    opciones: int
    opciones_por_explorador: dict[str, int]
    grupos: int
    nuevos: int
    novedad: float
    jaccard: dict[str, float]
    aportes_unicos: dict[str, int]
    en_los_tres: int
    grupos_con_ia: int
    sin_asignar: list[str] = field(default_factory=list)
    repetidas: list[str] = field(default_factory=list)
    desconocidas: list[str] = field(default_factory=list)
    sin_nombre: list[str] = field(default_factory=list)
    nombres_largos: list[str] = field(default_factory=list)

    @property
    def valido(self) -> bool:
        """Bloquea el avance: asignación no única o grupos sin nombre."""
        return not (self.sin_asignar or self.repetidas or self.desconocidas or self.sin_nombre)

    def errores(self) -> list[str]:
        e = []
        if self.sin_asignar:
            e.append(f"Opciones sin grupo: {', '.join(self.sin_asignar)}")
        if self.repetidas:
            e.append(f"Opciones en más de un grupo: {', '.join(self.repetidas)}")
        if self.desconocidas:
            e.append(f"Miembros que no existen en la fase A: {', '.join(self.desconocidas)}")
        if self.sin_nombre:
            e.append(f"Grupos sin nombre legible: {', '.join(self.sin_nombre)}")
        return e

    def avisos(self) -> list[str]:
        if self.nombres_largos:
            return [f"Nombres de más de {MAX_PALABRAS_NOMBRE} palabras: {', '.join(self.nombres_largos)}"]
        return []


def comprobar_fusion(grupos, exploradores: dict[str, dict]) -> InformeFusion:
    G = normalizar_grupos(grupos)
    opciones = indexar_exploradores(exploradores)
    asignadas = [m for g in G.values() for m in g["members"]]

    vistos, repetidas = set(), []
    for m in asignadas:
        if m in vistos and m not in repetidas:
            repetidas.append(m)
        vistos.add(m)
    sin_asignar = [o for o in opciones if o not in vistos]
    desconocidas = [m for m in dict.fromkeys(asignadas) if m not in opciones]

    sin_nombre = [gid for gid, g in G.items() if not g["name"].strip() or g["name"].strip() == gid]
    nombres_largos = [gid for gid, g in G.items() if len(g["name"].split()) > MAX_PALABRAS_NOMBRE]

    nuevos = sum(not g["baseline"] for g in G.values())
    cobertura = {e: {gid for gid, g in G.items() if any(m.split(":")[0] == e for m in g["members"])} for e in exploradores}
    jaccard = {}
    for a, b in combinations(exploradores, 2):
        union = cobertura[a] | cobertura[b]
        jaccard[f"{a}-{b}"] = round(len(cobertura[a] & cobertura[b]) / len(union), 2) if union else 0.0
    unicos = {e: len([g for g in cobertura[e] if all(g not in cobertura[o] for o in exploradores if o != e)]) for e in exploradores}
    en_todos = len(set.intersection(*cobertura.values())) if cobertura else 0
    con_ia = sum(any(opciones.get(m, {}).get("depends_on_ai") for m in g["members"]) for g in G.values())

    return InformeFusion(
        opciones=len(opciones),
        opciones_por_explorador={e: len(s["options"]) for e, s in exploradores.items()},
        grupos=len(G),
        nuevos=nuevos,
        novedad=round(nuevos / len(G), 4) if G else 0.0,
        jaccard=jaccard,
        aportes_unicos=unicos,
        en_los_tres=en_todos,
        grupos_con_ia=con_ia,
        sin_asignar=sin_asignar,
        repetidas=repetidas,
        desconocidas=desconocidas,
        sin_nombre=sin_nombre,
        nombres_largos=nombres_largos,
    )
