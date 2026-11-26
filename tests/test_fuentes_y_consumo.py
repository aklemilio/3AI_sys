"""Comprobación de fuentes dentro del flujo y registro de tiempo y consumo (SSB-106).

Sin red: ``descargar`` se sustituye por páginas falsas que contienen los
fragmentos del Explorador 1 del caso real; el resto de URL falla.
"""

import json

from conftest import cargar
from test_orquestacion import _hasta_linea_base, entorno  # noqa: F401  (fixture)
from tresia.calculo import fuentes as F
from tresia.motor import consumo, fase_b, pasos
from tresia.motor.flujo import avanzar


def _paginas_de(salida):
    paginas = {}
    for f in F.fuentes_de(salida):
        if f["url"].startswith("http") and f["fragmento"]:
            paginas.setdefault(f["url"], []).append(f["fragmento"])
    return paginas


def test_cada_url_se_descarga_una_vez_y_las_inaccesibles_se_reintentan():
    registro = {}
    F.registrar(registro, [{"url": "https://a.org", "fragmento": "uno"}, {"url": "https://a.org", "fragmento": "dos"},
                           {"url": "https://b.org", "fragmento": "tres"}], "faseA:E1")
    pedidas = []

    def sin_b(url):
        pedidas.append(url)
        if "b.org" in url:
            raise OSError("caída")
        return "text/html", "<p>uno y dos</p>"

    assert F.comprobar_pendientes(registro, sin_b) == {F.VERIFICADA: 2, F.INACCESIBLE: 1}
    assert sorted(pedidas) == ["https://a.org", "https://b.org"]
    pedidas.clear()
    assert F.comprobar_pendientes(registro, lambda u: (pedidas.append(u), ("text/html", "tres"))[1]) == {F.VERIFICADA: 1}
    assert pedidas == ["https://b.org"]          # las verificadas no se vuelven a descargar


def test_flujo_comprueba_fuentes_y_mide_consumo(entorno, monkeypatch):  # noqa: F811
    run, recursos, _, _ = entorno
    paginas = _paginas_de(cargar("E1.json"))
    assert paginas, "el Explorador 1 del caso real cita fuentes con fragmento"

    def descargar(url):
        if url in paginas:
            return "text/html", "<html><body>" + " ... ".join(paginas[url]) + "</body></html>"
        raise OSError("sin red en las pruebas")

    monkeypatch.setattr(F, "descargar", descargar)
    _hasta_linea_base(run)
    avanzar(run, recursos)

    # Fase A: el motor comprobó las fuentes y lo cuenta en las métricas.
    m = run.leer("metricas.json")["fase_a"]
    assert m["fuentes_verificadas"] >= len(paginas) and m["fuentes_no_verificadas"] > 0
    assert any("no se pudieron verificar" in a for a in run.leer("faseA/verificacion.json")["avisos"])
    # Los cribadores ven qué fuentes comprobó el motor.
    criba = run.leer("prompts/criba/S1.md")
    assert "sources_checked_by_engine" in criba and "verified (fragment found on the page)" in criba

    pasos.decidir_cartera(run, anadir=["C03"], motivo="x")
    run.aprobar("Cartera")
    avanzar(run, recursos)
    # El atacante recibe el resultado de la comprobación de las fuentes de la versión.
    ataque = run.leer("prompts/b1_ataque/atacante.md")
    assert "source_checks_by_engine" in ataque

    # El verificador falso dio «weak» a una fuente sin URL: el motor la rebaja.
    (c,) = run.leer("faseB/ciclo_1/verificador_claims_v1.json")["claims"]
    assert c["strength"] == "unsupported" and c["model_strength"] == "weak" and "Engine check: no URL given" in c["note"]

    fase_b.decidir_tarjetas(run, usar_por_defecto=True)
    avanzar(run, recursos)
    fase_b.decidir_cierre_ciclo(run, "adoptar")
    avanzar(run, recursos)

    lineas = consumo.llamadas(run)
    assert {l["paso"] for l in lineas} >= {"fase_a", "fusion", "criba", "b1_constructor", "b1_ataque"}
    assert all(l["ok"] and l["segundos"] >= 0 and l["caracteres_enviados"] > 0 for l in lineas)
    resumen = {r["fase"]: r for r in consumo.resumen_por_fase(run)}
    assert resumen["Fase A"]["llamadas"] == 3 and "Fase B, ciclo 1" in resumen
    informe = run.leer("informe.md")
    assert "## Tiempo y consumo por fase" in informe and "| Fase A | 3 | 0 |" in informe
    assert "Fuentes citadas que no se pudieron verificar" in informe and "Explorador" in informe


def test_la_solidez_de_una_fuente_la_decide_la_comprobacion(tmp_path, monkeypatch):
    from tresia.motor import Ejecucion
    from tresia.motor.verificador import aplicar_comprobacion_a_afirmaciones, registrar_fuentes_de_salida

    run = Ejecucion.crear(tmp_path, "x")
    claims = {"claims": [
        {"text": "a", "type": "source", "url": "https://a.org", "fragment": "uno", "strength": "strong"},
        {"text": "b", "type": "source", "url": "https://b.org", "fragment": "dos", "strength": "strong"},
        {"text": "c", "type": "reasoning", "premises": ["p"], "strength": "strong"},
    ]}
    run.escribir("claims.json", claims)
    def descargar(url):
        if url == "https://a.org":
            return "text/plain", "uno"
        raise OSError("no")

    monkeypatch.setattr(F, "descargar", descargar)
    registrar_fuentes_de_salida(run, claims, "afirmaciones:v1")
    assert aplicar_comprobacion_a_afirmaciones(run, "claims.json") == 1
    a, b, c = run.leer("claims.json")["claims"]
    assert a["strength"] == "strong" and a["engine_check"] == "verificada"
    assert b["strength"] == "unsupported" and b["model_strength"] == "strong" and "page inaccessible" in b["note"]
    assert c["strength"] == "strong" and "engine_check" not in c          # el razonamiento no se toca


def test_uso_de_cada_proveedor():
    claude = json.dumps({"result": "x", "total_cost_usd": 0.0123,
                         "usage": {"input_tokens": 10, "cache_read_input_tokens": 90, "output_tokens": 5}})
    assert consumo.extraer_uso(claude) == {"tokens_entrada": 100, "tokens_salida": 5, "coste_usd": 0.0123}
    gemini = json.dumps({"candidates": [], "usageMetadata": {"promptTokenCount": 1000, "candidatesTokenCount": 200,
                                                             "thoughtsTokenCount": 50}})
    precio = {"precio_usd_por_millon": {"entrada": 2.0, "salida": 10.0}}
    assert consumo.extraer_uso(gemini, precio) == {"tokens_entrada": 1000, "tokens_salida": 250, "coste_usd": 0.0045}
    ollama = json.dumps({"message": {}, "prompt_eval_count": 3000, "eval_count": 400})
    assert consumo.extraer_uso(ollama) == {"tokens_entrada": 3000, "tokens_salida": 400}
    assert consumo.extraer_uso("texto plano de codex") == {}


def test_una_llamada_fallida_tambien_se_registra(tmp_path):
    from tresia.adaptadores.base import Adaptador, AdaptadorError
    from tresia.motor import Ejecucion

    class Cae(Adaptador):
        def _llamar(self, prompt):
            raise AdaptadorError("tiempo agotado")

    run = Ejecucion.crear(tmp_path, "x")
    try:
        consumo.llamar(run, "fase_a", "E1", Cae({}), "hola")
    except AdaptadorError:
        pass
    (l,) = consumo.llamadas(run)
    assert not l["ok"] and "tiempo agotado" in l["error"] and l["paso"] == "fase_a"
    assert consumo.resumen_por_fase(run)[0]["fallidas"] == 1
