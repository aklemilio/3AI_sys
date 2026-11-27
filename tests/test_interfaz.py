"""Interfaz local (hito 4, SSB-105): el caso libanés de punta a punta por HTTP.

Los modelos son los mismos falsos de test_orquestacion. Se comprueba que la
interfaz llega a cada puerta del dueño, que sus tarjetas deciden con el motor,
que el modo manual funciona y que nunca se muestra la identidad de los modelos.
"""

import http.client
import json
import re
import threading
import urllib.parse

import pytest

from conftest import ETAPAS_C4
from test_orquestacion import ModeloFalso, VerificadorFalso, grupos_formato_verificador, leer
from tresia.interfaz import vistas
from tresia.interfaz.servidor import Aplicacion, crear_servidor
from tresia.motor import Ejecucion
from tresia.motor.llamadas import Recursos

SECRETO = "claude-modelo-secreto"


class RefFresca:
    """Los modelos falsos leen la asignación ciega del disco: el servidor usa sus propios objetos."""
    carpeta = None

    def __getitem__(self, i):
        return Ejecucion.abrir(self.carpeta)


class Cliente:
    def __init__(self, app):
        self.app, self.paginas = app, []

    def _pedir(self, metodo, ruta, cuerpo=None, cabeceras=None):
        c = http.client.HTTPConnection("127.0.0.1", self.app.puerto, timeout=30)
        cab = {"Host": f"127.0.0.1:{self.app.puerto}", **(cabeceras or {})}
        if cuerpo is not None:
            cab["Content-Type"] = "application/x-www-form-urlencoded"
        c.request(metodo, ruta, body=cuerpo, headers=cab)
        r = c.getresponse()
        texto = r.read().decode("utf-8")
        c.close()
        if r.status == 200 and "text/html" in (r.getheader("Content-Type") or ""):
            self.paginas.append(texto)
        return r.status, texto, r.getheader("Location")

    def get(self, ruta, **kw):
        return self._pedir("GET", ruta, **kw)

    def post(self, ruta, datos=(), token=True, **kw):
        pares = list(datos.items() if isinstance(datos, dict) else datos)
        if token:
            pares.append(("_t", self.app.token))
        return self._pedir("POST", ruta, urllib.parse.urlencode(pares), **kw)


@pytest.fixture
def entorno(tmp_path):
    ref = RefFresca()
    modelos = {l: ModeloFalso(l, ref) for l in "ABC"}
    verificador = VerificadorFalso()
    recursos = Recursos(modelos=modelos, verificadores=lambda run, ficha: [(verificador, "verificador-falso")])
    app = Aplicacion(tmp_path / "ejecuciones", perfil={"modelos": {"A": {"proveedor": "claude", "ejecutable": "claude"}}},
                     recursos=recursos)
    servidor = crear_servidor(app, 0)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    yield app, Cliente(app), ref
    servidor.shutdown()
    servidor.server_close()


def crear(app, cliente, ref, modo="automatico"):
    estado, _, destino = cliente.post("/nueva", {"nombre": "Caso libanés por la interfaz", "modo": modo})
    assert estado == 303 and destino.startswith("/e/")
    ident = destino.removeprefix("/e/")
    ref.carpeta = app.base / ident
    esperar(app, ident)
    return ident


def esperar(app, ident):
    app.trabajos.esperar(app.base / ident, 60)


def accion(app, cliente, ident, nombre, datos=()):
    estado, _, destino = cliente.post(f"/e/{ident}/accion/{nombre}", datos)
    assert estado == 303 and destino == f"/e/{ident}", (estado, destino)
    esperar(app, ident)
    _, pagina, _ = cliente.get(f"/e/{ident}")
    assert "mensaje error" not in pagina, re.findall(r'mensaje error"[^>]*>([^<]+)', pagina)
    return pagina


def hasta_linea_base(app, cliente, ident):
    _, pagina, _ = cliente.get(f"/e/{ident}")
    assert "Materiales del caso" in pagina
    accion(app, cliente, ident, "material", {"nombre": "Objetivo de conservación", "etiqueta": "objeto",
                                             "texto": "Preserve the spoken Lebanese cultural and linguistic heritage."})
    accion(app, cliente, ident, "material", {"nombre": "Notas internas", "etiqueta": "contexto", "texto": "SECRETO"})
    pagina = accion(app, cliente, ident, "cerrar_ingesta")
    assert "Encuadre: once preguntas" in pagina
    pagina = accion(app, cliente, ident, "encuadre", {
        "objetivo": "Preserve the spoken Lebanese cultural and linguistic heritage at risk of being lost.",
        "destinatarios": "People who do not read or write, rural, older people, the diaspora.",
        "caras": "Lebanese law as written\nReal market practice",
        "etapas": "\n".join(ETAPAS_C4), "limite_cuerpo": "1600", "limite_anexo": "800"})
    assert "¿Confirmas la ficha del caso?" in pagina and "por defecto" in pagina
    pagina = accion(app, cliente, ident, "confirmar_ficha")
    assert "Línea base: las opciones obvias" in pagina
    G = json.loads(leer("grupos_c4.json"))
    return accion(app, cliente, ident, "linea_base", {"opciones": "\n".join(v["name"] for v in G.values() if v["baseline"])})


# --- seguridad --------------------------------------------------------------------------------------
def test_rechaza_otro_host_otro_origen_y_formularios_sin_codigo(entorno):
    app, cliente, _ = entorno
    assert cliente.get("/", cabeceras={"Host": "evil.example"})[0] == 403
    assert cliente.post("/nueva", {"nombre": "x"}, cabeceras={"Origin": "https://evil.example"})[0] == 403
    assert cliente.post("/nueva", {"nombre": "x"}, token=False)[0] == 403
    assert cliente.post("/nueva", [("nombre", "x"), ("_t", "otro")], token=False)[0] == 403
    assert not list(app.base.iterdir())
    assert cliente.get("/e/..%2F..%2Fwindows")[0] == 404
    assert cliente.get("/estatico/..%2Fservidor.py")[0] == 404


def test_cabeceras_de_seguridad(entorno):
    app, _, _ = entorno
    c = http.client.HTTPConnection("127.0.0.1", app.puerto)
    c.request("GET", "/", headers={"Host": f"127.0.0.1:{app.puerto}"})
    r = c.getresponse()
    assert "script-src 'self'" in r.getheader("Content-Security-Policy")
    assert r.getheader("X-Frame-Options") == "DENY"
    # Con «no-referrer» el navegador manda «Origin: null» en los formularios y se rechazarían.
    assert r.getheader("Referrer-Policy") == "same-origin"


def test_formulario_con_el_origen_que_manda_el_navegador(entorno):
    app, cliente, _ = entorno
    origen = f"http://127.0.0.1:{app.puerto}"
    estado, _, destino = cliente.post("/nueva", {"nombre": "Desde el navegador", "modo": "manual"},
                                      cabeceras={"Origin": origen})
    assert estado == 303 and destino.startswith("/e/")
    app.trabajos.esperar(app.base / destino.removeprefix("/e/"), 30)
    assert cliente.post("/nueva", {"nombre": "x"}, cabeceras={"Origin": "null"})[0] == 403


# --- recorrido completo -------------------------------------------------------------------------------
def test_recorrido_completo_por_la_interfaz(entorno):
    app, cliente, ref = entorno
    ident = crear(app, cliente, ref)
    assert "Caso libanés por la interfaz" in cliente.get("/")[1]
    pagina = hasta_linea_base(app, cliente, ident)

    # Fase A → … → cartera, solo con los modelos.
    assert "¿Apruebas la cartera?" in pagina
    # Cada opción de la cartera lleva su explicación en un globo (descripción del explorador).
    assert 'class="explicable"' in pagina and 'role="tooltip"' in pagina
    run = Ejecucion.abrir(app.base / ident)
    gid = run.leer("cartera.json")["seleccion"][0]["id"]
    assert f'id="exp-{gid}"' in pagina
    _, res, _ = cliente.get(f"/e/{ident}/resultados")
    assert "Grabar oficios, trabajo y vida cotidiana en contexto" in res and "Desacuerdo en: Seguridad" in res
    assert "Explorador 1" in res or "Explorador 2" in res

    pagina = accion(app, cliente, ident, "cartera_cambiar", [("anadir", "C03"), ("anadir", "C01"),
                                                              ("motivo", "Rescate urgente de cintas")])
    assert "Decisión tuya" in pagina
    pagina = accion(app, cliente, ident, "cartera_aprobar")

    # Fase B: tarjetas del árbitro.
    assert "Hallazgos del atacante (ciclo 1)" in pagina and "Si no respondes: apply" in pagina
    pagina = accion(app, cliente, ident, "disposiciones", {"d_A1": "reject", "n_A1": "Fuera de alcance"})
    assert "¿adoptas la versión v1.1?" in pagina and "Evaluador 1" in pagina
    run = Ejecucion.abrir(app.base / ident)
    disp = run.leer("faseB/ciclo_1/disposiciones.json")
    assert disp["A1"] == {"opcion": "reject", "nota": "Fuera de alcance", "origen": "dueno"}
    assert disp["A2"]["origen"] == "por_defecto"

    _, prop, _ = cliente.get(f"/e/{ident}/propuesta")
    assert "Law 75/1999" in prop and "Fuente con fragmento" in prop

    pagina = accion(app, cliente, ident, "cierre", {"accion": "adoptar", "motivo": "Suficiente para el piloto"})
    assert "¿Apruebas el informe?" in pagina
    pagina = accion(app, cliente, ident, "aprobar_informe")
    assert "Ejecución terminada" in pagina

    _, reg, _ = cliente.get(f"/e/{ident}/decisiones")
    assert "Rescate urgente de cintas" in reg and "Fuera de alcance" in reg
    assert "Terminada" in cliente.get("/")[1]
    for vista in ("resultados", "propuesta", "informe", "decisiones"):
        assert cliente.get(f"/e/{ident}/{vista}")[0] == 200

    # Nunca se muestra la identidad de los modelos (ni el contexto, que no sale de su tarjeta de ingesta).
    run = Ejecucion.abrir(app.base / ident)
    run.estado["identidades"]["fase_a:E1"] = SECRETO
    run.estado.setdefault("avisos", []).append({"fecha": "2026-11-26T10:00:00", "texto":
                                                f"fase_a E1: el modelo no respondió (No se encuentra {SECRETO})."})
    run.guardar()
    _, pagina, _ = cliente.get(f"/e/{ident}")
    assert "Explorador 1: el modelo no respondió" in pagina
    for html in cliente.paginas + [pagina]:
        assert SECRETO not in html and "verificador-falso" not in html
        assert not re.search(r"(?i)\bclaude\b", html)


def test_una_decision_vieja_no_decide_otra_puerta(entorno):
    app, cliente, ref = entorno
    ident = crear(app, cliente, ref)
    estado, _, _ = cliente.post(f"/e/{ident}/accion/cartera_aprobar")
    esperar(app, ident)
    _, pagina, _ = cliente.get(f"/e/{ident}")
    assert estado == 303 and "ya no corresponde a la fase actual" in pagina
    assert Ejecucion.abrir(app.base / ident).fase_actual == "ingesta"


def test_errores_del_dueno_se_explican(entorno):
    app, cliente, ref = entorno
    ident = crear(app, cliente, ref)
    cliente.post(f"/e/{ident}/accion/cerrar_ingesta")
    _, pagina, _ = cliente.get(f"/e/{ident}")
    assert "Falta al menos un material marcado como «objeto»" in pagina


# --- modo manual --------------------------------------------------------------------------------------
def test_modo_manual_copiar_y_pegar(entorno):
    app, cliente, ref = entorno
    ident = crear(app, cliente, ref, modo="manual")
    hasta_linea_base(app, cliente, ident)
    _, pagina, _ = cliente.get(f"/e/{ident}")
    for n in (1, 2, 3):
        assert f"Explorador {n}</a>" in pagina

    _, manual, _ = cliente.get(f"/e/{ident}/manual/fase_a/E1")
    assert "You are one of three independent explorers" in manual and "Copiar la ficha" in manual
    assert "SECRETO" not in manual                                  # el contexto nunca llega a la ficha

    # Respuesta mala: se explica y se ofrece el mensaje de reintento para copiar.
    estado, _, destino = cliente.post(f"/e/{ident}/manual/fase_a/E1", {"respuesta": "no es JSON"})
    assert estado == 303 and destino.endswith("/manual/fase_a/E1")
    _, manual, _ = cliente.get(destino)
    assert "La respuesta no es válida" in manual and "Pídele al modelo que corrija la respuesta" in manual

    for r in ("E1", "E2", "E3"):
        estado, _, destino = cliente.post(f"/e/{ident}/manual/fase_a/{r}", {"respuesta": leer(f"{r}.json")})
        assert destino == f"/e/{ident}", r
        esperar(app, ident)
    _, pagina, _ = cliente.get(f"/e/{ident}")
    assert "Verificador: fusión de opciones</a>" in pagina

    cliente.post(f"/e/{ident}/manual/fusion/V", {"respuesta": json.dumps(grupos_formato_verificador())})
    esperar(app, ident)
    _, pagina, _ = cliente.get(f"/e/{ident}")
    assert "Cribador 1</a>" in pagina
    assert Ejecucion.abrir(app.base / ident).fase_actual == "criba"


def test_pasar_de_manual_a_automatico(entorno):
    app, cliente, ref = entorno
    ident = crear(app, cliente, ref, modo="manual")
    hasta_linea_base(app, cliente, ident)
    cliente.post(f"/e/{ident}/modo", {"modo": "automatico"})
    esperar(app, ident)
    _, pagina, _ = cliente.get(f"/e/{ident}")
    assert "¿Apruebas la cartera?" in pagina


# --- piezas sueltas -----------------------------------------------------------------------------------
def test_markdown_escapa_y_solo_enlaza_http():
    html = vistas.md_a_html("# Título\n\n<script>alert(1)</script> **negrita** [x](javascript:alert(1)) https://ejemplo.org/a\n\n"
                            "| a | b |\n|---|---|\n| 1 | 2 |\n\n- uno\n- dos")
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert "<strong>negrita</strong>" in html and 'href="javascript' not in html
    assert '<a href="https://ejemplo.org/a"' in html and "<table>" in html and "<li>dos</li>" in html


def test_nombres_legibles_de_las_ranuras():
    assert vistas.nombre_ranura("fase_a", "E2") == "Explorador 2"
    assert vistas.nombre_ranura("criba", "S3") == "Cribador 3"
    assert vistas.nombre_ranura("b2_verificacion", "claims") == "Verificador: afirmaciones (ciclo 2)"
    assert vistas.nombre_ranura("b1_veredicto", "V2") == "Evaluador 2 (ciclo 1)"
    assert vistas.nombre_ranura("b3_constructor", "constructor") == "Constructor (ciclo 3)"


def test_ocultador_quita_nombres_de_modelos():
    o = vistas.Ocultador({"modelos": {"C": {"proveedor": "gemini", "modelo": "gemini-4-hydrogen"}}})
    texto = o("HTTP 400 de gemini-4-hydrogen: clave mala; codex y Claude no responden")
    assert "gemini" not in texto.lower() and "codex" not in texto and "claude" not in texto.lower()
