"""Comprobación de fuentes y registro de fuentes (SPEC §7, lecciones 10 y 19).

- Se descarga la URL y se busca el fragmento normalizado (espacios, comillas,
  rayas, mayúsculas y diacríticos).
- Estados: ``verificada``, ``no_coincide``, ``inaccesible`` o ``sin_fragmento``.
  Nada se marca verificado sin fragmento.
- El registro de fuentes (``fuentes.json``) solo crece: una fuente no desaparece
  porque una versión nueva la haya quitado; se marca como ausente en esa versión.
"""

from __future__ import annotations

import hashlib
import html
import re
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Callable

VERIFICADA, NO_COINCIDE, INACCESIBLE, SIN_FRAGMENTO = "verificada", "no_coincide", "inaccesible", "sin_fragmento"
AGENTE = "tresia-verificador/0.1 (+comprobacion de fuentes)"
TIEMPO_MAXIMO = 20
TAMANO_MAXIMO = 8 * 1024 * 1024

_TRADUCCION = str.maketrans({
    "“": '"', "”": '"', "„": '"', "«": '"', "»": '"', "″": '"',
    "‘": "'", "’": "'", "‚": "'", "′": "'", "´": "'", "`": "'",
    "–": "-", "—": "-", "−": "-", "‐": "-", "‑": "-",
    " ": " ", " ": " ", " ": " ", "​": "",
    "…": "...",
})
_ETIQUETA = re.compile(r"<[^>]+>")
_BLOQUES_SIN_TEXTO = re.compile(r"<(script|style|noscript)\b.*?</\1>", re.IGNORECASE | re.DOTALL)


def normalizar(texto: str) -> str:
    """Texto comparable: sin HTML, sin diacríticos, comillas y rayas unificadas,
    minúsculas y espacios colapsados."""
    texto = html.unescape(texto).translate(_TRADUCCION)
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto).strip().lower()


def texto_de_html(contenido: str) -> str:
    contenido = _BLOQUES_SIN_TEXTO.sub(" ", contenido)
    return _ETIQUETA.sub(" ", contenido)


def descargar(url: str) -> tuple[str, str]:
    """Devuelve (tipo de contenido, texto). Lanza ``OSError`` si no se puede."""
    peticion = urllib.request.Request(url, headers={"User-Agent": AGENTE, "Accept": "text/html,text/plain,*/*"})
    with urllib.request.urlopen(peticion, timeout=TIEMPO_MAXIMO) as r:
        tipo = r.headers.get_content_type()
        datos = r.read(TAMANO_MAXIMO)
        juego = r.headers.get_content_charset() or "utf-8"
    return tipo, datos.decode(juego, errors="replace")


Descargador = Callable[[str], tuple[str, str]]


def comprobar(url: str, fragmento: str, obtener: Descargador = descargar) -> dict:
    """Comprueba que ``fragmento`` aparece en ``url``. ``obtener`` se puede sustituir
    (pruebas sin red, caché o modo manual)."""
    resultado = {"url": url, "fragmento": fragmento, "fecha": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    if not fragmento or not normalizar(fragmento):
        return resultado | {"estado": SIN_FRAGMENTO, "nota": "Sin fragmento no se puede verificar."}
    if not url or not url.startswith(("http://", "https://")):
        return resultado | {"estado": INACCESIBLE, "nota": "URL ausente o no válida."}
    try:
        tipo, contenido = obtener(url)
    except (OSError, urllib.error.URLError, ValueError) as e:
        return resultado | {"estado": INACCESIBLE, "nota": f"No se pudo descargar: {e}"}
    if tipo == "application/pdf":
        return resultado | {"estado": INACCESIBLE, "nota": "PDF: el MVP no extrae texto de PDF; comprobar a mano."}
    pagina = normalizar(texto_de_html(contenido) if "html" in tipo or "<" in contenido[:500] else contenido)
    if normalizar(fragmento) in pagina:
        return resultado | {"estado": VERIFICADA, "nota": ""}
    return resultado | {"estado": NO_COINCIDE, "nota": "El fragmento no aparece en la página descargada."}


# --- registro de fuentes -------------------------------------------------------------
def clave(url: str, fragmento: str) -> str:
    return hashlib.sha1(f"{url}\n{normalizar(fragmento)}".encode("utf-8")).hexdigest()[:12]


def fuentes_de(datos) -> list[dict]:
    """Extrae los respaldos de tipo «source» de cualquier salida JSON de un papel."""
    encontradas = []

    def recorrer(x):
        if isinstance(x, dict):
            if x.get("type") == "source" and "url" in x:
                encontradas.append({"url": x.get("url", ""), "fragmento": x.get("fragment", ""), "afirmacion": x.get("claim", "")})
            for v in x.values():
                recorrer(v)
        elif isinstance(x, list):
            for v in x:
                recorrer(v)

    recorrer(datos)
    return encontradas


def registrar(registro: dict, fuentes: list[dict], origen: str) -> dict:
    """Añade fuentes al registro sin borrar ninguna. ``origen``: fase o versión que la cita."""
    for f in fuentes:
        k = clave(f["url"], f.get("fragmento", ""))
        entrada = registro.setdefault(k, {"url": f["url"], "fragmento": f.get("fragmento", ""),
                                          "afirmaciones": [], "citada_en": [], "comprobaciones": [],
                                          "estado": SIN_FRAGMENTO if not f.get("fragmento") else "sin_comprobar"})
        if f.get("afirmacion") and f["afirmacion"] not in entrada["afirmaciones"]:
            entrada["afirmaciones"].append(f["afirmacion"])
        if origen not in entrada["citada_en"]:
            entrada["citada_en"].append(origen)
    return registro


def anotar_comprobacion(registro: dict, resultado: dict) -> None:
    entrada = registro[clave(resultado["url"], resultado["fragmento"])]
    entrada["comprobaciones"].append({k: resultado[k] for k in ("fecha", "estado", "nota")})
    entrada["estado"] = resultado["estado"]


def ausentes_en(registro: dict, texto_version: str) -> list[dict]:
    """Fuentes del registro cuya URL ya no aparece en la versión: hay que restituirlas
    o justificar la retirada (lección 19)."""
    return [e for e in registro.values() if e["url"] and e["url"] not in texto_version]
