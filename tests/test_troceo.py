"""Troceo de las tareas largas del verificador del servidor (SSB-107).

El verificador falso es determinista: responde lo mismo a una ficha completa que
a sus partes. Así se comprueba que (1) ninguna llamada pasa del máximo de prompt
y (2) el resultado unido coincide con el de una sola llamada sobre el mismo caso.
"""

import json
import re

import pytest

from conftest import CASO
from tresia import papeles
from tresia.adaptadores.base import Adaptador, AdaptadorError
from tresia.adaptadores.http import estimar_tokens
from tresia.motor import Ejecucion, manual, troceo
from tresia.motor.llamadas import Recursos, ejecutar_paso

CLAVES = ["text", "part", "owner_decisions", "options", "baseline", "group_ids", "merge_note", "findings",
          "additions", "objective", "owner_principles", "timeline_table", "table_note"]


def entrada(prompt: str, clave: str):
    inicio = prompt.index(f"### {clave}\n") + len(f"### {clave}\n")
    finales = [prompt.find(f"\n\n### {k}\n", inicio) for k in CLAVES if k != clave]
    finales.append(prompt.find("\n\nAnswer with a single JSON", inicio))
    valor = prompt[inicio:min(f for f in finales if f >= 0)]
    if valor.startswith("```json\n"):
        return json.loads(valor.removeprefix("```json\n").removesuffix("\n```"))
    return valor


def tiene(prompt, clave):
    return f"### {clave}\n" in prompt


def frases(texto):
    return [" ".join(f.split()) for f in re.split(r"(?<=[.!?])\s+|\n+", texto) if f.strip()]


def filas_de(texto):
    salida = []
    for linea in texto.splitlines():
        if m := re.match(r"(GATE|ACTIVITY): (.+?) \| (\d{4}-\d{2}) \| (.*)", linea.strip()):
            tipo, nombre, cuando, ref = m.groups()
            fila = {"kind": "gate" if tipo == "GATE" else "activity", "name": nombre, "when": cuando}
            fila["authorises" if tipo == "GATE" else "requires"] = [ref]
            salida.append(fila)
    return salida


def problemas(filas):
    puertas = {f["authorises"][0]: f for f in filas if f["kind"] == "gate"}
    return sorted(({"gate": puertas[f["name"]]["name"], "activity": f["name"], "problem": "Gate not before activity.",
                    "fix": "Move the gate earlier."}
                   for f in filas if f["kind"] == "activity" and f["name"] in puertas
                   and puertas[f["name"]]["when"] >= f["when"]), key=lambda p: p["activity"])


class VerificadorDeterminista(Adaptador):
    """Servidor con contexto fijo: tiene ``cabe`` y ``max_prompt`` como AdaptadorOllama."""

    def __init__(self, max_prompt=100_000, fallar_en=None):
        super().__init__({"proveedor": "falso"})
        self.max_prompt, self.fallar_en, self.prompts = max_prompt, fallar_en, []

    def cabe(self, prompt):
        return (estimar_tokens(prompt) <= self.max_prompt, "no cabe")

    def _llamar(self, prompt):
        assert estimar_tokens(prompt) <= self.max_prompt, "Se envió un prompt que no cabe"
        self.prompts.append(prompt)
        if self.fallar_en and len(self.prompts) == self.fallar_en:
            raise AdaptadorError("Ollama recortó el prompt")
        datos = responder(prompt)
        return "```json\n" + json.dumps(datos, ensure_ascii=False) + "\n```", ""


def responder(prompt):
    tarea = re.search(r"Run ONLY the task «([\w-]+)»", prompt).group(1)
    if tarea == "claims":
        return {"claims": [{"text": f, "type": "position", "strength": "unsupported"}
                           for f in frases(entrada(prompt, "text")) if re.search(r"\d", f)]}
    if tarea == "compliance":
        return {"violations": [f for f in frases(entrada(prompt, "text")) if "Lebanon" in f]}
    if tarea == "timeline-table":
        return {"rows": filas_de(entrada(prompt, "text"))}
    if tarea == "timeline":
        filas = entrada(prompt, "timeline_table") if tiene(prompt, "timeline_table") else filas_de(entrada(prompt, "text"))
        return {"timeline_issues": problemas(filas)}
    if tarea == "arbitrate":
        return {"cards": [{"finding": h["id"], "question": f"Apply «{h['name']}»?",
                           "options": [{"label": "apply", "consequence": "x"}, {"label": "reject", "consequence": "y"}],
                           "default": "apply"} for h in entrada(prompt, "findings")]}
    if tarea == "merge":
        grupos = {}
        for o in entrada(prompt, "options"):
            grupos.setdefault(o["name"].split(" / ")[0], []).append(o["ref"])
        base = set(entrada(prompt, "baseline"))
        return {"groups": [{"id": f"G{i}", "name": n, "members": m, "matches_baseline": n in base}
                           for i, (n, m) in enumerate(grupos.items(), 1)]}
    raise AssertionError(tarea)


def troceado(tarea, entradas, max_prompt):
    v = VerificadorDeterminista(max_prompt)

    def llamar(subtarea, sub):
        prompt = papeles.componer_ficha("verifier", sub, subtarea)
        v._llamar(prompt)               # comprueba el tamaño y lo anota
        return responder(prompt)

    return troceo.resolver(tarea, entradas, llamar, max_prompt), v


def entera(tarea, entradas):
    return responder(papeles.componer_ficha("verifier", entradas, tarea))


V42 = (CASO / "v42.md").read_text(encoding="utf-8")


# --- partición del texto ---------------------------------------------------------------------------
def test_partir_texto_no_pierde_nada_y_respeta_el_maximo():
    trozos = troceo.partir_texto(V42, 1200)
    assert len(trozos) > 3
    assert all(estimar_tokens(t) <= 1200 for _, t in trozos)
    assert "".join("".join(t for _, t in trozos).split()) == "".join(V42.split())
    assert all(s for s, _ in trozos)                      # cada trozo dice qué secciones cubre


def test_texto_sin_encabezados_ni_parrafos_se_parte_igual():
    texto = "Una frase con 1 dato. " * 2000
    trozos = troceo.partir_texto(texto, 500)
    assert all(estimar_tokens(t) <= 500 for _, t in trozos)
    assert "".join("".join(t for _, t in trozos).split()) == "".join(texto.split())


# --- cada tarea: ningún prompt pasa del máximo y el resultado coincide -------------------------
MAX = 2500


def test_claims_troceado_coincide_con_una_llamada():
    resultado, v = troceado("claims", {"text": V42}, MAX)
    assert len(v.prompts) > 3 and all(estimar_tokens(p) <= MAX for p in v.prompts)
    assert {c["text"] for c in resultado["claims"]} == {c["text"] for c in entera("claims", {"text": V42})["claims"]}


def test_claims_se_trocea_aunque_quepa_si_el_texto_es_largo():
    assert troceo.conviene("claims", {"text": V42})
    assert not troceo.conviene("claims", {"text": "Corto."})
    assert not troceo.conviene("timeline", {"text": V42})


def test_compliance_troceado_coincide():
    entradas = {"text": V42, "owner_decisions": ["Do not name private persons."]}
    resultado, v = troceado("compliance", entradas, MAX)
    assert len(v.prompts) > 1
    assert sorted(resultado["violations"]) == sorted(set(entera("compliance", entradas)["violations"]))


def _texto_timeline():
    secciones = []
    for p in range(1, 9):
        lineas = [f"## Programme {p}", "Some context sentence that fills the section. " * 40]
        lineas.append(f"GATE: Permit {p} | 2027-{p:02d} | Works {p}")
        # La actividad del programa p está en la sección siguiente: la tabla debe unirlas.
        if p > 1:
            mes = p - 1 if p % 2 else p + 2
            lineas.append(f"ACTIVITY: Works {p - 1} | 2027-{mes:02d} | Permit {p - 1}")
        secciones.append("\n\n".join(lineas))
    return "\n\n".join(secciones)


def test_timeline_por_tabla_ve_puertas_y_actividades_de_secciones_distintas():
    texto = _texto_timeline()
    resultado, v = troceado("timeline", {"text": texto}, MAX)
    tareas = [re.search(r"Run ONLY the task «([\w-]+)»", p).group(1) for p in v.prompts]
    assert tareas.count("timeline-table") > 1 and tareas[-1] == "timeline"
    esperado = entera("timeline", {"text": texto})["timeline_issues"]
    assert esperado and resultado["timeline_issues"] == esperado


def test_arbitrate_por_lotes():
    hallazgos = json.loads((CASO / "atacante_c4.json").read_text(encoding="utf-8"))["findings"]
    entradas = {"findings": hallazgos, "additions": [], "objective": "x", "owner_decisions": [], "owner_principles": []}
    resultado, v = troceado("arbitrate", entradas, MAX)
    assert len(v.prompts) > 1
    assert [t["finding"] for t in resultado["cards"]] == [h["id"] for h in hallazgos]


def _opciones():
    opciones, k = [], 0
    for etapa in ("detect", "document", "litigate", "recover"):
        for mecanismo in ("registry", f"{etapa}-tool", f"{etapa}-network"):
            for variante in range(4):
                k += 1
                opciones.append({"ref": f"E{k % 3 + 1}:O{k}", "name": f"{mecanismo} / variant {variante}",
                                 "description": "A long description of the option and how it works. " * 6,
                                 "chain_stage": etapa, "depends_on_ai": False})
    return opciones


def test_merge_por_etapas_y_luego_entre_etapas():
    entradas = {"baseline": ["registry"], "options": _opciones(), "group_ids": "Use C01, C02, … in order."}
    resultado, v = troceado("merge", entradas, 3000)
    assert len(v.prompts) > 2
    unico = entera("merge", entradas)
    assert {(g["name"], frozenset(g["members"]), g["matches_baseline"]) for g in resultado["groups"]} == \
           {(g["name"], frozenset(g["members"]), g["matches_baseline"]) for g in unico["groups"]}
    assert [g["id"] for g in resultado["groups"]] == [f"C{i:02d}" for i in range(1, len(resultado["groups"]) + 1)]


def test_elemento_que_no_cabe_solo_es_error():
    with pytest.raises(troceo.ErrorTroceo):
        troceo.empaquetar([1, 2, 3], lambda lote: 2 not in lote)


# --- integración con el motor -------------------------------------------------------------------
def _run_con_claims(tmp_path):
    run = Ejecucion.crear(tmp_path, "Troceo")
    manual.preparar_ficha(run, "b1_verificacion", "claims", "verifier", {"text": V42},
                          "faseB/ciclo_1/verificador_claims_v1.json", tarea="claims", asignado="verificador")
    return run


class Respaldo(Adaptador):
    def __init__(self):
        super().__init__({"proveedor": "falso"})
        self.prompts = []

    def _llamar(self, prompt):
        self.prompts.append(prompt)
        return json.dumps(responder(prompt), ensure_ascii=False), ""


def test_el_motor_trocea_y_no_usa_el_respaldo(tmp_path):
    run = _run_con_claims(tmp_path)
    servidor, respaldo = VerificadorDeterminista(MAX), Respaldo()
    ejecutar_paso(run, "b1_verificacion", Recursos(modelos={}, verificadores=lambda r, f: [(servidor, "srv"), (respaldo, "resp")]))
    assert manual.paso_completo(run, "b1_verificacion")
    assert len(servidor.prompts) > 3 and not respaldo.prompts
    datos = run.leer("faseB/ciclo_1/verificador_claims_v1.json")
    assert {c["text"] for c in datos["claims"]} == {c["text"] for c in entera("claims", {"text": V42})["claims"]}
    assert run.existe("prompts/b1_verificacion/claims_trozo01.md")
    assert any("por partes" in a["texto"] for a in run.estado["avisos"])


def test_si_falla_un_trozo_pasa_al_respaldo_con_la_ficha_completa(tmp_path):
    run = _run_con_claims(tmp_path)
    servidor, respaldo = VerificadorDeterminista(MAX, fallar_en=2), Respaldo()
    ejecutar_paso(run, "b1_verificacion", Recursos(modelos={}, verificadores=lambda r, f: [(servidor, "srv"), (respaldo, "resp")]))
    assert manual.paso_completo(run, "b1_verificacion")
    assert len(respaldo.prompts) == 1 and V42[:200] in respaldo.prompts[0]
    assert run.estado["identidades"]["b1_verificacion:claims"] == "resp"
    assert any("falló la tarea por partes" in a["texto"] for a in run.estado["avisos"])


def test_sin_respaldo_queda_para_el_modo_manual(tmp_path):
    run = _run_con_claims(tmp_path)
    servidor = VerificadorDeterminista(MAX, fallar_en=1)
    r = ejecutar_paso(run, "b1_verificacion", Recursos(modelos={}, verificadores=lambda r, f: [(servidor, "srv")]))
    assert r[0].pasa_a_manual and not manual.paso_completo(run, "b1_verificacion")
    assert run.estado["pendientes"]["b1_verificacion"]["claims"]["estado"] == "esperando"
