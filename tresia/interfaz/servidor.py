"""Servidor local de la interfaz (biblioteca estándar + Jinja2).

Seguridad:
- Solo escucha en 127.0.0.1 y rechaza cabeceras ``Host`` u ``Origin`` de otro sitio
  (así una web abierta en el navegador no puede hablar con la herramienta).
- Todo formulario lleva un código de control que cambia en cada arranque.
- Las plantillas escapan todo el texto de los modelos.
"""

from __future__ import annotations

import hmac
import re
import secrets
import threading
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

from tresia.interfaz import tarjetas as T
from tresia.interfaz import vistas as V
from tresia.interfaz.trabajo import Trabajos, ultimo_estado
from tresia.motor import Ejecucion, manual
from tresia.motor.ejecucion import FASES

AQUI = Path(__file__).resolve().parent
ESTATICOS = {"estilo.css": "text/css; charset=utf-8", "app.js": "text/javascript; charset=utf-8"}
_ID = re.compile(r"[\w.-]{1,120}")
MAX_CUERPO = 20 * 1024 * 1024


class Aplicacion:
    def __init__(self, base: Path, perfil: dict | None = None, recursos=None, motivo_sin_recursos: str = ""):
        self.base = Path(base)
        self.base.mkdir(parents=True, exist_ok=True)
        self.token = secrets.token_urlsafe(24)
        self.ocultar = V.Ocultador(perfil)
        self.recursos = recursos
        self.motivo_sin_recursos = motivo_sin_recursos
        self.trabajos = Trabajos(self.recursos_para)
        self.mensajes: dict[str, list[tuple[str, str]]] = {}
        self._cerrojo = threading.Lock()
        self.puerto = 0
        self.env = Environment(loader=FileSystemLoader(AQUI / "plantillas"), autoescape=select_autoescape(["html"]),
                               trim_blocks=True, lstrip_blocks=True)
        self.env.filters["md"] = lambda t: Markup(V.md_a_html(t or ""))
        self.env.filters["fase"] = lambda k: V.NOMBRE_FASE.get(k, k)
        self.env.filters["fecha"] = lambda f: (f or "")[:16].replace("T", " ")
        self.env.globals.update(etiquetas=V.ETIQUETAS, nombre_ranura=V.nombre_ranura)

    # --- recursos y estado ------------------------------------------------------------------
    def recursos_para(self, run: Ejecucion):
        return None if run.estado.get("config", {}).get("modo") == "manual" else self.recursos

    def carpeta(self, ident: str) -> Path | None:
        if not _ID.fullmatch(ident or "") or ident in (".", ".."):
            return None
        c = self.base / ident
        return c if (c / "run.json").is_file() else None

    def avisar(self, ident: str, tipo: str, texto: str) -> None:
        with self._cerrojo:
            self.mensajes.setdefault(ident, []).append((tipo, texto))

    def mensajes_de(self, ident: str) -> list[tuple[str, str]]:
        with self._cerrojo:
            return self.mensajes.pop(ident, [])

    def render(self, plantilla: str, **ctx) -> str:
        return self.env.get_template(plantilla).render(token=self.token, **ctx)

    def ejecuciones(self) -> list[dict]:
        salida = []
        for c in self.base.iterdir():
            if not (c / "run.json").is_file():
                continue
            try:
                run = Ejecucion.abrir(c)
            except (OSError, ValueError):
                continue
            ui = ultimo_estado(run)
            espera = run.espera_dueno() or (ui.get("estado") or {}).get("espera") == "dueno"
            salida.append({"id": c.name, "nombre": run.estado["nombre"], "fase": V.NOMBRE_FASE[run.fase_actual],
                           "espera_dueno": espera, "trabajando": self.trabajos.trabajando(c),
                           "respuestas": (ui.get("estado") or {}).get("espera") == "respuestas",
                           "terminada": bool((ui.get("estado") or {}).get("terminada")),
                           "actualizada": run.estado.get("actualizada", ""),
                           "modo": run.estado.get("config", {}).get("modo", "automatico")})
        return sorted(salida, key=lambda e: e["actualizada"], reverse=True)

    def pendientes(self, run: Ejecucion) -> list[dict]:
        return [{"paso": paso, "ranura": r, "nombre": V.nombre_ranura(paso, r),
                 "estado": V.ESTADO_RANURA.get(p["estado"], p["estado"])}
                for paso, ranuras in run.estado.get("pendientes", {}).items()
                for r, p in ranuras.items() if p["estado"] != "recibida"]

    def contexto_ejecucion(self, ident: str, run: Ejecucion) -> dict:
        ui = ultimo_estado(run)
        trabajando = self.trabajos.trabajando(run.carpeta)
        fases = [{"nombre": n, "estado": run.estado["fases"][k], "texto": V.ESTADO_FASE[run.estado["fases"][k]],
                  "actual": k == run.fase_actual} for k, n, _ in FASES]
        avisos = [{"fecha": a["fecha"], "texto": V.aviso_legible(a["texto"], run, self.ocultar)}
                  for a in run.estado.get("avisos", [])]
        return {"id": ident, "run": run, "nombre": run.estado["nombre"], "fases": fases,
                "fase": V.NOMBRE_FASE[run.fase_actual], "ui": ui.get("estado"), "fecha_ui": ui.get("fecha"),
                "error": self.ocultar(ui["error"], run) if ui.get("error") else None,
                "trabajando": trabajando, "tarjeta": None if trabajando else T.tarjeta(run, ui.get("estado")),
                "pendientes": self.pendientes(run), "avisos": list(reversed(avisos)),
                "metricas": V.metricas_legibles(run), "mensajes": self.mensajes_de(ident),
                "modo": run.estado.get("config", {}).get("modo", "automatico"),
                "sin_recursos": self.recursos is None, "motivo_sin_recursos": self.motivo_sin_recursos,
                "hay_resultados": run.existe("grupos.json"), "hay_propuesta": bool(run.estado.get("fase_b", {}).get("versiones")),
                "hay_informe": run.existe("informe.md")}


class Manejador(BaseHTTPRequestHandler):
    app: Aplicacion
    server_version = "tresia"
    sys_version = ""

    def log_request(self, code="-", size="-"):    # sin ruido en la consola; los errores sí se muestran
        if str(getattr(code, "value", code))[:1] in ("4", "5"):
            super().log_request(code, size)

    # --- utilidades ---------------------------------------------------------------------
    def _origen_valido(self) -> bool:
        permitidos = {f"127.0.0.1:{self.app.puerto}", f"localhost:{self.app.puerto}"}
        if self.headers.get("Host", "") not in permitidos:
            return False
        origen = self.headers.get("Origin")
        return origen is None or origen in {f"http://{h}" for h in permitidos}

    def _enviar(self, codigo: int, cuerpo: str | bytes, tipo: str = "text/html; charset=utf-8") -> None:
        datos = cuerpo.encode("utf-8") if isinstance(cuerpo, str) else cuerpo
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(datos)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy",
                         "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
                         "form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(datos)

    def _ir(self, destino: str) -> None:
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", destino)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _error(self, codigo: int, texto: str) -> None:
        self._enviar(codigo, self.app.render("error.html", codigo=codigo, texto=texto))

    def _formulario(self) -> tuple[dict, dict]:
        largo = int(self.headers.get("Content-Length") or 0)
        if largo > MAX_CUERPO:
            raise ValueError("El envío es demasiado grande.")
        crudo = self.rfile.read(largo).decode("utf-8", errors="replace")
        pares = urllib.parse.parse_qs(crudo, keep_blank_values=True)
        return {k: v[-1] for k, v in pares.items()}, pares

    # --- GET ------------------------------------------------------------------------------
    def do_GET(self):
        if not self._origen_valido():
            return self._error(403, "Solo se admiten peticiones desde esta misma herramienta.")
        ruta = urllib.parse.urlparse(self.path).path
        try:
            return self._get(ruta)
        except Exception as e:   # pragma: no cover - se muestra en pantalla
            return self._error(500, f"Error interno: {type(e).__name__}: {e}")

    def _get(self, ruta: str):
        a = self.app
        if ruta == "/":
            return self._enviar(200, a.render("ejecuciones.html", ejecuciones=a.ejecuciones(),
                                              sin_recursos=a.recursos is None, motivo_sin_recursos=a.motivo_sin_recursos))
        if m := re.fullmatch(r"/estatico/([\w.]+)", ruta):
            if m[1] not in ESTATICOS:
                return self._error(404, "No existe.")
            return self._enviar(200, (AQUI / "estatico" / m[1]).read_bytes(), ESTATICOS[m[1]])
        m = re.fullmatch(r"/e/([^/]+)(?:/(resultados|propuesta|decisiones|informe|manual/([^/]+)/([^/]+)))?/?", ruta)
        if not m or not (carpeta := a.carpeta(m[1])):
            return self._error(404, "Esa ejecución no existe.")
        ident, vista = m[1], m[2]
        run = Ejecucion.abrir(carpeta)
        comun = {"id": ident, "nombre": run.estado["nombre"]}
        if vista is None:
            return self._enviar(200, a.render("ejecucion.html", **a.contexto_ejecucion(ident, run)))
        if vista == "resultados":
            return self._enviar(200, a.render("resultados.html", **comun, r=V.resultados(run)))
        if vista == "propuesta":
            return self._enviar(200, a.render("propuesta.html", **comun, p=V.propuesta(run)))
        if vista == "informe":
            texto = run.leer("informe.md") if run.existe("informe.md") else ""
            return self._enviar(200, a.render("informe.html", **comun, html=Markup(V.md_a_html(texto))))
        if vista == "decisiones":
            decisiones = [{**d, "fase_nombre": V.NOMBRE_FASE.get(d["fase"], d["fase"]),
                           "detalle": ", ".join(f"{k}: {v}" for k, v in d.items()
                                                if k not in ("fecha", "fase", "tipo", "origen"))}
                          for d in reversed(run.decisiones())]
            return self._enviar(200, a.render("decisiones.html", **comun, decisiones=decisiones))
        paso, ranura = urllib.parse.unquote(m[3]), urllib.parse.unquote(m[4])
        pend = run.estado.get("pendientes", {}).get(paso, {}).get(ranura)
        if not pend:
            return self._error(404, "Esa ficha no existe.")
        ficha = run.leer(f"prompts/{paso}/{ranura}.md")
        reintento = None
        if pend["estado"] == "reintento":
            r = f"prompts/{paso}/{ranura}_reintento{pend['intentos']}.md"
            reintento = run.leer(r) if run.existe(r) else None
        return self._enviar(200, a.render("manual.html", **comun, paso=paso, ranura=ranura,
                                          rol=V.nombre_ranura(paso, ranura), pend=pend, ficha=ficha,
                                          estado=V.ESTADO_RANURA.get(pend["estado"], pend["estado"]),
                                          reintento=reintento, mensajes=a.mensajes_de(ident),
                                          constructor=bool(pend.get("destino_texto"))))

    # --- POST ----------------------------------------------------------------------------
    def do_POST(self):
        if not self._origen_valido():
            return self._error(403, "Solo se admiten peticiones desde esta misma herramienta.")
        try:
            f, listas = self._formulario()
        except ValueError as e:
            return self._error(413, str(e))
        if not hmac.compare_digest(f.get("_t", ""), self.app.token):
            return self._error(403, "Formulario caducado o ajeno: recarga la página y vuelve a intentarlo.")
        ruta = urllib.parse.urlparse(self.path).path
        try:
            return self._post(ruta, f, listas)
        except Exception as e:   # pragma: no cover
            return self._error(500, f"Error interno: {type(e).__name__}: {e}")

    def _post(self, ruta: str, f: dict, listas: dict):
        a = self.app
        if ruta == "/nueva":
            nombre = f.get("nombre", "").strip()
            if not nombre:
                return self._ir("/")
            modo = "manual" if f.get("modo") == "manual" else "automatico"
            run = Ejecucion.crear(a.base, nombre, {"modo": modo})
            a.trabajos.lanzar(run.carpeta)
            return self._ir(f"/e/{run.carpeta.name}")

        m = re.fullmatch(r"/e/([^/]+)/(avanzar|modo|accion/(\w+)|manual/([^/]+)/([^/]+))", ruta)
        if not m or not (carpeta := a.carpeta(m[1])):
            return self._error(404, "Esa ejecución no existe.")
        ident = m[1]
        if a.trabajos.trabajando(carpeta):
            a.avisar(ident, "aviso", "El motor está trabajando: espera a que termine para decidir.")
            return self._ir(f"/e/{ident}")
        run = Ejecucion.abrir(carpeta)

        if m[2] == "avanzar":
            a.trabajos.lanzar(carpeta)
            return self._ir(f"/e/{ident}")

        if m[2] == "modo":
            modo = "manual" if f.get("modo") == "manual" else "automatico"
            with run.cerrojo:
                run.estado.setdefault("config", {})["modo"] = modo
                run.guardar()
            run.registrar_decision(run.fase_actual, "modo", {"modo": modo})
            a.avisar(ident, "ok", "Modo manual: copiarás y pegarás las fichas." if modo == "manual"
                     else "Modo automático: el motor llamará a los modelos.")
            a.trabajos.lanzar(carpeta)
            return self._ir(f"/e/{ident}")

        if m[3]:
            accion = T.ACCIONES.get(m[3])
            if not accion:
                return self._error(404, "Acción desconocida.")
            if T.FASE_DE_ACCION[m[3]] != run.fase_actual:
                a.avisar(ident, "error", "Esa decisión ya no corresponde a la fase actual. Revisa la pantalla.")
                return self._ir(f"/e/{ident}")
            try:
                texto = accion(run, f, listas) if m[3] in T.CON_LISTAS else accion(run, f)
            except (ValueError, RuntimeError) as e:
                a.avisar(ident, "error", str(e))
                return self._ir(f"/e/{ident}")
            a.avisar(ident, "ok", texto)
            if m[3] != "material":            # añadir materiales no cierra nada: no hace falta avanzar
                a.trabajos.lanzar(carpeta)
            return self._ir(f"/e/{ident}")

        paso, ranura = urllib.parse.unquote(m[4]), urllib.parse.unquote(m[5])
        pend = run.estado.get("pendientes", {}).get(paso, {}).get(ranura)
        if not pend:
            return self._error(404, "Esa ficha no existe.")
        volver = f"/e/{ident}/manual/{urllib.parse.quote(paso)}/{urllib.parse.quote(ranura)}"
        texto = f.get("respuesta", "")
        if not texto.strip():
            a.avisar(ident, "error", "Pega la respuesta del modelo antes de enviarla.")
            return self._ir(volver)
        if pend["estado"] == "recibida":
            a.avisar(ident, "aviso", "Esta ficha ya tenía respuesta; no se ha cambiado.")
            return self._ir(f"/e/{ident}")
        with run.cerrojo:
            if pend["estado"] == "agotado":   # el dueño vuelve a pegar: se le da otra vez un reintento
                pend.update(estado="esperando", intentos=0)
                run.guardar()
        res = manual.recibir_respuesta(run, paso, ranura, texto)
        if res.ok:
            a.avisar(ident, "ok", f"Respuesta de «{V.nombre_ranura(paso, ranura)}» recibida y validada.")
            a.trabajos.lanzar(carpeta)
            return self._ir(f"/e/{ident}")
        a.avisar(ident, "error", "La respuesta no es válida: " + "; ".join(res.errores[:5]))
        return self._ir(volver)


def crear_servidor(app: Aplicacion, puerto: int = 8765) -> ThreadingHTTPServer:
    manejador = type("ManejadorTresia", (Manejador,), {"app": app})
    servidor = ThreadingHTTPServer(("127.0.0.1", puerto), manejador)
    servidor.daemon_threads = True
    app.puerto = servidor.server_address[1]
    return servidor
