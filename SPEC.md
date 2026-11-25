# Sistema de tres IA — Especificación del MVP

Para: Claude Code en el PC del dueño (Windows). Versión 1, 25 nov 2026.
Origen: prueba manual completa (cuatro ciclos, caso «el libanés en la era de la IA»). El informe con las 20 lecciones está en `referencia/informe-tres-ia-prueba1.md`.

## 1. Qué es

Una herramienta local que exprime y valida cualquier idea, problema, documento, código o negocio con tres modelos de proveedores distintos. Primero amplía las opciones; después las valida de forma sistemática y medible, sin podarlas. Una persona (el dueño) decide en puntos fijos y nada se ejecuta ni se envía sin su aprobación.

Prioridades del dueño, en este orden:
1. Procedimiento reutilizable, sin armar estructura cada vez.
2. Interfaz sencilla que muestre el proceso, los resultados y el porqué de la propuesta final, sin recargar la pantalla.
3. Medible: cada fase deja métricas.

## 2. Alcance del MVP

Dentro:
- Motor determinista en Python que lleva el estado de una ejecución en disco y es reanudable.
- Papeles en archivos `SKILL.md` (carpeta `skills/`), con salida JSON validada con esquema.
- Tres adaptadores de modelos más un modo manual (copiar y pegar).
- Verificador fijo, fuera de la rotación.
- Interfaz web local con tarjetas de decisión.
- Reproducción del caso de prueba como prueba de aceptación (sección 11).

Fuera (fase siguiente):
- Entorno del servidor sin conexión (sí dejar la configuración preparada: mismos `SKILL.md`, otro perfil de modelos).
- Integración con Plane.
- Multiusuario, despliegue en red, autenticación.

## 3. Entorno y proveedores

- Windows, Python 3.11 o superior, entorno virtual propio. Nada de rutas Unix fijas.
- Solo `localhost`. No exponer puertos.
- Perfil `pc` (por defecto):

| Papel en la rotación | Proveedor | Cómo se llama |
|---|---|---|
| Modelo A | Claude | `claude -p` con la sesión de la suscripción, salida JSON |
| Modelo B | ChatGPT | `codex exec` con la sesión de ChatGPT |
| Modelo C | Gemini | API de pago (no la gratuita, que puede usar los datos para entrenar). Clave en variable de entorno o en el almacén de credenciales de Windows, nunca en el repositorio |
| Verificador | Qwen en el servidor del verificador | Ollama por HTTP a través de una conexión privada; si no responde, usar un modelo fijo configurable que no esté en la rotación del ciclo y avisar en pantalla |

- Modo manual por adaptador: el motor genera la ficha (prompt completo), la interfaz la muestra con botón de copiar y un cuadro para pegar la respuesta. Imprescindible como respaldo y para depurar.
- Llamar a las CLI como subprocesos con el prompt por archivo o stdin, no por argumento: en Windows los prompts largos fallan. Se puede reutilizar código de `the-llm-council` (licencia MIT, citar origen): subprocesos de CLI en Windows y validación con esquema y reintento. No usarlo como dependencia ni como marco (evaluación en la sección 4 quáter del informe).
- Limpieza de salidas: las respuestas pegadas desde la web traen artefactos (`&#x20;`, barras invertidas, comillas escapadas). Extraer el bloque JSON, limpiarlo y validarlo; si falla, reintentar una vez pidiendo solo el JSON.

## 4. Flujo (máquina de estados)

Cada paso escribe sus artefactos en la carpeta de la ejecución y no avanza sin las aprobaciones marcadas con ⛔.

1. **Ingesta.** El dueño aporta materiales y etiqueta cada uno: contexto, objeto a validar, restricción o evidencia. El contexto nunca llega a los papeles (lección 1).
2. **Encuadre.** Las 11 preguntas universales (sección 6) con sus valores por defecto. Producen la ficha del caso y las caras del problema. ⛔ El dueño confirma la ficha.
3. **Línea base.** Lista de opciones obvias escrita antes de la fase A (por el dueño o por el verificador). No se entrega a los papeles; sirve para medir novedad.
4. **Fase A, abrir opciones.** Los tres modelos en paralelo y a ciegas, papel explorador, con las técnicas obligatorias T1–T7 y las cuotas de la ficha.
5. **Verificación A.** Esquema, cuotas, cobertura de técnicas y etapas, fuentes (sección 7).
6. **Fusión.** El verificador agrupa las opciones por mecanismo; el script comprueba que cada opción esté en exactamente un grupo. Métricas: grupos, novedad frente a la línea base, solapamiento (Jaccard) y aportes únicos por explorador, grupos que dependen de IA.
7. **Criba ciega.** Los tres modelos, papel cribador, sin saber quién propuso qué. Voto fatal solo con motivo respaldado y siempre con rescate; cinco puntuaciones de 1 a 5 (criterios de la ficha); hasta 3 opciones nuevas cada uno.
8. **Agregación** (determinista). Se elimina solo con 2 de 3 votos fatales verificados. Mediana por criterio, total, orden, desacuerdos (rango ≥ 2).
9. **Cartera por regla** (lección 16). Orden por total de medianas, luego mediana de impacto, luego mediana de inclusión (o los dos criterios que la ficha marque como prioritarios). Las N primeras; si en el corte hay empate en las tres claves, entran todos los empatados; la mejor de cada etapa de la cadena que falte; las opciones nuevas que dos cribadores proponen por separado entran como combinaciones; el resto se archiva y puede volver. ⛔ El dueño puede añadir o quitar; su decisión prevalece y queda marcada como tal.
10. **Fase B, validar** (por ciclo; rotación en cuadrado latino, sección 5):
    1. Constructor: produce o corrige el entregable con ediciones mínimas; cada cambio cita lo que resuelve.
    2. Verificador: recuento, comparación con la versión anterior, fuentes, cumplimiento de las decisiones del dueño, orden temporal frente a puertas (sección 7).
    3. Atacante: hallazgos con gravedad y corrección obligatoria.
    4. Verificador sobre el ataque.
    5. Árbitro: propone qué hacer con cada hallazgo aplicando proporcionalidad (lección 17). ⛔ El dueño decide con tarjetas.
    6. Constructor aplica las disposiciones.
    7. Veredicto cruzado de los dos modelos que no construyeron.
    8. Si hay condiciones, una última pasada del constructor y verificación. ⛔ El dueño adopta o pide otro ciclo.
11. **Informe y entregable final** (por ejemplo un post): paso sencillo, fuera de los ciclos. ⛔ Aprobación antes de enviar o publicar nada.

Decisiones a mitad de proceso: opción conservadora, seguir y listarla en el informe (lección 4). Un cuestionamiento de la premisa se decide al final del ciclo (lección 5).

## 5. Papeles y rotación

- Papeles: explorador, cribador, constructor, atacante, evaluador del veredicto cruzado. Verificador y árbitro son fijos y no rotan.
- En la fase A y la criba, los tres modelos hacen el mismo papel en paralelo.
- En la fase B rotan en cuadrado latino: ciclo 1 constructor A, atacante B, evaluadores B y C; ciclo 2 constructor B, atacante C; ciclo 3 constructor C, atacante A. El constructor nunca evalúa su propia versión.
- La identidad de cada modelo se guarda aparte; la interfaz muestra «Explorador 1, 2, 3» (al dueño no le importa quién es quién).
- Cada papel se define en `skills/<papel>/SKILL.md` con su prompt en inglés y el formato JSON de salida. Los esquemas JSON (`schemas/`) se derivan de esos formatos.

## 6. Encuadre: 11 preguntas universales

1. ¿Qué es cada material: contexto, objeto a validar, restricción o evidencia?
2. ¿Qué decisión tomarás con el resultado: abrir opciones, validar o ambas?
3. ¿Qué es fijo y qué se puede cuestionar, incluida la premisa?
4. ¿Qué no se puede tocar, usar ni revelar?
5. ¿Para quién es, a quién afecta y quién podría quedar fuera?
6. ¿Qué relación tienes con el objeto y cuánto quieres exponerte?
7. ¿Cómo sabremos que está bien y qué cuenta como prueba?
8. ¿Qué es crítico y detiene el proceso, y cuánto inviertes?
9. ¿Qué tiene que cubrir sí o sí?
10. ¿Qué caras tiene el problema, qué manda en cada una y cuál obliga? (Por defecto las propone el sistema y el dueño confirma; proponer siempre la práctica real del mercado.)
11. ¿Cómo evoluciona el problema si no hacemos nada y qué valor queda entonces? (Por defecto lo explora la fase A con T7.)

Campos de la ficha: objetivo, decisión, fijo y cuestionable, prohibiciones, destinatarios y excluibles, exposición, criterios de prueba, críticos, cobertura obligatoria, caras, fuentes de verdad aceptadas (por defecto todas, cada una con su tipo), principios del dueño (por ejemplo proporcionalidad), criterios de la criba (cinco), etapas de la cadena, cuotas de la fase A, límites de longitud del entregable.

## 7. Verificador (fijo)

Partes deterministas (script, sin modelo):
- Validación de esquema y cuotas.
- Recuento propio de palabras y elementos; nunca aceptar los recuentos del modelo (lección 3).
- Comparación entre versiones: secciones, fuentes y URL perdidas; cambios declarados que no aparecen en el texto (lección 19).
- Comprobación de fuentes con internet: descargar la URL, buscar el fragmento normalizado (espacios, comillas, diacríticos) y marcar verificada, no coincide o inaccesible. Nada se marca verificado sin fragmento (lección 10). Registro de fuentes que no se pierde entre versiones.

Partes con modelo (verificador fijo):
- Extraer afirmaciones y su tipo de respaldo: 🔗 fuente con fragmento, 🧠 razonamiento con premisas, 👤 conocimiento del dueño, ⚖️ postura (lección 11). La solidez la asigna el verificador, no quien cita (lección 2).
- Revisar premisas según su tipo; el árbitro solo comprueba que la conclusión se siga.
- Orden temporal: cruzar cada puerta o permiso con el calendario y con cada actividad que debe autorizar (lección 20).
- Cumplimiento de las decisiones del dueño, que son vinculantes.
- Lo que un modelo dice sobre su propio entrenamiento es indicio débil.

## 8. Reglas del motor (de las lecciones)

- Fase A y fase B separadas; las reglas de convergencia solo valen en B (6). El conocimiento del dueño entra en las fases que cierran, nunca en las que abren (7).
- La selección cubre toda la cadena, hasta el uso real (8). Una idea con precedente falso se conserva como «propuesta sin precedente verificado» (9).
- Problemas con varias caras: el encuadre las declara, la exploración las cubre, el atacante ataca desde cada una y el informe dice en cuáles aguanta (12).
- Lo que ve el dueño nunca es un código solo: cada código nace con un nombre legible de ocho palabras como máximo y el script rechaza códigos sin nombre (13).
- Ampliar sin podar: toda crítica que tumba algo trae alternativa; lo descartado se archiva con su motivo; se mide por fase cuántas opciones entran, cuántas sobreviven y cuánta novedad hay (15).
- Proporcionalidad: si una protección no se puede cumplir de verdad, se sustituye por un aviso claro (17).
- En pilotos pequeños, validar para corregir, no para aprobar (18).

## 9. Interfaz (local, en español)

Pantallas, nada más:
1. **Ejecuciones:** lista con nombre, fase actual y si espera al dueño.
2. **Ejecución:** barra de fases arriba con su estado; debajo, el paso actual con su resultado resumido y sus métricas.
3. **Tarjetas de decisión:** cada una autosuficiente: pregunta, contexto en una o dos líneas, opciones con su consecuencia y qué pasa si no responde. Las respuestas quedan en un registro con fecha.
4. **Resultados:** tabla de opciones o grupos por nombre legible, con puntuaciones, novedad y desacuerdos; el detalle se despliega.
5. **Propuesta final y su porqué:** el entregable con cada afirmación marcada con su tipo de respaldo, enlace a la fuente y la traza de qué fase la introdujo.
6. **Modo manual:** ficha con botón de copiar y cuadro para pegar la respuesta.

Tecnología a elección de Claude Code, priorizando pocas dependencias y que funcione en Windows (por ejemplo FastAPI con HTML simple). Los prompts a los modelos van en inglés; la interfaz y los informes, en español.

## 10. Datos en disco

Una carpeta por ejecución, con todo en JSON o Markdown legible:
`run.json` (estado y configuración), `materiales/`, `ficha.json`, `linea_base.json`, `faseA/E1..E3.json`, `grupos.json`, `criba/S1..S3.json`, `ranking.json`, `cartera.json`, `faseB/ciclo_N/` (versiones, registros de cambios, ataque, veredictos, notas del verificador), `decisiones.jsonl`, `fuentes.json`, `metricas.json`, `informe.md`. Copia de cada prompt enviado y de cada respuesta bruta.

## 11. Pruebas de aceptación con el caso real

En `fixtures/caso-libanes-c4/` están las fichas y las respuestas reales del ciclo 4.
1. **Agregación de la criba:** a partir de `grupos_c4.json` y `S1..S3.json`, reproducir `ranking_c4.json` (mismas medianas, totales y orden).
2. **Cartera por regla:** con N = 10, desempate por total, impacto e inclusión, y cobertura de etapas, obtener C21, C25, C26, C10, C13, C29, C35, C04, C09, C27, C33 (empatada con C09 y C27 en las tres claves) y C16 (etapa «describir»). C03 y C01 entraron en el caso real por decisión del dueño, no por la regla: la prueba debe permitir añadirlas como decisión marcada.
3. **Fusión:** con `E1..E3.json` y `grupos_c4.json`, comprobar que las 67 opciones están en exactamente un grupo (41) y recalcular novedad (33 de 41) y Jaccard (0,27–0,33). La agrupación automática no tiene que coincidir; sí las comprobaciones.
4. **Recuento:** sobre `v42.md`, cuerpo hasta antes de `# **Annex` y anexo A–F hasta antes de `## **G.`: alrededor de 1590 y 798 palabras (método: quitar los símbolos `| * # ``, los separadores de tabla y los guiones sueltos, y contar lo que queda separado por espacios). Documentar el método en el informe.
5. **Comparación de versiones:** entre `v4_builder.txt` y `v41_builder.txt`, detectar que se perdieron todas las URL de fuentes y que el recorte declarado no se produjo.
6. **Modo manual:** recorrer criba y agregación pegando los JSON de los fixtures.
7. **Limpieza de JSON:** que acepte respuestas con artefactos de copiar y pegar.

## 12. Hitos sugeridos

1. Motor, estado en disco, esquemas y modo manual; pruebas 1–3 y 6–7.
2. Verificador determinista; pruebas 4 y 5.
3. Adaptadores de Claude, Codex y Gemini; verificador con Ollama.
4. Interfaz y tarjetas de decisión.
5. Una ejecución nueva completa con un problema sencillo elegido por el dueño.

## 13. Lo que no hay que hacer

- No inventar fuentes ni marcar nada como verificado sin fragmento.
- No mostrar al dueño códigos sin nombre.
- No enviar, publicar ni ejecutar nada fuera de la herramienta sin aprobación.
- No guardar claves en el repositorio.
- No depender de un marco de orquestación externo.
