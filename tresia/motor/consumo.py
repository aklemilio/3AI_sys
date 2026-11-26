"""Tiempo y consumo de cada llamada a un modelo (SSB-106: medir por fase).

Una línea por llamada en ``llamadas.jsonl``: paso, ranura, inicio, segundos,
caracteres enviados y recibidos, tokens y coste cuando el proveedor los da.
Claude (``claude -p --output-format json``) informa del coste; Gemini y Ollama,
de los tokens. Si el perfil da precios (``precio_usd_por_millon = {entrada, salida}``),
el coste se calcula con los tokens. El modelo concreto se guarda en disco, como
las identidades, pero el resumen es por fase y nunca dice quién es quién.
"""

from __future__ import annotations

import json
import re
from datetime import datetime

from tresia.motor.ejecucion import Ejecucion, _ahora

ARCHIVO = "llamadas.jsonl"


def extraer_uso(bruto: str, definicion: dict | None = None) -> dict:
    """Tokens y coste de la respuesta bruta del proveedor (vacío si no los da)."""
    try:
        d = json.loads(bruto)
    except (TypeError, ValueError):
        return {}
    if not isinstance(d, dict):
        return {}
    uso: dict = {}
    if "total_cost_usd" in d or "usage" in d:                            # Claude Code
        u = d.get("usage") or {}
        uso["tokens_entrada"] = sum(int(u.get(k) or 0) for k in
                                    ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")) or None
        uso["tokens_salida"] = u.get("output_tokens")
        if d.get("total_cost_usd") is not None:
            uso["coste_usd"] = float(d["total_cost_usd"])
    elif "usageMetadata" in d:                                            # Gemini
        u = d["usageMetadata"]
        uso["tokens_entrada"] = u.get("promptTokenCount")
        uso["tokens_salida"] = (u.get("candidatesTokenCount") or 0) + (u.get("thoughtsTokenCount") or 0)
    elif "prompt_eval_count" in d or "eval_count" in d:                   # Ollama
        uso["tokens_entrada"] = d.get("prompt_eval_count")
        uso["tokens_salida"] = d.get("eval_count")
    precio = (definicion or {}).get("precio_usd_por_millon")
    if "coste_usd" not in uso and isinstance(precio, dict) and uso.get("tokens_entrada") is not None:
        uso["coste_usd"] = round(((uso.get("tokens_entrada") or 0) * float(precio.get("entrada", 0))
                                  + (uso.get("tokens_salida") or 0) * float(precio.get("salida", 0))) / 1e6, 6)
    return {k: v for k, v in uso.items() if v is not None}


def registrar(run: Ejecucion, paso: str, ranura: str, prompt: str, inicio: str, segundos: float,
              respuesta=None, error: Exception | str | None = None, adaptador=None, etiqueta: str = "") -> dict:
    linea = {"paso": paso, "ranura": ranura, "inicio": inicio, "segundos": round(segundos, 1),
             "caracteres_enviados": len(prompt), "caracteres_recibidos": len(respuesta.texto) if respuesta else 0,
             "ok": error is None, "modelo": etiqueta}
    if error is not None:
        linea["error"] = str(error)[:300]
    if respuesta is not None:
        linea |= extraer_uso(respuesta.bruto, getattr(adaptador, "definicion", None))
    with run.cerrojo, open(run.carpeta / ARCHIVO, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(linea, ensure_ascii=False) + "\n")
    return linea


def llamar(run: Ejecucion, paso: str, ranura: str, adaptador, prompt: str, etiqueta: str = ""):
    """``adaptador.llamar(prompt)`` midiendo tiempo y consumo. Relanza el error."""
    import time
    inicio, t0 = _ahora(), time.monotonic()
    try:
        r = adaptador.llamar(prompt)
    except Exception as e:
        registrar(run, paso, ranura, prompt, inicio, time.monotonic() - t0, error=e, adaptador=adaptador, etiqueta=etiqueta)
        raise
    registrar(run, paso, ranura, prompt, inicio, time.monotonic() - t0, respuesta=r, adaptador=adaptador, etiqueta=etiqueta)
    return r


# --- resumen por fase -------------------------------------------------------------------------------
def fase_de_paso(paso: str) -> str:
    if paso == "fase_a":
        return "Fase A"
    if paso == "fusion":
        return "Fusión"
    if paso == "criba":
        return "Criba"
    if m := re.fullmatch(r"b(\d+)_\w+", paso):
        return f"Fase B, ciclo {m[1]}"
    if paso.startswith("verificador_"):
        return "Verificador (tareas sueltas)"
    return "Otras"


def llamadas(run: Ejecucion) -> list[dict]:
    if not run.existe(ARCHIVO):
        return []
    return [json.loads(l) for l in (run.carpeta / ARCHIVO).read_text(encoding="utf-8").splitlines() if l.strip()]


def resumen_por_fase(run: Ejecucion) -> list[dict]:
    """Por fase: llamadas, fallidas, tiempo de reloj (de la primera a la última),
    suma de segundos de todas las llamadas, tokens y coste conocido."""
    grupos: dict[str, dict] = {}
    for l in llamadas(run):
        g = grupos.setdefault(fase_de_paso(l["paso"]), {"llamadas": 0, "fallidas": 0, "segundos": 0.0,
                                                        "tokens_entrada": 0, "tokens_salida": 0, "coste_usd": 0.0,
                                                        "sin_datos_de_consumo": 0, "inicio": None, "fin": None})
        g["llamadas"] += 1
        g["fallidas"] += not l["ok"]
        g["segundos"] += l["segundos"]
        g["tokens_entrada"] += l.get("tokens_entrada") or 0
        g["tokens_salida"] += l.get("tokens_salida") or 0
        g["coste_usd"] += l.get("coste_usd") or 0.0
        g["sin_datos_de_consumo"] += l["ok"] and "tokens_entrada" not in l and "coste_usd" not in l
        ini = datetime.fromisoformat(l["inicio"])
        fin = ini.timestamp() + l["segundos"]
        g["inicio"] = min(g["inicio"] or ini.timestamp(), ini.timestamp())
        g["fin"] = max(g["fin"] or fin, fin)
    salida = []
    for fase, g in grupos.items():
        salida.append({"fase": fase, **{k: v for k, v in g.items() if k not in ("inicio", "fin")},
                       "reloj_segundos": round((g["fin"] - g["inicio"]) if g["inicio"] is not None else 0, 1),
                       "segundos": round(g["segundos"], 1), "coste_usd": round(g["coste_usd"], 4)})
    return salida
