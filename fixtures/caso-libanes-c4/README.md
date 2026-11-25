# Caso real: ciclo 4 de la prueba manual (conservación cultural del libanés hablado)

Respuestas reales de tres modelos, pegadas a mano. Sirven como datos de prueba y como ejemplo de cada fase.

| Archivo | Fase | Qué es |
|---|---|---|
| `ficha-c4-faseA-conservacion.md` | Fase A | Ficha enviada a los exploradores |
| `E1.json`, `E2.json`, `E3.json` | Fase A | Respuestas de los tres exploradores (24, 25 y 18 opciones) |
| `grupos_c4.json` | Fusión | 41 grupos hechos a mano, con nombre y si coinciden con la línea base |
| `mapa_c4.py` | Fusión | Script usado: comprueba asignación única, novedad y Jaccard |
| `ficha-c4-criba.md` | Criba | Ficha de la criba ciega |
| `S1.json`, `S2.json`, `S3.json` | Criba | Respuestas de los tres cribadores (0 votos fatales; 9 opciones nuevas) |
| `criba_c4.py`, `ranking_c4.json` | Agregación | Script y resultado esperado (medianas, totales, orden) |
| `ficha-c4-constructor.md`, `v4_builder.txt` | Fase B | Ficha y versión 4 del constructor |
| `ficha-c4-atacante.md`, `atacante_c4.json` | Fase B | Ficha y ataque (17 hallazgos, 3 añadidos) |
| `ficha-c4-constructor-v41.md`, `v41_builder.txt`, `v41_consolidada.md` | Fase B | Correcciones con decisiones del dueño; versión 4.1 (perdió las fuentes) y la versión con el registro de fuentes restituido |
| `ficha-c4-veredicto.md`, `V1.json`, `V2.json` | Fase B | Veredicto cruzado de los dos modelos que no construyeron |
| `ficha-c4-constructor-v42.md`, `v42.md` | Fase B | Última pasada y versión final verificada |

Notas:
- Algunas respuestas mezclan inglés y español: es real y el motor debe aceptarlo.
- El tercer explorador marcó como dependientes de IA opciones que no lo son, y usó T7 para una opción que no sale del escenario sin intervención: el verificador debería detectarlo.
- Los nombres de los modelos no figuran a propósito (criba ciega).
