"""Pruebas de aceptación 1, 2, 3 y 6 de la SPEC (§11) con el caso real del ciclo 4."""

import json

import pytest

from conftest import CASO, ETAPAS_C4
from tresia.calculo import esquemas
from tresia.calculo.agregacion import agregar
from tresia.calculo.cartera import cartera_por_regla
from tresia.calculo.fusion import comprobar_fusion
from tresia.motor import Ejecucion, PuertaCerrada, manual, pasos


# --- Prueba 1: agregación de la criba ----------------------------------------------
def test_1_agregacion_reproduce_ranking(grupos, exploradores, cribas, ranking_esperado):
    r = agregar(grupos, exploradores, cribas)
    assert r.votos_fatales == 0 and not r.eliminadas and not r.incompletas
    assert [f["id"] for f in r.ranking] == [f["id"] for f in ranking_esperado]
    for obtenida, esperada in zip(r.ranking, ranking_esperado):
        assert obtenida["med"] == esperada["med"], obtenida["id"]
        assert obtenida["tot"] == esperada["tot"], obtenida["id"]
        assert obtenida["dis"] == esperada["dis"], obtenida["id"]
    assert r.ranking == ranking_esperado


def test_1b_dos_votos_fatales_verificados_eliminan(grupos, exploradores, cribas):
    import copy
    S = copy.deepcopy(cribas)
    fatal = {"fatal": True, "fatal_reason": "Cannot work", "rescue": "Do X instead",
             "support": [{"type": "reasoning", "claim": "c", "premises": ["p"]}]}
    for s in ("S1", "S2"):
        next(a for a in S[s]["assessments"] if a["id"] == "C21").update(fatal)
    r = agregar(grupos, exploradores, S)
    assert [e["id"] for e in r.eliminadas] == ["C21"]
    assert all(e["rescate"] for e in r.eliminadas[0]["fatal"])
    # Un solo voto o un voto sin rescate no elimina.
    next(a for a in S["S2"]["assessments"] if a["id"] == "C21")["rescue"] = ""
    assert not agregar(grupos, exploradores, S).eliminadas


# --- Prueba 2: cartera por regla ----------------------------------------------------
ESPERADA = ["C21", "C25", "C26", "C10", "C13", "C29", "C35", "C04", "C09", "C27", "C33", "C16"]


def test_2_cartera_por_regla(ranking_esperado):
    c = cartera_por_regla(ranking_esperado, 10, ETAPAS_C4)
    ids = [s["id"] for s in c["seleccion"]]
    assert ids == ESPERADA
    origen = {s["id"]: s["origen"] for s in c["seleccion"]}
    assert origen["C33"] == "empate" and origen["C16"] == "etapa"
    assert "C03" not in ids and "C01" not in ids
    assert len(c["archivo"]) == len(ranking_esperado) - len(ESPERADA)
    assert all(a["motivo"] for a in c["archivo"])


def test_2b_decision_del_dueno_queda_marcada(ranking_esperado):
    c = cartera_por_regla(ranking_esperado, 10, ETAPAS_C4, anadir_dueno=["C03", "C01"])
    sel = {s["id"]: s for s in c["seleccion"]}
    assert [s["id"] for s in c["seleccion"]] == ESPERADA + ["C03", "C01"]
    assert sel["C03"]["origen"] == sel["C01"]["origen"] == "dueno"
    c2 = cartera_por_regla(ranking_esperado, 10, ETAPAS_C4, quitar_dueno=["C33"])
    assert "C33" not in [s["id"] for s in c2["seleccion"]]
    assert next(a for a in c2["archivo"] if a["id"] == "C33")["origen"] == "dueno"


# --- Prueba 3: fusión ----------------------------------------------------------------
def test_3_fusion(grupos, exploradores):
    f = comprobar_fusion(grupos, exploradores)
    assert f.valido, f.errores()
    assert f.opciones == 67 and f.grupos == 41
    assert f.opciones_por_explorador == {"E1": 24, "E2": 25, "E3": 18}
    assert f.nuevos == 33
    assert all(0.27 <= j <= 0.33 for j in f.jaccard.values()), f.jaccard


def test_3b_fusion_detecta_errores(grupos, exploradores):
    import copy
    G = copy.deepcopy(grupos)
    G["C01"]["members"].append("E1:O3")        # repetida (ya está en C04)
    G["C02"]["members"].remove("E2:O11")       # sin asignar
    G["C05"]["name"] = ""                      # código sin nombre (lección 13)
    f = comprobar_fusion(G, exploradores)
    assert not f.valido
    assert f.repetidas == ["E1:O3"] and f.sin_asignar == ["E2:O11"] and f.sin_nombre == ["C05"]


def test_esquemas_aceptan_fixtures():
    for nombre, archivos in [("explorer", ["E1", "E2", "E3"]), ("screener", ["S1", "S2", "S3"]),
                             ("attacker", ["atacante_c4"]), ("cross-verdict", ["V1", "V2"])]:
        for a in archivos:
            datos = json.loads((CASO / f"{a}.json").read_text(encoding="utf-8"))
            assert esquemas.errores(nombre, datos) == [], a


# --- Prueba 6: modo manual de punta a punta (criba y agregación) -----------------------
@pytest.fixture
def run_en_criba(tmp_path, grupos, exploradores):
    run = Ejecucion.crear(tmp_path, "Caso libanés ciclo 4")
    run.escribir("ficha.json", {
        "objetivo": "Preserve spoken Lebanese cultural heritage.",
        "destinatarios": "Non-literate, low-income, rural, older people, diaspora, future generations.",
        "criterios_criba": {"impact": "", "feasibility": "", "evidence": "", "safety": "", "inclusion": ""},
        "criterios_prioritarios": ["impact", "inclusion"],
        "etapas": ETAPAS_C4,
        "cartera_n": 10,
    })
    for e, salida in exploradores.items():
        run.escribir(f"faseA/{e}.json", salida)
    run.ir_a("fusion")
    informe = pasos.registrar_fusion(run, grupos)
    assert informe["valido"]
    run.avanzar()
    return run


def test_6_modo_manual_criba_y_agregacion(run_en_criba, ranking_esperado):
    run = run_en_criba
    assert run.fase_actual == "criba"
    fichas = pasos.preparar_criba(run)
    assert set(fichas) == {"S1", "S2", "S3"}
    for ficha in fichas.values():
        assert "You are one of three independent screeners" in ficha
        assert ficha.split("## Case inputs")[1].count('"id": "C') == 41
        assert "E1:" not in ficha and "E2:O" not in ficha   # criba ciega
    assert (run.carpeta / "prompts" / "criba" / "S1.md").exists()

    for s in ("S1", "S2", "S3"):
        pegado = "Here is my assessment:\n```json\n" + (CASO / f"{s}.json").read_text(encoding="utf-8") + "\n```\nThanks."
        res = manual.recibir_respuesta(run, "criba", s, pegado)
        assert res.ok, res.errores
    assert manual.paso_completo(run, "criba")
    assert (run.carpeta / "respuestas" / "criba" / "S2_intento1.txt").exists()
    run.avanzar()

    metricas = pasos.agregar_criba(run)
    assert metricas["votos_fatales"] == 0 and metricas["opciones_nuevas_propuestas"] == 9
    assert run.leer("ranking.json") == ranking_esperado
    run.avanzar()

    cartera = pasos.proponer_cartera(run)
    assert [s["id"] for s in cartera["seleccion"]] == ESPERADA
    with pytest.raises(PuertaCerrada):
        run.avanzar()                       # ⛔ sin aprobación del dueño
    assert run.espera_dueno()

    cartera = pasos.decidir_cartera(run, anadir=["C03", "C01"], motivo="Rescate urgente de cintas")
    assert [s["origen"] for s in cartera["seleccion"]][-2:] == ["dueno", "dueno"]
    run.aprobar("Cartera confirmada")
    assert run.avanzar() == "fase_b"

    # Reanudable: se vuelve a abrir desde disco con el mismo estado.
    otra = Ejecucion.abrir(run.carpeta)
    assert otra.fase_actual == "fase_b"
    assert [d["tipo"] for d in otra.decisiones("cartera")] == ["anadir", "aprobacion"]
    assert all("fecha" in d for d in otra.decisiones())
    assert set(otra.leer("metricas.json")) == {"fusion", "agregacion", "cartera"}


def test_6b_respuesta_invalida_pide_reintento_una_vez(run_en_criba):
    run = run_en_criba
    pasos.preparar_criba(run)
    r1 = manual.recibir_respuesta(run, "criba", "S1", "Sorry, I cannot produce JSON now.")
    assert not r1.ok and r1.ficha_reintento and "ONLY the JSON" in r1.ficha_reintento
    r2 = manual.recibir_respuesta(run, "criba", "S1", '{"assessments": [{"id": "C01", "fatal": false, "scores": {"impact": 9}}]}')
    assert not r2.ok and r2.agotado
    assert any("impact" in e for e in r2.errores)
