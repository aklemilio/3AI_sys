"""Pruebas de aceptación 4 y 5 de la SPEC (§11) y comprobación de fuentes sin red."""

import json

import pytest

from conftest import CASO
from tresia.calculo import fuentes as F
from tresia.calculo.recuento import elementos, palabras, recuento_por_partes, urls
from tresia.calculo.versiones import comparar, secciones, separar_registro
from tresia.motor import Ejecucion
from tresia.motor.verificador import registrar_fuentes_de_salida, verificar_version


def leer(nombre):
    return (CASO / nombre).read_text(encoding="utf-8")


PARTES_V42 = {"cuerpo": (None, "# **Annex"), "anexo": ("# **Annex", "## **G.")}


# --- Prueba 4: recuento ------------------------------------------------------------
def test_4_recuento_v42():
    r = recuento_por_partes(leer("v42.md"), PARTES_V42, {"cuerpo": 1600, "anexo": 800})
    assert r["cuerpo"]["palabras"] == 1590
    assert r["anexo"]["palabras"] == 798
    assert not r["cuerpo"]["excede"] and not r["anexo"]["excede"]
    assert "guiones" in r["metodo"]


def test_4b_metodo_de_recuento():
    assert palabras("| **Hola** | mundo |\n|---|---|\n- uno — dos `tres` # cuatro") == 7
    e = elementos("# T\n\n- a\n- b\n1. c\n\n| x | y |\n|---|---|\n| 1 | 2 |\nver https://a.org/x.")
    assert (e.encabezados, e.vinetas, e.filas_tabla, e.urls) == (1, 3, 2, 1)
    assert urls("(https://a.org/x), https://b.org/y.") == ["https://a.org/x", "https://b.org/y"]


# --- Prueba 5: comparación de versiones ---------------------------------------------
def test_5_v4_a_v41_pierde_fuentes_y_no_recorta():
    c = comparar(leer("v4_builder.txt"), leer("v41_builder.txt"))
    assert c.urls_anteriores == 8 and c.urls_nuevas == 0
    assert len(c.urls_perdidas) == 8
    assert c.registro_de_fuentes_perdido, "debe detectar que el registro de fuentes desapareció"
    assert [r["addresses"] for r in c.recortes_no_producidos] == ["A17"]
    assert not c.secciones_perdidas
    alertas = " ".join(c.alertas)
    assert "(todas)" in alertas and "Recorte declarado que no se produjo" in alertas


def test_5b_secciones_en_texto_plano_y_markdown():
    plano = [s["clave"] for s in secciones(separar_registro(leer("v4_builder.txt"))[0])]
    md = [s["clave"] for s in secciones(separar_registro(leer("v41_builder.txt"))[0])]
    for k in ["1", "7", "anexo:A", "anexo:F"]:
        assert k in plano and k in md


def test_5c_la_version_consolidada_restituye_las_fuentes():
    c = comparar(leer("v41_builder.txt"), leer("v41_consolidada.md"))
    assert c.urls_anteriores == 0 and c.urls_nuevas > 0
    assert not c.urls_perdidas


def test_5d_un_recorte_real_no_da_alerta():
    anterior = "Intro\n" + "palabra " * 1000 + "\nChange register\n" + json.dumps({"changes": []})
    nueva = "Intro\n" + "palabra " * 700 + "\nChange register\n" + json.dumps(
        {"changes": [{"section": "Body", "change": "Compress prose.", "addresses": "A1"}]})
    c = comparar(anterior, nueva)
    assert len(c.recortes_declarados) == 1 and not c.recortes_no_producidos


# --- Fuentes -----------------------------------------------------------------------------
PAGINA = """<html><head><script>var x = "no";</script></head><body>
<p>Founded in 1959 as the first public television station in the Arab world,
T&eacute;l&eacute; Liban preserves major audiovisual archives</p></body></html>"""


def falso(contenido, tipo="text/html"):
    return lambda url: (tipo, contenido)


def test_fuentes_normalizacion_y_estados():
    frag = "first public television station in the Arab world, Tele Liban preserves"
    assert F.comprobar("https://x.org", frag, falso(PAGINA))["estado"] == F.VERIFICADA
    # comillas tipográficas y rayas
    assert F.comprobar("https://x.org", "“a — b”", falso('<p>"a - b"</p>'))["estado"] == F.VERIFICADA
    assert F.comprobar("https://x.org", "not on the page", falso(PAGINA))["estado"] == F.NO_COINCIDE
    assert F.comprobar("https://x.org", "", falso(PAGINA))["estado"] == F.SIN_FRAGMENTO

    def caida(url):
        raise OSError("timeout")
    assert F.comprobar("https://x.org", "algo", caida)["estado"] == F.INACCESIBLE
    assert F.comprobar("https://x.org", "algo", falso("%PDF", "application/pdf"))["estado"] == F.INACCESIBLE
    assert F.comprobar("", "algo", falso(PAGINA))["estado"] == F.INACCESIBLE


def test_fuentes_registro_no_pierde_entradas():
    reg = {}
    F.registrar(reg, [{"url": "https://a.org", "fragmento": "x", "afirmacion": "c1"}], "v4")
    F.registrar(reg, [{"url": "https://a.org", "fragmento": "x", "afirmacion": "c2"}], "v4.1")
    assert len(reg) == 1
    (e,) = reg.values()
    assert e["citada_en"] == ["v4", "v4.1"] and e["afirmaciones"] == ["c1", "c2"]
    assert F.ausentes_en(reg, "texto sin la url") == [e]


# --- Integración en el motor --------------------------------------------------------------
def test_verificador_en_la_ejecucion(tmp_path):
    run = Ejecucion.crear(tmp_path, "Verificador")
    n = registrar_fuentes_de_salida(run, json.loads(leer("E1.json")), "faseA:E1")
    assert n > 0
    reg = run.leer("fuentes.json")
    assert all(e["estado"] != F.VERIFICADA for e in reg.values())   # nada verificado sin comprobar

    notas = verificar_version(run, 4, "v4.1", leer("v41_builder.txt"), anterior=leer("v4_builder.txt"),
                              partes={"cuerpo": (None, "# **Annex"), "anexo": ("# **Annex", "# **Change register")},
                              limites={"cuerpo": 1600, "anexo": 800})
    assert run.existe("faseB/ciclo_4/notas_verificador_v4.1.json")
    assert any("URL de fuentes" in a for a in notas["alertas"])
    assert any("restituirlas" in a for a in notas["alertas"])
    ausentes_v41 = len(notas["fuentes_ausentes"])

    notas2 = verificar_version(run, 4, "v4.1c", leer("v41_consolidada.md"), anterior=leer("v41_builder.txt"))
    assert len(notas2["fuentes_ausentes"]) < ausentes_v41


def test_verificador_comprueba_fuentes_sin_red(tmp_path):
    run = Ejecucion.crear(tmp_path, "Fuentes")
    registrar_fuentes_de_salida(run, {"support": [
        {"type": "source", "claim": "c", "url": "https://x.org/a", "fragment": "Tele Liban preserves major audiovisual archives"},
        {"type": "source", "claim": "d", "url": "https://x.org/b", "fragment": "frase inventada"},
    ]}, "faseA:E3")
    notas = verificar_version(run, 1, "v1", "Texto con https://x.org/a y https://x.org/b",
                              comprobar_fuentes=True, obtener=falso(PAGINA))
    assert notas["fuentes_por_estado"] == {F.VERIFICADA: 1, F.NO_COINCIDE: 1}
