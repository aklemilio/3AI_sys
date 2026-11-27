"""Hito 3: adaptadores y llamadas, sin llamar a ningún modelo real.

Las CLI se sustituyen por ``tests/falsos/cli_falso.py`` y Gemini/Ollama por un
servidor HTTP local en 127.0.0.1.
"""

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from tresia import adaptadores, perfiles
from tresia.adaptadores import AdaptadorError
from tresia.motor import Ejecucion, manual
from tresia.motor.llamadas import ejecutar_en_paralelo, elegir_verificador, rotacion

FALSO = str(Path(__file__).parent / "falsos" / "cli_falso.py")
VALIDO = {"assessments": [{"id": "C01", "fatal": False, "scores": {"impact": 4}}]}


def cli(modo, salida="texto", tiempo=30, extra=()):
    return adaptadores.crear({"tipo": "cli", "proveedor": "falso", "ejecutable": sys.executable,
                              "argumentos": ["-I", FALSO, modo, *extra], "salida": salida, "tiempo_maximo": tiempo})


# --- rotación -------------------------------------------------------------------------
def test_rotacion_cuadrado_latino():
    assert rotacion(1) == {"constructor": "A", "atacante": "B", "evaluadores": ["B", "C"]}
    assert rotacion(2) == {"constructor": "B", "atacante": "C", "evaluadores": ["C", "A"]}
    assert rotacion(3) == {"constructor": "C", "atacante": "A", "evaluadores": ["A", "B"]}
    for c in range(1, 7):
        r = rotacion(c)
        assert r["constructor"] not in r["evaluadores"]


# --- CLI --------------------------------------------------------------------------------
def test_cli_claude_json():
    r = cli("eco_json", "claude_json").llamar("hola")
    assert json.loads(r.texto.strip("`json\n")) == VALIDO


def test_cli_archivo_de_salida():
    r = cli("archivo", "archivo", extra=["{archivo_salida}"]).llamar("hola")
    assert json.loads(r.texto) == VALIDO


def test_cli_prompt_largo_por_stdin_en_utf8():
    prompt = "Líbano — «zajal» عربي " * 20000   # ~500 000 caracteres: imposible como argumento en Windows
    assert cli("eco_prompt").llamar(prompt).texto == prompt


def test_cli_tiempo_agotado_y_error():
    with pytest.raises(AdaptadorError, match="no respondió"):
        cli("dormir", tiempo=2).llamar("x")
    with pytest.raises(AdaptadorError, match="código 3"):
        cli("falla").llamar("x")


def test_cli_no_instalada():
    a = adaptadores.crear({"tipo": "cli", "ejecutable": "no-existe-tresia-xyz"})
    ok, motivo = a.disponible()
    assert not ok and "No se encuentra" in motivo
    with pytest.raises(AdaptadorError):
        a.llamar("x")


# --- HTTP falso (Gemini y Ollama) --------------------------------------------------------------
class _Manejador(BaseHTTPRequestHandler):
    recibido: list = []
    solo_razonamiento = False

    def log_message(self, *a):
        pass

    def _responder(self, datos, codigo=200):
        cuerpo = json.dumps(datos).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_GET(self):
        if self.path == "/api/tags":
            self._responder({"models": [{"name": "qwen-prueba:latest"}]})

    def do_POST(self):
        cuerpo = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        _Manejador.recibido.append({"path": self.path, "headers": dict(self.headers), "body": cuerpo})
        if self.path.endswith(":generateContent"):
            if self.headers.get("x-goog-api-key") != "clave-de-prueba":
                return self._responder({"error": {"message": "API key not valid"}}, 400)
            return self._responder({"candidates": [{"content": {"parts": [{"text": json.dumps(VALIDO)}]}}]})
        if self.path == "/api/chat":
            texto = cuerpo["messages"][0]["content"]
            # «RECORTAR» simula que Ollama truncó la entrada al contexto fijo de 8192.
            evaluados = 8192 if "RECORTAR" in texto else len(texto) // 4 + 1
            if _Manejador.solo_razonamiento:
                return self._responder({"message": {"role": "assistant", "content": "", "thinking": "Let me think..."},
                                        "prompt_eval_count": evaluados, "done_reason": "length"})
            return self._responder({"message": {"role": "assistant", "content": json.dumps(VALIDO)},
                                    "prompt_eval_count": evaluados, "done_reason": "stop"})


@pytest.fixture(scope="module")
def servidor():
    s = HTTPServer(("127.0.0.1", 0), _Manejador)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}"
    s.shutdown()


def test_gemini_clave_en_cabecera_no_en_url(servidor, monkeypatch):
    monkeypatch.setenv("TRESIA_CLAVE_PRUEBA", "clave-de-prueba")
    g = adaptadores.crear({"tipo": "gemini", "proveedor": "gemini", "modelo": "gemini-prueba",
                           "clave_env": "TRESIA_CLAVE_PRUEBA", "url_base": servidor})
    r = g.llamar("hola")
    assert json.loads(r.texto) == VALIDO
    ultima = _Manejador.recibido[-1]
    assert "clave-de-prueba" not in ultima["path"] and "clave-de-prueba" not in r.bruto


def test_gemini_sin_clave_o_clave_mala(servidor, monkeypatch):
    monkeypatch.delenv("TRESIA_CLAVE_PRUEBA", raising=False)
    g = adaptadores.crear({"tipo": "gemini", "modelo": "m", "clave_env": "TRESIA_CLAVE_PRUEBA", "url_base": servidor})
    assert not g.disponible()[0]
    monkeypatch.setenv("TRESIA_CLAVE_PRUEBA", "otra")
    with pytest.raises(AdaptadorError, match="HTTP 400"):
        g.llamar("x")


def _ollama(servidor, **extra):
    return adaptadores.crear({"tipo": "ollama", "proveedor": "ollama", "modelo": "qwen-prueba",
                              "url_base": servidor, "habilitado": True, **extra})


def test_ollama(servidor):
    o = _ollama(servidor, num_predict=1500)
    assert o.disponible() == (True, "")
    assert json.loads(o.llamar("hola").texto) == VALIDO
    cuerpo = _Manejador.recibido[-1]["body"]
    assert cuerpo["format"] == "json" and cuerpo["stream"] is False
    # El servidor fija el contexto: no se manda num_ctx ni keep_alive.
    assert cuerpo["options"] == {"num_predict": 1500} and "keep_alive" not in cuerpo
    # qwen3.x gasta num_predict razonando: por defecto no se le deja (corrida del 26 nov).
    assert cuerpo["think"] is False
    _ollama(servidor, pensar=True).llamar("hola")
    assert _Manejador.recibido[-1]["body"]["think"] is True


def test_ollama_solo_razonamiento_se_explica(servidor):
    o = _ollama(servidor)
    _Manejador.solo_razonamiento = True
    try:
        with pytest.raises(AdaptadorError, match="razonamiento agotó num_predict"):
            o.llamar("hola")
    finally:
        _Manejador.solo_razonamiento = False


def test_ollama_no_envia_lo_que_no_cabe_y_detecta_recorte(servidor):
    o = _ollama(servidor)
    assert o.max_prompt == 8192 - 2000 - 200
    largo = "palabra " * 4000        # ≈10 700 tokens estimados
    assert not o.cabe(largo)[0]
    n = len(_Manejador.recibido)
    with pytest.raises(AdaptadorError, match="no cabe"):
        o.llamar(largo)
    assert len(_Manejador.recibido) == n          # ni siquiera se envió
    with pytest.raises(AdaptadorError, match="recortó"):
        o.llamar("RECORTAR " + "x" * 100)


# --- verificador con respaldo ---------------------------------------------------------------
def _perfil(servidor, habilitado, respaldo_modelo="gemini-respaldo"):
    return {
        "modelos": {"A": {"proveedor": "claude", "tipo": "cli", "ejecutable": "claude"},
                    "C": {"proveedor": "gemini", "tipo": "gemini", "modelo": "gemini-rotacion"}},
        "verificador": {"proveedor": "ollama", "tipo": "ollama", "modelo": "qwen-prueba", "url_base": servidor, "habilitado": habilitado},
        "verificador_respaldo": {"proveedor": "gemini", "tipo": "gemini", "modelo": respaldo_modelo,
                                 "clave_env": "TRESIA_CLAVE_PRUEBA", "url_base": servidor},
    }


def test_verificador_principal_respaldo_y_manual(tmp_path, servidor, monkeypatch):
    monkeypatch.setenv("TRESIA_CLAVE_PRUEBA", "clave-de-prueba")
    run = Ejecucion.crear(tmp_path, "Verificador")

    a, etiqueta = elegir_verificador(run, _perfil(servidor, habilitado=True))
    assert etiqueta == "ollama:qwen-prueba" and not run.estado.get("avisos")

    a, etiqueta = elegir_verificador(run, _perfil(servidor, habilitado=False))
    assert etiqueta == "gemini:gemini-respaldo"
    assert "respaldo" in run.estado["avisos"][-1]["texto"]

    a, motivo = elegir_verificador(run, _perfil(servidor, habilitado=False, respaldo_modelo="gemini-rotacion"))
    assert a is None and "modo manual" in motivo
    assert "rotación" in run.estado["avisos"][-1]["texto"]


def test_verificador_pasa_al_respaldo_si_el_servidor_recorta_o_no_cabe(tmp_path, servidor, monkeypatch):
    from tresia.motor.llamadas import tarea_verificador
    monkeypatch.setenv("TRESIA_CLAVE_PRUEBA", "clave-de-prueba")
    perfil = _perfil(servidor, habilitado=True)

    # 1. El servidor recorta en silencio: se detecta, se descarta y responde el respaldo.
    run = Ejecucion.crear(tmp_path, "Recorte")
    r = tarea_verificador(run, perfil, "premises", {"text": "RECORTAR"}, "premisas.json")
    assert r.ok, r.errores
    assert run.estado["identidades"]["verificador_premises:V"] == "gemini:gemini-respaldo"
    assert any("recortó" in a["texto"] for a in run.estado["avisos"])

    # 2. La ficha no cabe en 8192: ni se intenta en el servidor.
    run2 = Ejecucion.crear(tmp_path, "Grande")
    n = len([x for x in _Manejador.recibido if x["path"] == "/api/chat"])
    r2 = tarea_verificador(run2, perfil, "premises", {"text": "palabra " * 4000}, "premisas.json")
    assert r2.ok and run2.estado["identidades"]["verificador_premises:V"] == "gemini:gemini-respaldo"
    assert len([x for x in _Manejador.recibido if x["path"] == "/api/chat"]) == n
    assert any("no cabe" in a["texto"] for a in run2.estado["avisos"])


def test_perfil_pc_no_contiene_direcciones_ni_claves():
    p = perfiles.cargar("pc", Path(__file__).resolve().parent.parent / "perfiles")
    assert p["verificador"]["url_base"] == "" or Path(Path(__file__).parent.parent / "perfiles" / "pc.local.toml").exists()
    texto = (Path(__file__).resolve().parent.parent / "perfiles" / "pc.toml").read_text(encoding="utf-8")
    assert "AIza" not in texto and "http://" not in texto


def test_tarea_del_verificador_sin_verificador_queda_en_manual(tmp_path, servidor, monkeypatch):
    from tresia.motor.llamadas import tarea_verificador
    monkeypatch.delenv("TRESIA_CLAVE_PRUEBA", raising=False)
    run = Ejecucion.crear(tmp_path, "Manual")
    r = tarea_verificador(run, _perfil(servidor, habilitado=False), "merge", {"options": []}, "grupos_verificador.json")
    assert not r.ok and r.pasa_a_manual
    ficha = run.leer("prompts/verificador_merge/V.md")
    assert "Run ONLY the task «merge»" in ficha
    pegado = json.dumps({"groups": [{"id": "C01", "name": "Inventario de archivos", "members": ["E1:O1"], "matches_baseline": True}]})
    assert manual.recibir_respuesta(run, "verificador_merge", "V", pegado).ok


# --- de punta a punta: criba en paralelo con un reintento y una caída ---------------------------
def test_criba_en_paralelo_con_reintento_y_caida(tmp_path):
    run = Ejecucion.crear(tmp_path, "Paralelo")
    fichas = {s: manual.preparar_ficha(run, "criba", s, "screener", {"options": []}, f"criba/{s}.json")
              for s in ("S1", "S2", "S3")}
    resultados = ejecutar_en_paralelo(run, "criba", {
        "S1": (cli("eco_json", "claude_json"), "A"),
        "S2": (cli("invalido"), "B"),
        "S3": (cli("falla"), "C"),
    }, fichas)
    por = {r.ranura: r for r in resultados}
    assert por["S1"].ok and por["S2"].ok
    assert not por["S3"].ok and por["S3"].pasa_a_manual
    assert run.existe("criba/S1.json") and run.existe("criba/S2.json") and not run.existe("criba/S3.json")
    assert run.existe("prompts/criba/S2_reintento1.md")
    assert run.estado["identidades"] == {"criba:S1": "A", "criba:S2": "B", "criba:S3": "C"}
    assert any("S3" in a["texto"] for a in run.estado["avisos"])
    # La ranura caída se completa pegando a mano.
    assert manual.recibir_respuesta(run, "criba", "S3", json.dumps(VALIDO)).ok
    assert manual.paso_completo(run, "criba")
