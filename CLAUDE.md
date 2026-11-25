# Instrucciones para Claude Code — MVP del sistema de tres IA

Trabajas en el PC del dueño (Windows), no en el servidor del verificador.

1. Lee `SPEC.md` completo antes de proponer nada. Es la fuente de verdad del MVP.
2. Lee los papeles en `skills/*/SKILL.md`. Son los prompts que usó la prueba manual, ya generalizados. Puedes ajustar redacción; no cambies sus reglas sin preguntar.
3. Los casos de prueba reales están en `fixtures/caso-libanes-c4/` (ver su README). Las pruebas de aceptación de la sección 11 de `SPEC.md` se hacen con ellos.
4. El contexto completo del diseño y las 20 lecciones están en `referencia/informe-tres-ia-prueba1.md`. Consúltalo cuando una regla de `SPEC.md` no esté clara.
5. Antes de escribir código, propón: estructura del repositorio, dependencias (pocas, que funcionen en Windows) y el plan por hitos de la sección 12. Espera la aprobación del dueño.
6. No instales nada global ni toques la configuración del sistema sin avisar. Entorno virtual propio.
7. Las claves (Gemini) nunca van al repositorio.
8. Interfaz, mensajes e informes en español neutro. Prompts a los modelos en inglés.
9. Al terminar cada hito, resume qué hiciste, qué pruebas pasan y qué queda, en pocas líneas.
