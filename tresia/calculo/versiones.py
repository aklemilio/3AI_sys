"""Comparación entre versiones del entregable (SPEC §7, lección 19).

Detecta sin modelo:
- secciones perdidas, añadidas o renombradas;
- URL de fuentes perdidas;
- recortes declarados en el registro de cambios que no se ven en el recuento.

Acepta texto Markdown (encabezados ``#``) y texto plano exportado, donde los
encabezados son líneas cortas que empiezan por «1.», «A.», «Annex», «Programme»…
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from tresia.calculo.limpieza_json import JSONIrrecuperable, extraer_json
from tresia.calculo.recuento import palabras, urls

# Marcadores del registro de cambios que el constructor añade al final.
_INICIO_REGISTRO = re.compile(r"^\s*#*\s*\**\s*(change register|registro de cambios)", re.IGNORECASE | re.MULTILINE)
_PALABRAS_RECORTE = re.compile(
    r"\b(compress\w*|condens\w*|shorten\w*|trim\w*|cut\b|reduc\w*|remove duplicat\w*|"
    r"recort\w*|acort\w*|condensa\w*|reduci\w*|resum\w*)",
    re.IGNORECASE,
)
_ENCABEZADO_MD = re.compile(r"^\s{0,3}(#{1,6})\s+(.*\S)\s*$")
_ENCABEZADO_PLANO = re.compile(r"^(?:(?:\d{1,2}\.|[A-Z]\.|Programme\b|Programa\b)\s*\S.*|(?:Annex|Anexo)\b.*)$")
_PREFIJO = re.compile(r"^(\d{1,2}|[A-Z])\.\s")
_ETIQUETAS = re.compile(r"\s*\[[^\]]*\]")
_PALABRAS_FUENTES = re.compile(r"\b(source|sources|fuente|fuentes|references|referencias)\b", re.IGNORECASE)

UMBRAL_RECORTE = 0.10   # un recorte declarado debe reducir al menos un 10 %


def _limpiar_titulo(t: str) -> str:
    t = t.replace("*", "").replace("`", "")
    t = _ETIQUETAS.sub("", t)
    return re.sub(r"\s+", " ", t).strip()


def separar_registro(texto: str) -> tuple[str, str]:
    """Devuelve (documento, registro de cambios)."""
    m = _INICIO_REGISTRO.search(texto)
    return (texto[: m.start()], texto[m.start():]) if m else (texto, "")


def cambios_declarados(texto_registro: str) -> list[dict]:
    if not texto_registro:
        return []
    try:
        datos = extraer_json(texto_registro)
    except JSONIrrecuperable:
        return []
    return datos.get("changes", []) if isinstance(datos, dict) else []


def secciones(documento: str) -> list[dict]:
    """Encabezados con su clave de comparación: el prefijo («1», «A») si lo hay,
    si no el título normalizado. Dentro del anexo las letras llevan prefijo «anexo:».
    La primera línea con texto es el título del documento y no cuenta como sección."""
    salida, en_anexo = [], False
    lineas = documento.splitlines()
    primera = next((i for i, l in enumerate(lineas) if l.strip()), None)
    for i, linea in enumerate(lineas):
        if i == primera:
            continue
        if m := _ENCABEZADO_MD.match(linea):
            titulo = _limpiar_titulo(m.group(2))
        elif _ENCABEZADO_PLANO.match(linea.strip()) and len(linea.split()) <= 12 and not linea.rstrip().endswith((".", ";", ":")):
            titulo = _limpiar_titulo(linea)
        else:
            continue
        if not titulo:
            continue
        if re.fullmatch(r"(annex|anexo)", titulo, re.IGNORECASE):
            en_anexo = True
        p = _PREFIJO.match(titulo)
        clave = (p.group(1) if p else titulo.lower())
        if en_anexo and p:
            clave = "anexo:" + clave
        salida.append({"clave": clave, "titulo": titulo})
    # Una clave repetida (p. ej. una lista numerada confundida con encabezado) se queda con la primera.
    vistas, unicas = set(), []
    for s in salida:
        if s["clave"] not in vistas:
            vistas.add(s["clave"])
            unicas.append(s)
    return unicas


@dataclass
class Comparacion:
    secciones_perdidas: list[str] = field(default_factory=list)
    secciones_nuevas: list[str] = field(default_factory=list)
    secciones_renombradas: list[dict] = field(default_factory=list)
    registro_de_fuentes_perdido: list[str] = field(default_factory=list)
    urls_anteriores: int = 0
    urls_nuevas: int = 0
    urls_perdidas: list[str] = field(default_factory=list)
    palabras_anteriores: int = 0
    palabras_nuevas: int = 0
    recortes_declarados: list[dict] = field(default_factory=list)
    recortes_no_producidos: list[dict] = field(default_factory=list)

    @property
    def alertas(self) -> list[str]:
        a = []
        if self.urls_perdidas:
            todas = " (todas)" if self.urls_nuevas == 0 and self.urls_anteriores else ""
            a.append(f"Se perdieron {len(self.urls_perdidas)} de {self.urls_anteriores} URL de fuentes{todas}.")
        if self.registro_de_fuentes_perdido:
            a.append("Desapareció el registro de fuentes: " + "; ".join(self.registro_de_fuentes_perdido) + ".")
        for s in self.secciones_perdidas:
            a.append(f"Sección perdida: {s}.")
        for r in self.recortes_no_producidos:
            a.append(f"Recorte declarado que no se produjo ({r['addresses']}): {r['motivo']}")
        return a

    def como_dict(self) -> dict:
        return asdict(self) | {"alertas": self.alertas}


def comparar(anterior: str, nueva: str, umbral_recorte: float = UMBRAL_RECORTE) -> Comparacion:
    doc_a, reg_a = separar_registro(anterior)
    doc_n, reg_n = separar_registro(nueva)
    c = Comparacion()

    sec_a = {s["clave"]: s["titulo"] for s in secciones(doc_a)}
    sec_n = {s["clave"]: s["titulo"] for s in secciones(doc_n)}
    c.secciones_perdidas = [sec_a[k] for k in sec_a if k not in sec_n]
    c.secciones_nuevas = [sec_n[k] for k in sec_n if k not in sec_a]
    for k in sec_a.keys() & sec_n.keys():
        if sec_a[k].lower() != sec_n[k].lower():
            c.secciones_renombradas.append({"antes": sec_a[k], "despues": sec_n[k]})
            if _PALABRAS_FUENTES.search(sec_a[k]) and not _PALABRAS_FUENTES.search(sec_n[k]):
                c.registro_de_fuentes_perdido.append(f"«{sec_a[k]}» pasó a «{sec_n[k]}»")
    for t in c.secciones_perdidas:
        if _PALABRAS_FUENTES.search(t):
            c.registro_de_fuentes_perdido.append(f"«{t}» ya no existe")
    c.secciones_renombradas.sort(key=lambda r: r["antes"])

    # Las URL cuentan en todo el texto: también las del registro de cambios (respaldos).
    u_a, u_n = urls(anterior), set(urls(nueva))
    c.urls_anteriores, c.urls_nuevas = len(u_a), len(u_n)
    c.urls_perdidas = [u for u in u_a if u not in u_n]

    c.palabras_anteriores, c.palabras_nuevas = palabras(doc_a), palabras(doc_n)
    for cambio in cambios_declarados(reg_n):
        texto = f"{cambio.get('change', '')}"
        if not _PALABRAS_RECORTE.search(texto):
            continue
        reduccion = 1 - c.palabras_nuevas / c.palabras_anteriores if c.palabras_anteriores else 0
        r = {"section": cambio.get("section", ""), "addresses": cambio.get("addresses", ""),
             "change": texto, "reduccion": round(reduccion, 4)}
        c.recortes_declarados.append(r)
        if reduccion < umbral_recorte:
            r = dict(r, motivo=(
                f"el documento pasó de {c.palabras_anteriores} a {c.palabras_nuevas} palabras "
                f"(reducción del {reduccion:.1%}; se esperaba al menos un {umbral_recorte:.0%})."
            ))
            c.recortes_no_producidos.append(r)
    return c
