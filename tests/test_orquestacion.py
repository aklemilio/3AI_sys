"""Orquestación de punta a punta (SSB-108) con el caso real del ciclo 4.

Los modelos son falsos: devuelven las respuestas reales de los fixtures según el
papel y la ranura, así que todo el motor (fichas, asignación ciega, limpieza,
esquemas, fusión, criba, cartera, fase B, verificador e informe) corre de verdad.
"""

import json
import re

import pytest

from conftest import CASO, ETAPAS_C4
from tresia.adaptadores.base import Adaptador
from tresia.motor import Ejecucion, encuadre, fase_b, manual, pasos
from tresia.motor.flujo import avanzar
from tresia.motor.llamadas import Recursos

ESPERADA = ["C21", "C25", "C26", "C10", "C13", "C29", "C35", "C04", "C09", "C27", "C33", "C16"]


def leer(nombre):
    return (CASO / nombre).read_text(encoding="utf-8")


def grupos_formato_verificador():
    g = json.loads(leer("grupos_c4.json"))
    return {"groups": [{"id": k, "name": v["name"], "members": v["members"], "matches_baseline": v["baseline"]}
                       for k, v in g.items()]}


class ModeloFalso(Adaptador):
    """Responde con el fixture que corresponde a la ranura que tiene asignada."""

    def __init__(self, letra, run_ref):
        super().__init__({"proveedor": "falso"})
        self.letra, self.run_ref, self.llamadas = letra, run_ref, []

    def _ranura(self, fase):
        inversa = {v: k for k, v in self.run_ref[0].estado["asignacion"][fase].items()}
        return inversa[self.letra]

    def _llamar(self, prompt):
        self.llamadas.append(prompt[:60])
        if prompt.startswith("You are one of three independent explorers"):
            texto = leer(f"{self._ranura('fase_a')}.json")
        elif prompt.startswith("You are one of three independent screeners"):
            texto = leer(f"{self._ranura('criba')}.json").replace("S", "S", 1)
        elif prompt.startswith("You are the builder"):
            texto = leer("v4_builder.txt") if "### mode\nbuild" in prompt else leer("v41_builder.txt")
        elif prompt.startswith("You are the attacker"):
            texto = "Here is my attack:\n```json\n" + leer("atacante_c4.json") + "\n```"
        elif prompt.startswith("You did not build this version"):
            run = self.run_ref[0]
            pend = next(p for k, p in run.estado["pendientes"].items() if k.endswith("_veredicto"))
            ranura = next(r for r, p in pend.items() if p["asignado"] == self.letra)
            texto = leer(f"{ranura}.json")
        else:
            raise AssertionError("Papel inesperado: " + prompt[:80])
        return texto, texto


class VerificadorFalso(Adaptador):
    def __init__(self):
        super().__init__({"proveedor": "falso"})
        self.tareas = []

    def _llamar(self, prompt):
        tarea = re.search(r"Run ONLY the task «(\w+)»", prompt).group(1)
        self.tareas.append(tarea)
        if tarea == "merge":
            datos = grupos_formato_verificador()
        elif tarea == "claims":
            datos = {"claims": [{"text": "Law 75/1999 limits broadcaster rights to 50 years.", "type": "source",
                                 "strength": "weak", "note": "No fragment in this version."}]}
        elif tarea == "timeline":
            datos = {"timeline_issues": []}
        elif tarea == "compliance":
            datos = {"violations": [], "silent_weakenings": []}
        elif tarea == "arbitrate":
            hallazgos = json.loads(leer("atacante_c4.json"))["findings"]
            datos = {"cards": [{"finding": h["id"], "question": f"¿Aplicamos la corrección de «{h['name']}»?",
                                "context": h["problem"][:120],
                                "options": [{"label": "apply", "consequence": "Se corrige."},
                                            {"label": "reject", "consequence": "Queda como está."}],
                                "default": "apply", "recommendation": "apply"} for h in hallazgos]}
        else:
            raise AssertionError(tarea)
        texto = json.dumps(datos, ensure_ascii=False)
        return texto, texto


@pytest.fixture
def entorno(tmp_path):
    run_ref = [None]
    modelos = {l: ModeloFalso(l, run_ref) for l in "ABC"}
    verificador = VerificadorFalso()
    recursos = Recursos(modelos=modelos, verificadores=lambda run, ficha: [(verificador, "verificador-falso")])
    run = Ejecucion.crear(tmp_path, "Caso libanés ciclo 4 (simulado)")
    run_ref[0] = run
    return run, recursos, modelos, verificador


def _hasta_linea_base(run):
    encuadre.ingestar(run, "Objetivo de conservación", "objeto",
                      texto="Preserve the spoken Lebanese cultural and linguistic heritage at risk of being lost.")
    encuadre.ingestar(run, "Notas internas del dueño", "contexto", texto="SECRETO: esto nunca debe llegar a los papeles.")
    e = avanzar(run)
    assert e.fase == "ingesta" and e.espera == "dueno"
    encuadre.cerrar_ingesta(run)

    e = avanzar(run)
    assert e.fase == "encuadre" and e.espera == "dueno"
    ficha = encuadre.responder_encuadre(run, {
        "objetivo": "Preserve the spoken Lebanese cultural and linguistic heritage that is at risk of being flattened or lost.",
        "destinatarios": "People who do not read or write, low-income, rural, older people, the diaspora, future generations.",
        "caras": ["Lebanese law as written", "GDPR required by foreign funders", "Real market practice", "Copyright and broadcaster ownership"],
    }, {"etapas": ETAPAS_C4, "limites": {"cuerpo": 1600, "anexo": 800}})
    assert "decision" in ficha["valores_por_defecto"] and ficha["decision"] == "ambas"
    e = avanzar(run)
    assert e.espera == "dueno" and "Confirma" in e.detalle
    run.aprobar("Ficha confirmada")

    e = avanzar(run)
    assert e.fase == "linea_base" and e.espera == "dueno"
    G = json.loads(leer("grupos_c4.json"))
    encuadre.registrar_linea_base(run, [v["name"] for v in G.values() if v["baseline"]])


def test_ejecucion_completa_con_modelos(entorno, ranking_esperado):
    run, recursos, modelos, verificador = entorno
    _hasta_linea_base(run)

    # Fase A → verificación A → fusión → criba → agregación → cartera, sin intervención.
    e = avanzar(run, recursos)
    assert e.fase == "cartera" and e.espera == "dueno"
    # El contexto nunca llega a los papeles, ni la línea base a los exploradores.
    for paso in ("fase_a", "criba"):
        for ficha in (run.carpeta / "prompts" / paso).glob("*.md"):
            texto = ficha.read_text(encoding="utf-8")
            assert "SECRETO" not in texto
            assert "Notas internas" not in texto
    assert sorted(run.estado["asignacion"]["fase_a"].values()) == ["A", "B", "C"]
    verif_a = run.leer("faseA/verificacion.json")
    assert set(verif_a["por_explorador"]) == {"E1", "E2", "E3"}
    assert run.leer("ranking.json") == ranking_esperado
    assert [s["id"] for s in run.leer("cartera.json")["seleccion"]] == ESPERADA

    pasos.decidir_cartera(run, anadir=["C03", "C01"], motivo="Rescate urgente de cintas")
    run.aprobar("Cartera confirmada")

    # Fase B, ciclo 1: constructor A, atacante B, evaluadores B y C.
    e = avanzar(run, recursos)
    assert e.fase == "fase_b" and e.espera == "dueno" and "tarjetas" in e.detalle
    asig = {r: p["asignado"] for r, p in run.estado["pendientes"]["b1_constructor"].items()}
    assert asig == {"constructor": "A"}
    assert run.estado["pendientes"]["b1_ataque"]["atacante"]["asignado"] == "B"
    assert run.existe("faseB/ciclo_1/version_v1.md") and run.existe("faseB/ciclo_1/tarjetas.json")
    constructor_prompt = run.leer("prompts/b1_constructor/constructor.md")
    assert "C03" in constructor_prompt and "Rescate urgente de cintas" in constructor_prompt   # decisión del dueño
    assert "SECRETO" not in constructor_prompt

    fase_b.decidir_tarjetas(run, {"A1": {"opcion": "reject", "nota": "Fuera de alcance"}}, usar_por_defecto=True)
    e = avanzar(run, recursos)
    assert e.espera == "dueno" and "Adoptar" in e.detalle
    assert {r: p["asignado"] for r, p in run.estado["pendientes"]["b1_veredicto"].items()} == {"V1": "B", "V2": "C"}
    notas = run.leer("faseB/ciclo_1/notas_verificador_v1.1.json")
    assert any("URL de fuentes" in a for a in notas["alertas"])          # la v4.1 perdió las fuentes
    assert any("Recorte declarado" in a for a in notas["alertas"])
    correccion = run.leer("prompts/b1_correccion/constructor.md")
    assert '"owner_disposition": "reject"' in correccion

    fase_b.decidir_cierre_ciclo(run, "adoptar", "Suficiente para el piloto")
    e = avanzar(run, recursos)
    assert e.fase == "informe" and e.espera == "dueno"
    informe = run.leer("informe.md")
    for texto in ("v1.1", "Cartera", "decisión del dueño", "URL de fuentes", "Método", "41 grupos"):
        assert texto in informe, texto
    run.aprobar("Informe aprobado")
    assert avanzar(run, recursos).terminada

    assert verificador.tareas.count("merge") == 1 and verificador.tareas.count("arbitrate") == 1
    assert run.estado["identidades"]["b1_constructor:constructor"] == "A"


def test_modo_manual_se_detiene_y_continua_al_pegar(entorno):
    run, _, _, _ = entorno
    _hasta_linea_base(run)
    e = avanzar(run)                       # sin recursos: todo a mano
    assert e.fase == "fase_a" and e.espera == "respuestas" and e.pendientes == ["E1", "E2", "E3"]
    for r in ("E1", "E2", "E3"):
        assert manual.recibir_respuesta(run, "fase_a", r, leer(f"{r}.json")).ok
    e = avanzar(run)
    assert e.fase == "fusion" and e.pendientes == ["V"]
    assert manual.recibir_respuesta(run, "fusion", "V", json.dumps(grupos_formato_verificador())).ok
    e = avanzar(run)
    assert e.fase == "criba" and e.pendientes == ["S1", "S2", "S3"]


def test_fusion_invalida_espera_al_dueno_y_se_corrige(entorno):
    from tresia.motor.flujo import corregir_fusion
    run, _, _, _ = entorno
    _hasta_linea_base(run)
    avanzar(run)
    for r in ("E1", "E2", "E3"):
        manual.recibir_respuesta(run, "fase_a", r, leer(f"{r}.json"))
    avanzar(run)
    malo = grupos_formato_verificador()
    malo["groups"] = malo["groups"][1:]                  # sin el grupo C01: E2:O1 queda sin grupo
    manual.recibir_respuesta(run, "fusion", "V", json.dumps(malo))
    e = avanzar(run)
    assert e.fase == "fusion" and e.espera == "dueno" and "E2:O1" in e.detalle
    assert corregir_fusion(run, grupos_formato_verificador())["valido"]
    assert avanzar(run).fase == "criba"


def test_otro_ciclo_rota_el_constructor(entorno):
    run, recursos, _, _ = entorno
    _hasta_linea_base(run)
    avanzar(run, recursos)
    run.aprobar("Cartera")
    avanzar(run, recursos)
    fase_b.decidir_tarjetas(run, usar_por_defecto=True)
    avanzar(run, recursos)
    fase_b.decidir_cierre_ciclo(run, "otro_ciclo", "Falta restituir las fuentes")
    e = avanzar(run, recursos)
    assert e.espera == "dueno" and e.paso.startswith("ciclo 2")
    assert run.estado["pendientes"]["b2_constructor"]["constructor"]["asignado"] == "B"
    assert run.estado["pendientes"]["b2_ataque"]["atacante"]["asignado"] == "C"
    assert "Falta restituir las fuentes" in run.leer("prompts/b2_constructor/constructor.md")
