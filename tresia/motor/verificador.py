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
    obtener: F.Descargador = F.descargar,
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
        for entrada in registro.values():
            if entrada["fragmento"]:
                F.anotar_comprobacion(registro, F.comprobar(entrada["url"], entrada["fragmento"], obtener))
    notas["fuentes_por_estado"] = _por_estado(registro)

    notas["alertas"] = alertas
    run.escribir("fuentes.json", registro)
    run.escribir(f"faseB/ciclo_{ciclo}/notas_verificador_{version}.json", notas)
    return notas


def registrar_fuentes_de_salida(run: Ejecucion, datos, origen: str) -> int:
    """Lleva al registro las fuentes con fragmento que cita una salida de papel (E1, S2, ataque…)."""
    registro = _registro(run)
    nuevas = F.fuentes_de(datos)
    F.registrar(registro, nuevas, origen)
    run.escribir("fuentes.json", registro)
    return len(nuevas)


def _urls_sin_registro(registro: dict, texto: str) -> list[str]:
    from tresia.calculo.recuento import urls
    conocidas = {e["url"] for e in registro.values()}
    return [u for u in urls(texto) if u not in conocidas]


def _por_estado(registro: dict) -> dict[str, int]:
    salida: dict[str, int] = {}
    for e in registro.values():
        salida[e["estado"]] = salida.get(e["estado"], 0) + 1
    return salida
