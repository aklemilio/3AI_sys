# 3AI_sys — sistema de tres IA

Herramienta local para ampliar y validar ideas, documentos, código o negocios con tres modelos de proveedores distintos. Primero abre opciones y después las valida de forma medible. Motor determinista en Python, papeles en `skills/*/SKILL.md` y decisiones humanas en puntos fijos.

La especificación del MVP está en [SPEC.md](SPEC.md).

## Estado

Hito 1 de 5: motor con estado en disco, esquemas JSON, modo manual, fusión, agregación de la criba y cartera por regla.

## Puesta en marcha (Windows)

El entorno virtual vive fuera de la carpeta del proyecto:

```powershell
py -3.12 -m venv "$env:LOCALAPPDATA\tresia\venv"
& "$env:LOCALAPPDATA\tresia\venv\Scripts\python.exe" -m pip install jsonschema pytest
$env:PYTHONDONTWRITEBYTECODE = 1
& "$env:LOCALAPPDATA\tresia\venv\Scripts\python.exe" -m pytest -q -p no:cacheprovider
```

## Estructura

- `tresia/calculo/`: cálculos deterministas (limpieza de JSON, esquemas, fusión, agregación y cartera).
- `tresia/motor/`: estado de cada ejecución, fases con puertas del dueño, modo manual y pasos del flujo.
- `tresia/papeles.py`: compone la ficha (prompt) a partir de cada `SKILL.md`.
- `skills/`: papeles (prompts en inglés).
- `schemas/`: esquemas JSON de la salida de cada papel.
- `fixtures/caso-libanes-c4/`: caso real usado en las pruebas de aceptación.
- `tests/`: pruebas de aceptación de la sección 11 de la SPEC.
