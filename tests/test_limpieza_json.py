"""Prueba 7 de la SPEC (§11): limpieza de JSON pegado desde la web."""

import pytest

from conftest import CASO
from tresia.calculo import esquemas
from tresia.calculo.limpieza_json import JSONIrrecuperable, extraer_json

ESPERADO = {"id": "C01", "name": "Archivo_semilla [mínimo]", "ok": True, "n": [1, 2]}


@pytest.mark.parametrize("texto", [
    # JSON limpio con texto alrededor y bloque de código
    'Sure! Here it is:\n```json\n{"id": "C01", "name": "Archivo_semilla [mínimo]", "ok": true, "n": [1, 2]}\n```\nHope it helps.',
    # Sin bloque de código, con texto antes y después
    'Answer: {"id": "C01", "name": "Archivo_semilla [mínimo]", "ok": true, "n": [1, 2]} -- end',
    # Entidades HTML de la web (&#x20;, &quot;)
    '```json\n{&quot;id&quot;:&#x20;"C01", "name": "Archivo_semilla [mínimo]", "ok": true, "n": [1,&#x20;2]}\n```',
    # Escapes de Markdown (\_ \[ \])
    '```json\n{"id": "C01", "name": "Archivo\\_semilla \\[mínimo\\]", "ok": true, "n": [1, 2]}\n```',
    # Comillas tipográficas, espacio duro y coma final
    '{“id”: “C01”, "name": "Archivo_semilla [mínimo]", "ok": true, "n": [1, 2,],}',
    # JSON entero escapado (comillas con barra invertida)
    '{\\"id\\": \\"C01\\", \\"name\\": \\"Archivo_semilla [mínimo]\\", \\"ok\\": true, \\"n\\": [1, 2]}',
    # Doblemente serializado: una cadena JSON que contiene el objeto
    '"{\\"id\\": \\"C01\\", \\"name\\": \\"Archivo_semilla [mínimo]\\", \\"ok\\": true, \\"n\\": [1, 2]}"',
    # BOM y bloque sin etiqueta de lenguaje
    '﻿```\n{"id": "C01", "name": "Archivo_semilla [mínimo]", "ok": true, "n": [1, 2]}\n```',
])
def test_7_acepta_artefactos(texto):
    assert extraer_json(texto) == ESPERADO


def test_7_fixture_real_con_artefactos_de_pegado():
    original = (CASO / "S1.json").read_text(encoding="utf-8")
    sucio = "Here you go\n\n```json\n" + original.replace("_reason", "\\_reason").replace(" ", "&#x20;", 40) + "\n```"
    datos = extraer_json(sucio)
    assert esquemas.errores("screener", datos) == []
    assert len(datos["assessments"]) == 41


@pytest.mark.parametrize("texto", ["", "   ", "No JSON here at all.", "```json\n{ roto: \n```"])
def test_7_irrecuperable(texto):
    with pytest.raises(JSONIrrecuperable):
        extraer_json(texto)
