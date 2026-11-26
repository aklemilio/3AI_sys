"""Verificador determinista sobre una versión de la fase B (SPEC §4.10.2 y §7).

Recuenta, compara con la versión anterior y lleva el registro de fuentes. Escribe
``faseB/ciclo_N/notas_verificador_<version>.json`` y ``fuentes.json``. La parte
con modelo (afirmaciones, premisas, orden temporal, cumplimiento) llega en el hito 3.
"""

from __future__ import annotations

from tresia.calculo import fuentes as F
from tresia.calculo.recuento import METODO, elementos, palabras, tramo
from tresia.calculo.versiones import comparar, separar_registro
from tresia.motor.ejecucion import Ejecucion


def _registro(run: Ejecucion) -> dict:
    return run.leer("fuentes.json") if run.existe("fuentes.json") else {}


def verificar_version(
    run: Ejecucion,
    ciclo: int,
    version: str,
    texto: str,
    anterior: str | None = None,
    partes: dict[str, tuple[str | None, str | None]] | None = None,
    limites: dict[str, int] | None = None,
    comprobar_fuentes: bool = False,
    obtener: F.Descargador | None = None,
) -> dict:
    """``partes``: nombre -> (marcador inicial, marcador final) para el recuento por
    partes, p. ej. {"cuerpo": (None, "# **Annex"), "anexo": ("# **Annex", "## **G.")}.
    ``comprobar_fuentes`` descarga las URL (necesita red)."""
    documento, _ = separar_registro(texto)
    notas: dict = {"version": version, "metodo_recuento": METODO}

    e = elementos(documento)
    notas["recuento"] = {"total": vars(e)}
    limites = limites or {}
    for nombre, (desde, hasta) in (partes or {}).items():
        try:
            n = palabras(tramo(texto, desde, hasta))
        except ValueError:
            notas["recuento"][nombre] = {"error": f"No se encontró el marcador de «{nombre}»."}
            continue
        lim = limites.get(nombre)
        notas["recuento"][nombre] = {"palabras": n, "limite": lim, "excede": lim is not None and n > lim}

    alertas = [f"«{k}» tiene {v['palabras']} palabras; el límite es {v['limite']}."
               for k, v in notas["recuento"].items() if isinstance(v, dict) and v.get("excede")]

    if anterior is not None:
        comp = comparar(anterior, texto)
        notas["comparacion"] = comp.como_dict()
        alertas += comp.alertas

    registro = _registro(run)
    if anterior is not None:
        F.registrar(registro, [{"url": u, "fragmento": ""} for u in _urls_sin_registro(registro, anterior)], f"{version}:anterior")
    citadas = [{"url": u, "fragmento": ""} for u in _urls_sin_registro(registro, texto)]
    F.registrar(registro, citadas, version)
    ausentes = F.ausentes_en(registro, texto)
    notas["fuentes_ausentes"] = [{"url": a["url"], "citada_en": a["citada_en"]} for a in ausentes]
    if ausentes:
        alertas.append(f"{len(ausentes)} fuentes del registro no aparecen en esta versión; hay que restituirlas o justificar su retirada.")

    if comprobar_fuentes:
        notas["fuentes_comprobadas_ahora"] = F.comprobar_pendientes(registro, obtener)
    notas["fuentes_por_estado"] = _por_estado(registro)
    if fallidas := fuentes_no_verificadas(registro):
        alertas.append(f"{len(fallidas)} fuentes citadas no se pudieron verificar (fragmento ausente, página "
                       "inaccesible o sin fragmento); no cuentan como respaldo hasta corregirlas.")

    notas["alertas"] = alertas
    run.escribir("fuentes.json", registro)
    run.escribir(f"faseB/ciclo_{ciclo}/notas_verificador_{version}.json", notas)
    return notas


def comprobacion_activa(run: Ejecucion) -> bool:
    """La comprobación en línea está activa salvo que la ficha la desactive
    (``"comprobar_fuentes": false``, por ejemplo sin conexión)."""
    ficha = run.leer("ficha.json") if run.existe("ficha.json") else {}
    return bool(ficha.get("comprobar_fuentes", True))


def registrar_fuentes_de_salida(run: Ejecucion, datos, origen: str, comprobar: bool = True) -> int:
    """Lleva al registro las fuentes con fragmento que cita una salida de papel (E1,
    ataque, registro de cambios, afirmaciones del verificador…) y comprueba en línea
    las nuevas: la solidez de una fuente la asigna el motor, no quien la cita."""
    with run.cerrojo:
        registro = _registro(run)
        nuevas = F.fuentes_de(datos)
        F.registrar(registro, nuevas, origen)
        if comprobar and comprobacion_activa(run):
            F.comprobar_pendientes(registro)
        run.escribir("fuentes.json", registro)
    return len(nuevas)


NO_VERIFICADAS = (F.NO_COINCIDE, F.INACCESIBLE)
_MOTIVO = {F.NO_COINCIDE: "fragment not found on the page", F.INACCESIBLE: "page inaccessible",
           F.SIN_FRAGMENTO: "no fragment given", F.SIN_COMPROBAR: "not checked (online checking is off)"}


def aplicar_comprobacion_a_afirmaciones(run: Ejecucion, ruta: str) -> int:
    """La solidez de una afirmación de tipo «source» la decide la comprobación del
    motor, no el modelo: si el fragmento no se encontró en la página (o no hay URL o
    fragmento), pasa a «unsupported» con una nota. Devuelve cuántas se rebajaron."""
    datos = run.leer(ruta)
    registro = _registro(run)
    rebajadas = 0
    for c in datos.get("claims", []):
        if c.get("type") != "source":
            continue
        e = registro.get(F.clave(c.get("url", ""), c.get("fragment", ""))) if c.get("url") else None
        estado = e["estado"] if e else (F.SIN_FRAGMENTO if c.get("url") else F.INACCESIBLE)
        c["engine_check"] = estado
        if estado == F.VERIFICADA:
            continue
        motivo = "no URL given" if not c.get("url") else _MOTIVO.get(estado, estado)
        if c.get("strength") != "unsupported":
            c["model_strength"] = c.get("strength")
            c["strength"] = "unsupported"
            rebajadas += 1
        c["note"] = (c.get("note", "") + " " if c.get("note") else "") + f"Engine check: {motivo}."
    run.escribir(ruta, datos)
    return rebajadas


def fuentes_no_verificadas(registro: dict) -> list[dict]:
    return [e for e in registro.values() if e.get("estado") in NO_VERIFICADAS]


def estado_de_fuentes(run: Ejecucion) -> list[dict]:
    """Resumen para los papeles (atacante, evaluadores, cribadores): qué fuentes
    comprobó el motor y con qué resultado. En inglés, como los prompts."""
    nombres = {F.VERIFICADA: "verified: fragment found on the page", F.NO_COINCIDE: "NOT verified: fragment not found on the page",
               F.INACCESIBLE: "NOT verified: page inaccessible", F.SIN_FRAGMENTO: "NOT verifiable: no fragment given",
               F.SIN_COMPROBAR: "not checked yet"}
    return [{"url": e["url"], "fragment": e["fragmento"][:200], "status": nombres.get(e["estado"], e["estado"])}
            for e in _registro(run).values() if e["url"]]


def _urls_sin_registro(registro: dict, texto: str) -> list[str]:
    from tresia.calculo.recuento import urls
    conocidas = {e["url"] for e in registro.values()}
    return [u for u in urls(texto) if u not in conocidas]


def _por_estado(registro: dict) -> dict[str, int]:
    salida: dict[str, int] = {}
    for e in registro.values():
        salida[e["estado"]] = salida.get(e["estado"], 0) + 1
    return salida
