"""CLI falsa para probar el adaptador sin llamar a ningún modelo.

Uso: cli_falso.py <modo> [archivo_salida]
  eco_json     -> imprime {"result": "<json válido>"} como «claude -p --output-format json»
  archivo      -> escribe la respuesta en archivo_salida, como «codex exec --output-last-message»
  invalido     -> responde texto sin JSON la primera vez y JSON válido si ve el reintento
  dormir       -> espera mucho (para probar el tiempo máximo)
  falla        -> sale con código 3
  eco_prompt   -> devuelve el prompt recibido por stdin (comprueba UTF-8 y tamaño)
"""

import json
import sys
import time

modo = sys.argv[1]
prompt = sys.stdin.buffer.read().decode("utf-8")
valido = json.dumps({"assessments": [{"id": "C01", "fatal": False, "scores": {"impact": 4}}]})

if modo == "eco_json":
    sys.stdout.write(json.dumps({"type": "result", "is_error": False, "result": "```json\n" + valido + "\n```"}))
elif modo == "archivo":
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        f.write(valido)
    sys.stdout.write("log de progreso que no es la respuesta\n")
elif modo == "invalido":
    sys.stdout.write(valido if "ONLY the JSON" in prompt else "I cannot answer in JSON, sorry.")
elif modo == "dormir":
    time.sleep(60)
elif modo == "falla":
    sys.stderr.write("error simulado\n")
    sys.exit(3)
elif modo == "eco_prompt":
    sys.stdout.buffer.write(prompt.encode("utf-8"))
