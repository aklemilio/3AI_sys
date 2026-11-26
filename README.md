# 3AI_sys — sistema de tres IA

Herramienta local para ampliar y validar ideas, documentos, código o negocios con tres modelos de proveedores distintos. Primero abre opciones y después las valida de forma medible. Motor determinista en Python, papeles en `skills/*/SKILL.md` y decisiones humanas en puntos fijos.

La especificación del MVP está en [SPEC.md](SPEC.md).

## Estado

- Hito 1 de 5: motor con estado en disco, esquemas JSON, modo manual, fusión, agregación de la criba y cartera por regla.
- Hito 2 de 5: verificador determinista: recuento propio, comparación entre versiones y comprobación y registro de fuentes.
- Hito 3 de 5 (en curso): adaptadores de Claude y Codex (CLI), Gemini (API de pago) y Ollama (verificador), rotación en cuadrado latino y verificador con respaldo. Claude, Codex, Gemini y el verificador del servidor probados con una llamada real.

- Orquestación del flujo completo (`tresia/motor/flujo.py`): ingesta, encuadre, línea base, fase A, verificación A, fusión, criba, agregación, cartera, ciclo de la fase B e informe, en modo automático o manual.
- Troceo del verificador del servidor (`tresia/motor/troceo.py`): las tareas que no caben en su contexto fijo de 8192 tokens se resuelven por partes (claims y compliance por secciones; timeline con una tabla intermedia; arbitrate por lotes; merge por etapas y luego entre etapas). Si un trozo falla, se usa el respaldo con la ficha completa. El modo manual no cambia.

### Uso desde Python (hasta que llegue la interfaz)

```python
from tresia import perfiles
from tresia.motor import Ejecucion, encuadre, fase_b, pasos
from tresia.motor.flujo import avanzar
from tresia.motor.llamadas import Recursos

run = Ejecucion.crear("ejecuciones", "Mi caso")
recursos = Recursos.desde_perfil(perfiles.cargar("pc"))   # o None para modo manual
encuadre.ingestar(run, "Propuesta", "objeto", ruta="propuesta.md")
encuadre.cerrar_ingesta(run)
encuadre.responder_encuadre(run, {"objetivo": "..."})
run.aprobar()                                             # ⛔ ficha
encuadre.registrar_linea_base(run, ["opción obvia 1", "opción obvia 2"])
estado = avanzar(run, recursos)                           # se detiene en cada ⛔
```

### Modelos

El perfil `perfiles/pc.toml` define los modelos A, B y C, el verificador y su respaldo. Los valores locales (dirección del servidor, modelos concretos, rutas) van en `perfiles/pc.local.toml`, que no se sube al repositorio. La clave de Gemini se lee de la variable de entorno `GEMINI_API_KEY` o del almacén de credenciales de Windows; nunca se guarda en disco.

### Método de recuento de palabras

Se sustituyen por espacios los símbolos `|`, `*`, `#` y la comilla invertida, y se separa el texto por espacios. Se descartan las piezas formadas solo por guiones ASCII (viñetas y separadores de tabla). Las rayas tipográficas (`—`, `–`) sí cuentan como palabra. Con este método, `fixtures/caso-libanes-c4/v42.md` da 1590 palabras de cuerpo y 798 de anexo (A–F).

## Puesta en marcha (Windows)

El entorno virtual vive fuera de la carpeta del proyecto:

```powershell
py -3.12 -m venv "$env:LOCALAPPDATA\tresia\venv"
& "$env:LOCALAPPDATA\tresia\venv\Scripts\python.exe" -m pip install jsonschema truststore pytest
$env:PYTHONDONTWRITEBYTECODE = 1
& "$env:LOCALAPPDATA\tresia\venv\Scripts\python.exe" -m pytest -q -p no:cacheprovider
```

## Estructura

- `tresia/calculo/`: cálculos deterministas (limpieza de JSON, esquemas, fusión, agregación, cartera, recuento, versiones y fuentes).
- `tresia/motor/`: estado de cada ejecución, fases con puertas del dueño, modo manual, pasos del flujo y verificador determinista.
- `tresia/papeles.py`: compone la ficha (prompt) a partir de cada `SKILL.md`.
- `skills/`: papeles (prompts en inglés).
- `schemas/`: esquemas JSON de la salida de cada papel.
- `fixtures/caso-libanes-c4/`: caso real usado en las pruebas de aceptación.
- `tests/`: pruebas de aceptación de la sección 11 de la SPEC.
