"""Informe final en español (SPEC §4.11 y §10): qué se hizo, qué decidió el dueño,
métricas por fase y cómo se verificó. Determinista: solo lee la carpeta de la ejecución."""

from __future__ import annotations

import re

from tresia.calculo.recuento import METODO
from tresia.motor import consumo
from tresia.motor.ejecucion import FASES, Ejecucion


def _tabla(filas: list[list], cabecera: list[str]) -> str:
    lineas = ["| " + " | ".join(cabecera) + " |", "|" + "---|" * len(cabecera)]
    lineas += ["| " + " | ".join(str(c) for c in f) + " |" for f in filas]
    return "\n".join(lineas)


def _origen_legible(origen: str) -> str:
    """«faseA:E2» → «Explorador 2 (fase A)»; «ataque_ciclo_1» → «Atacante (ciclo 1)»…"""
    if m := re.fullmatch(r"faseA:E(\d)", origen):
        return f"Explorador {m[1]} (fase A)"
    if m := re.fullmatch(r"ataque_ciclo_(\d+)", origen):
        return f"Atacante (ciclo {m[1]})"
    if origen.startswith("afirmaciones:"):
        return f"afirmaciones de la versión {origen.split(':', 1)[1]}"
    if origen.endswith(":anterior"):
        return f"versión anterior a {origen.split(':', 1)[0]}"
    return f"versión {origen}"


def generar_informe(run: Ejecucion) -> str:
    ficha = run.leer("ficha.json") if run.existe("ficha.json") else {}
    metricas = run.leer("metricas.json") if run.existe("metricas.json") else {}
    b = run.estado.get("fase_b", {})
    partes = [f"# Informe: {run.estado['nombre']}", ""]
    partes += [f"**Objetivo:** {ficha.get('objetivo', '')}", ""]

    adoptada = b.get("version_adoptada")
    ruta = next((v["ruta"] for v in b.get("versiones", []) if v["nombre"] == adoptada), None)
    partes += ["## Propuesta final", "",
               f"Versión adoptada: **{adoptada}** (`{ruta}`), tras {b.get('ciclo', 0)} ciclo(s) de validación."
               if adoptada else "Todavía no hay versión adoptada.", ""]

    partes += ["## Métricas por fase", ""]
    fusion, agr, cartera, fase_a = (metricas.get(k, {}) for k in ("fusion", "agregacion", "cartera", "fase_a"))
    filas = []
    if fase_a:
        filas.append(["Fase A", f"{fase_a.get('opciones')} opciones ({fase_a.get('sin_ia')} sin IA); "
                                f"{fase_a.get('fuentes_citadas')} fuentes citadas; {fase_a.get('avisos')} avisos"])
    if fusion:
        filas.append(["Fusión", f"{fusion.get('grupos')} grupos; {fusion.get('nuevos')} nuevos frente a la línea base "
                                f"({fusion.get('novedad', 0):.0%}); Jaccard {fusion.get('jaccard')}; "
                                f"aportes únicos {fusion.get('aportes_unicos')}"])
    if agr:
        filas.append(["Criba", f"{agr.get('opciones_evaluadas')} evaluadas; {agr.get('eliminadas')} eliminadas; "
                               f"{agr.get('con_desacuerdo')} con desacuerdo; {agr.get('opciones_nuevas_propuestas')} opciones nuevas"])
    if cartera:
        filas.append(["Cartera", f"{cartera.get('seleccionadas')} seleccionadas {cartera.get('por_origen')}; "
                                 f"{cartera.get('archivadas')} archivadas (pueden volver)"])
    partes += [_tabla(filas, ["Fase", "Resultado"]) if filas else "Sin métricas todavía.", ""]

    if run.existe("cartera.json"):
        partes += ["## Cartera", ""]
        partes += [f"- {s['name']} — {s['motivo']}" + (" **(decisión del dueño)**" if s["origen"] == "dueno" else "")
                   for s in run.leer("cartera.json")["seleccion"]]
        partes.append("")

    partes += ["## Ciclos de validación", ""]
    for v in b.get("versiones", []):
        notas_ruta = f"faseB/ciclo_{v['ciclo']}/notas_verificador_{v['nombre']}.json"
        alertas = run.leer(notas_ruta).get("alertas", []) if run.existe(notas_ruta) else []
        partes.append(f"- **{v['nombre']}** (ciclo {v['ciclo']}, {v['paso']}): "
                      + ("; ".join(alertas) if alertas else "sin alertas del verificador determinista."))
    partes.append("")

    decisiones = [d for d in run.decisiones() if d["origen"] in ("dueno",) and d["tipo"] != "aprobacion"]
    partes += ["## Decisiones del dueño", ""]
    partes += [f"- {d['fecha'][:16]} · {d['fase']} · {d['tipo']}: "
               + ", ".join(f"{k}={v}" for k, v in d.items() if k not in ("fecha", "fase", "tipo", "origen"))
               for d in decisiones] or ["- Ninguna además de las aprobaciones."]
    partes.append("")

    avisos = run.estado.get("avisos", [])
    partes += ["## Avisos del proceso", ""]
    partes += [f"- {a['fecha'][:16]} · {a['texto']}" for a in avisos] or ["- Ninguno."]
    partes.append("")

    resumen = consumo.resumen_por_fase(run)
    if resumen:
        def minutos(s):
            return f"{s / 60:.1f} min"
        filas = [[r["fase"], r["llamadas"], r["fallidas"], minutos(r["reloj_segundos"]), minutos(r["segundos"]),
                  f"{r['tokens_entrada']:,} / {r['tokens_salida']:,}".replace(",", "."),
                  f"{r['coste_usd']:.2f} USD" if r["coste_usd"] else "—"] for r in resumen]
        sin_datos = sum(r["sin_datos_de_consumo"] for r in resumen)
        partes += ["## Tiempo y consumo por fase", "",
                   _tabla(filas, ["Fase", "Llamadas", "Fallidas", "Tiempo (reloj)", "Tiempo (suma de llamadas)",
                                  "Tokens entrada / salida", "Coste conocido"]), "",
                   "El tiempo de reloj va de la primera a la última llamada de la fase (las llamadas en paralelo "
                   "se solapan). El coste es el que informa el proveedor o el calculado con los precios del perfil; "
                   "con suscripción es orientativo." + (f" {sin_datos} llamadas no traen datos de consumo." if sin_datos else ""),
                   ""]

    if run.existe("fuentes.json"):
        estados: dict[str, int] = {}
        for e in run.leer("fuentes.json").values():
            estados[e["estado"]] = estados.get(e["estado"], 0) + 1
        partes += ["## Fuentes", "", ", ".join(f"{k}: {v}" for k, v in sorted(estados.items())),
                   "", "El motor descarga cada fuente citada y busca el fragmento en la página. "
                   "Nada se marca como verificado sin fragmento comprobado.", ""]
        fallidas = [e for e in run.leer("fuentes.json").values() if e["estado"] in ("no_coincide", "inaccesible")]
        if fallidas:
            partes += ["Fuentes citadas que no se pudieron verificar:", ""]
            partes += [f"- {e['url']} — {e['estado'].replace('_', ' ')}"
                       + (f" ({e['comprobaciones'][-1]['nota']})" if e.get("comprobaciones") else "")
                       + f"; citada en {', '.join(_origen_legible(c) for c in e['citada_en'])}" for e in fallidas[:40]]
            if len(fallidas) > 40:
                partes.append(f"- … y {len(fallidas) - 40} más (ver fuentes.json).")
            partes.append("")

    partes += ["## Método", "", f"Recuento de palabras: {METODO}",
               "Fases: " + " → ".join(n for _, n, _ in FASES) + ".", ""]
    texto = "\n".join(partes)
    run.escribir("informe.md", texto)
    return texto
