"""Materiales «solo para la fase B» y límites de cuerpo y anexo (preparación de SSB-106)."""

import json

import pytest

from conftest import ETAPAS_C4
from test_orquestacion import entorno, leer  # noqa: F401  (fixture)
from tresia.calculo.recuento import tramo
from tresia.interfaz import tarjetas
from tresia.motor import Ejecucion, encuadre, fase_b, pasos
from tresia.motor.flujo import avanzar
from tresia.motor.verificador import verificar_version


# --- materiales solo para la fase B -----------------------------------------------------------------
def test_los_exploradores_no_ven_los_materiales_solo_para_la_fase_b(entorno):  # noqa: F811
    run, recursos, _, _ = entorno
    encuadre.ingestar(run, "Objetivo", "objeto", texto="Preserve the spoken Lebanese heritage.")
    encuadre.ingestar(run, "Estrategia v3", "objeto", texto="STRATEGY-V3-TEXT", solo_fase_b=True)
    encuadre.ingestar(run, "Notas", "contexto", texto="SECRETO", solo_fase_b=True)
    assert [m["solo_fase_b"] for m in encuadre.materiales(run, True)] == [False, True, False]
    encuadre.cerrar_ingesta(run)
    avanzar(run)
    encuadre.responder_encuadre(run, {"objetivo": "Preserve the spoken Lebanese heritage."}, {"etapas": ETAPAS_C4})
    run.aprobar()
    G = json.loads(leer("grupos_c4.json"))
    encuadre.registrar_linea_base(run, [g["name"] for g in G.values() if g["baseline"]])
    avanzar(run, recursos)

    for e in ("E1", "E2", "E3"):
        ficha = run.leer(f"prompts/fase_a/{e}.md")
        assert "STRATEGY-V3-TEXT" not in ficha and "SECRETO" not in ficha
        assert "Preserve the spoken Lebanese heritage." in ficha
    pasos.decidir_cartera(run)
    run.aprobar()
    avanzar(run, recursos)
    constructor = run.leer("prompts/b1_constructor/constructor.md")
    assert "STRATEGY-V3-TEXT" in constructor and "SECRETO" not in constructor


# --- límites por partes -----------------------------------------------------------------------------
@pytest.mark.parametrize("titulo", ["# Annex", "# **Annex**", "## Annex A–F", "#  **Annex"])
def test_la_marca_del_anexo_admite_otro_nivel_o_negrita(titulo):
    texto = f"Body words here.\n\n{titulo}\n\nAnnex words."
    assert tramo(texto, None, "# Annex").strip() == "Body words here."
    assert tramo(texto, "# Annex").startswith(titulo)


def test_marca_que_no_aparece_da_error():
    with pytest.raises(ValueError):
        tramo("Sin anexo.", "# Annex")


def test_limites_por_partes_sin_registro_de_cambios_y_con_aviso_si_falta_la_marca(tmp_path):
    run = Ejecucion.crear(tmp_path, "Límites")
    partes = {"cuerpo": (None, "# Annex"), "anexo": ("# Annex", None)}
    texto = ("uno dos tres cuatro\n\n# **Annex**\n\ncinco seis\n\nChange register\n"
             + json.dumps({"changes": [{"what": " ".join(["palabra"] * 50)}]}))
    notas = verificar_version(run, 1, "v1", texto, partes=partes, limites={"cuerpo": 3, "anexo": 10})
    assert notas["recuento"]["cuerpo"]["palabras"] == 4 and notas["recuento"]["cuerpo"]["excede"]
    assert notas["recuento"]["anexo"]["palabras"] == 3          # «Annex», cinco, seis: sin el registro
    assert any("«cuerpo» tiene 4 palabras" in a for a in notas["alertas"])

    notas = verificar_version(run, 1, "v2", "Texto sin anexo.", partes=partes, limites={"cuerpo": 3, "anexo": 10})
    assert sum("No se encontró la marca «# Annex»" in a for a in notas["alertas"]) == 2


def test_el_encuadre_con_limites_guarda_las_marcas_y_el_constructor_las_recibe(tmp_path):
    run = Ejecucion.crear(tmp_path, "Encuadre")
    tarjetas._encuadre(run, {"objetivo": "Objetivo de prueba.", "limite_cuerpo": "1600", "limite_anexo": "800"})
    ficha = run.leer("ficha.json")
    assert ficha["limites"] == {"cuerpo": 1600, "anexo": 800}
    assert ficha["partes"] == {"cuerpo": [None, "# Annex"], "anexo": ["# Annex", None]}
    assert "«# Annex»" in fase_b._marcas_de_partes(ficha)["part_markers"]

    run2 = Ejecucion.crear(tmp_path, "Solo cuerpo")
    tarjetas._encuadre(run2, {"objetivo": "Objetivo.", "limite_cuerpo": "500"})
    assert run2.leer("ficha.json")["partes"] == {"cuerpo": [None, None]}
    assert fase_b._marcas_de_partes(run2.leer("ficha.json")) == {}
