"""Carga los papeles de ``skills/<papel>/SKILL.md`` y compone la ficha (prompt).

El cuerpo del SKILL.md se usa tal cual (en inglés). Las entradas del motor se
añaden al final en una sección «Case inputs», cada una con su nombre; así no
hace falta sustituir marcadores dentro del texto y el SKILL.md sigue siendo
la única definición del papel.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from tresia import SKILLS

PAPELES = ["explorer", "screener", "builder", "attacker", "cross-verdict", "verifier"]
ESQUEMA_POR_PAPEL = {
    "explorer": "explorer",
    "screener": "screener",
    "builder": "builder",
    "attacker": "attacker",
    "cross-verdict": "cross-verdict",
}
ESQUEMA_POR_TAREA_VERIFICADOR = {
    "merge": "verifier-merge",
    "claims": "verifier-claims",
    "timeline": "verifier-timeline",
    "arbitrate": "verifier-arbitrate",
}

_FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


@dataclass
class Papel:
    nombre: str
    descripcion: str
    cuerpo: str


def cargar(nombre: str) -> Papel:
    texto = (SKILLS / nombre / "SKILL.md").read_text(encoding="utf-8")
    meta, cuerpo = {}, texto
    if m := _FRONTMATTER.match(texto):
        for linea in m.group(1).splitlines():
            if ":" in linea:
                k, v = linea.split(":", 1)
                meta[k.strip()] = v.strip()
        cuerpo = texto[m.end():]
    return Papel(nombre=meta.get("name", nombre), descripcion=meta.get("description", ""), cuerpo=cuerpo.strip())


def esquema_de(papel: str, tarea: str | None = None) -> str | None:
    if papel == "verifier":
        return ESQUEMA_POR_TAREA_VERIFICADOR.get(tarea or "")
    return ESQUEMA_POR_PAPEL.get(papel)


def _formatear(valor) -> str:
    if isinstance(valor, str):
        return valor.strip()
    return "```json\n" + json.dumps(valor, ensure_ascii=False, indent=1) + "\n```"


def componer_ficha(papel: str, entradas: dict, tarea: str | None = None) -> str:
    """Prompt completo: papel + tarea (si es del verificador) + entradas del caso."""
    p = cargar(papel)
    partes = [p.cuerpo]
    if tarea:
        partes.append(f"## Task for this call\nRun ONLY the task «{tarea}» described above.")
    if entradas:
        bloques = [f"### {k}\n{_formatear(v)}" for k, v in entradas.items()]
        partes.append("## Case inputs\n\n" + "\n\n".join(bloques))
    partes.append("Answer with a single JSON object inside ONE ```json code block, as specified above.")
    return "\n\n".join(partes) + "\n"
