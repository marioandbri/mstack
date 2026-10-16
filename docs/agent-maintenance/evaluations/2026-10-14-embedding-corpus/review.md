# Ejemplos y etiquetas para comparar recuperación en Reflect

El conjunto reúne 33 registros trazables a 20 fuentes del mantenimiento de mstack. Hay 26 intenciones de consulta con variantes en español e inglés, 52 consultas propuestas, cinco casos ambiguos separados y un control histórico fuera de la comparación. Los datos y etiquetas son un borrador para revisión. No se ejecutaron modelos ni se congeló un benchmark.

Los 30 antecedentes históricos mezclan cinco registros de incidente, nueve decisiones de Mario, cuatro hallazgos documentales, siete resultados de evaluación, una revisión editorial, un cierre histórico de instalación y tres pruebas sintéticas de almacenamiento. Tres de los cinco incidentes proceden de evaluaciones con fixtures; los otros dos son una corrección de esta conversación y un fallo del recolector local. Se añaden tres escenarios pedidos por Mario sobre convenciones, entrevista y worktree, todavía sin ejecutar. Sus fuentes son procedimientos y criterios de esta revisión, sin trazas de incidentes. No son 33 fricciones independientes de uso cotidiano.

## Cómo leer las etiquetas

- Grado 2. El antecedente responde directamente a la intención explícita de la consulta.
- Grado 1. Aporta contexto útil, pero no satisface por sí solo lo que se busca.
- Grado 0. No responde a esa consulta en este corpus, aunque comparta palabras o tema.
- Sin antecedente. La consulta no tiene un resultado pertinente en el conjunto preparado. No afirma ausencia en otros proyectos o sesiones.
- Pendiente. La consulta admite varias interpretaciones. Sus etiquetas propuestas no se usarán para puntuar hasta resolverla.

Las etiquetas viven fuera del texto que recibirá el modelo. Se codifica sólo text de cada antecedente; IDs, relevancia, fuentes, tipo y metadata no se añaden a la entrada del embedding. Un vecino cercano no pasa a ser un duplicado ni una nueva ocurrencia por ese resultado.

Los [antecedentes](records.json), [consultas y razones](queries.json) y [etiquetas generadas](labels.json) conservan sus IDs. Las [fuentes y extractos](sources.json) fijan los archivos revisados por hash y cada cita o JSON Pointer. Los originales sin session_id disponible mantienen ese valor desconocido. No se consultaron las sesiones completas ni credenciales.

## Catálogo de antecedentes

| ID | Antecedente | Tipo | Fuente |
|---|---|---|---|
| R01 | Aprendizaje promovido directamente a instrucciones | Incidente | S01 |
| R02 | Revisión sin aplicar perdió continuidad entre sesiones | Incidente | S02 |
| R03 | La tarea terminó, pero la exportación no era legible | Incidente | S03 |
| R04 | Documentación no distingue pruebas acotadas y runner pendiente | Hallazgo documental | S04 |
| R05 | Continuación centrada en un componente y no en el sistema completo | Incidente | S05 |
| R06 | Recolector JSON falló después de captura y consulta exitosas | Incidente | S06 |
| R07 | Investigar un bug no reproducido sin inventar una corrección | Resultado de evaluación | S07 |
| R08 | Corrección acotada de guardado y reanudación | Resultado de evaluación | S08 |
| R09 | La excepción explícita de sólo chat evita escrituras | Resultado de evaluación | S08 |
| R10 | El perfil B completado no promovió aprendizajes y tampoco capturó | Resultado de evaluación | S07 |
| R11 | Selección de una skill cambió sin mejorar tareas ya correctas | Resultado de evaluación | S03 |
| R12 | Captura automática y revisión solicitada antes de integrar | Decisión de Mario | S09 |
| R13 | Resolver la selección en la propia skill | Decisión de Mario | S09 |
| R14 | Avanzar dentro del alcance aprobado y conservar autorización | Decisión de Mario | S09 |
| R15 | Cerrar la entrevista por aceptación resuelta, no por ruta rápida | Decisión de Mario | S09 |
| R16 | Regresión fiel y elección del nivel de prueba | Decisión de Mario | S09 |
| R17 | Reparar regresiones propias y reportar fallos independientes | Decisión de Mario | S09 |
| R18 | Worktree, commits, evidencia y merge remoto por Mario | Decisión de Mario | S09 |
| R19 | Ajustes temporales y límite para persistencia global | Decisión de Mario | S09 |
| R20 | Brevedad natural y caveman sólo explícito | Decisión de Mario | S09 |
| R21 | Acortar el global preservando condiciones no prueba rendimiento | Revisión editorial | S10 |
| R22 | Declaración, instalación, exposición y carga son evidencias distintas | Hallazgo documental | S11 |
| R23 | Captura y Reflect comparten tema y tienen entradas distintas | Hallazgo documental | S11 |
| R24 | Entrevistas parecidas no demuestran competencia perjudicial | Hallazgo documental | S11 |
| R25 | Instalación verificada y reversión todavía sin ensayo completo | Instalación histórica | S12 |
| R26 | Reintento simultáneo nativo duplicó filas en LanceDB | Prueba sintética de base | S13 |
| R27 | SQLite conserva originales y publica el índice en transacción | Prueba sintética de base | S14 |
| R28 | Chroma genera embeddings antes de persistir documentos | Prueba sintética de base | S15 |
| R29 | MiniLM recuperó antecedentes con límites en español | Resultado de evaluación | S16 |
| R30 | Selección y tarea correcta se calificaron por separado | Resultado de evaluación | S07 |
| R31 | Omitir la skill de convenciones y distinguir cumplimiento efectivo | Escenario sin ejecutar | S17 |
| R32 | Saltarse el cierre de brechas antes de preparar implementación | Escenario sin ejecutar | S18 |
| R33 | Cambiar el checkout compartido sin worktree propio | Escenario sin ejecutar | S19 |

Las fuentes S02, S03, S04 y S08 sólo están en el checkout canónico de investigación y se leyeron sin modificarlas. Las otras proceden del worktree propio. Se preservaron copias congeladas privadas de las 20 fuentes; el paquete público contiene los extractos mínimos para comprobar las etiquetas sin copiar directorios históricos completos. S20 conserva los [comentarios de Mario en esta revisión](review-feedback.json), sin convertirlos en instrucciones activas ni en aprobación de todas las etiquetas.

## Consultas con etiquetas propuestas

Cada fila tiene una variante inglesa equivalente en queries.json. Los antecedentes están redactados en español con sus nombres técnicos originales; las consultas inglesas prueban recuperación entre idiomas sobre esos mismos textos. Son ejemplos redactados para la prueba a partir de evidencia existente; no se presentan como nuevas preguntas naturales de Mario. Las traducciones del mismo caso tampoco son muestras independientes del problema.

| Caso | Consulta en español | Directo, grado 2 | Contexto, grado 1 | Negativos cercanos, grado 0 |
|---|---|---|---|---|
| C01 | Busca un caso donde el agente guardó lo aprendido en instrucciones activas sin pasar por revisión humana. | R01 | R12, R10 | R02, R06 |
| C02 | La revisión quedó sólo en la conversación y al retomar faltaban las respuestas. ¿Hay un antecedente documentado? | R02 | R08 | R09, R06 |
| C03 | Encuentra la comprobación donde otra sesión recuperó decisiones anteriores y la propuesta sin volver a preguntar. | R08 | R02 | R09, R25 |
| C04 | La tarea evaluada terminó, pero el recolector no pudo leer las exportaciones ni completar sus hashes por permisos. Busca ese incidente. | R03 | R04 | R06, R08 |
| C05 | El modelo ya respondió y el documento quedó en la base, pero construir el informe falló porque la configuración contenía un objeto no serializable. | R06 | R28 | R03, R02 |
| C06 | El manual llama pendientes a todas las pruebas aunque ya hay comprobaciones acotadas y resultados. Busca el hallazgo que distingue esos estados. | R04 | R08, R03 | R21, R22 |
| C07 | ¿Qué decidimos sobre continuar un encargo ya autorizado sin pedir otra vez la misma aprobación? | R14 | R17, R19 | R18, R15 |
| C08 | Busca el criterio acordado para reproducir un bug fielmente sin exigir siempre una prueba de punta a punta. | R16 | R07 | R30, R20 |
| C09 | La skill está disponible, pero no se selecciona para su tarea. ¿Dónde acordamos corregir su activación en lugar de añadir un selector al global? | R13 | R11, R22 | R23, R24 |
| C10 | ¿Qué evidencia confirma la instalación pero deja pendiente ensayar la reversión completa? | R25 | R22 | R08, R27 |
| C11 | Busca la prueba donde dos reintentos simultáneos de la misma captura duplicaron filas en LanceDB y el bloqueo del adaptador evitó el duplicado. | R26 | R27 | R02, R23 |
| C12 | Busca la prueba que muestra que fallar al generar el embedding impide guardar un documento nuevo en el flujo automático de Chroma. | R28 | R27 | R06, R03 |
| C13 | ¿Qué resultados tenemos para recuperar antecedentes en español con MiniLM y cuáles son sus límites? | R29 | R28 | R27, R30 |
| C14 | ¿Qué auditoría explica por qué registrar una fricción y abrir una revisión son responsabilidades distintas aunque compartan recursos? | R23 | R12 | R24, R13 |
| C15 | Busca la corrección donde el usuario tuvo que recuperar el alcance del sistema completo porque el agente se centró en un componente opcional de Reflect. | R05 | R14 | R13, R24 |
| C16 | Busca en el proyecto control-proyecto-ausente una observación sobre permisos repetidos. | Ninguno | Ninguno | Ninguno |
| C17 | Encuentra un incidente confirmado en que un agente haya subido una clave secreta de API a Git. | Ninguno | Ninguno | R01, R18, R19 |
| C18 | Busca un incidente registrado donde se calculó mal el IVA de una factura exportada a CSV. | Ninguno | Ninguno | R11, R17 |
| C19 | Busca el escenario preparado donde el agente empieza a modificar el repositorio sin usar la skill disponible para cargar convenciones ni leer AGENTS y documentación aplicable. | R31 | R22, R13 | R32, R33 |
| C20 | Busca el control preparado que no abre la skill de convenciones, pero sí lee AGENTS y los documentos rectores y resuelve las reglas aplicables antes de editar. | R31 | R22, R30 | R32, R33 |
| C21 | Busca el escenario preparado donde una petición no trivial deja alcance y aceptación abiertos y el agente redacta tickets sin investigar ni hacer entrevista para cerrar esas brechas. | R32 | R15, R14 | R31, R33 |
| C22 | Busca el control preparado donde el agente continúa desde una spec aprobada con requisitos cerrados, documentación suficiente y sin desviación de alcance, y no repite una entrevista innecesaria. | R32 | R15, R14 | R31, R33 |
| C23 | Busca el escenario preparado donde se hacen cambios en el checkout compartido sin preparar ni reutilizar un worktree propio configurado. | R33 | R18 | R31, R32 |
| C24 | Busca el control preparado donde se verifica y reutiliza un worktree propio ya configurado al reanudar, sin crear otro worktree. | R33 | R18 | R31, R32 |
| C25 | Busca el control preparado donde se pidió implementar una spec aprobada, pero aparece una brecha de dominio sin respaldo en los documentos y el agente pregunta por la decisión pendiente tras investigar. | R32 | R15, R14 | R31, R33 |
| C26 | Busca el control preparado donde se explica qué es una convención de código, fuera de un repositorio y sin análisis de arquitectura, implementación ni revisión, y no se selecciona la skill de carga de convenciones. | R31 | R22, R13 | R32, R33 |

Para la intención explícita, los demás antecedentes elegibles se proponen con grado 0. Las razones y negativos cercanos están en queries.json. Son juicios del preparador, pendientes de revisión, no etiquetas aprobadas por el usuario ni un dictamen independiente.

C16 tiene cero candidatos por filtro de proyecto. Se informará aparte de C17 y C18, que mantienen candidatos pero no tienen un incidente relevante. Estos últimos permiten medir asociaciones incorrectas o abstención; un KNN que siempre devuelve vecinos necesita distinguir candidato de antecedente confirmado.

## Omisiones de procedimiento y controles

R31, R32 y R33 contienen los escenarios solicitados. C19 a C26 preparan omisiones y controles cercanos. Las etiquetas siguientes describen el comportamiento esperado en una futura ejecución. Se conservan fuera del texto del embedding y no sustituyen los grados de relevancia de recuperación.

| Caso | Etiqueta de comportamiento propuesta | Criterio esperado si se ejecuta |
|---|---|---|
| C19 | conventions-skill-and-context-omitted | La traza completa del escenario muestra que se omitieron tanto la skill aplicable como sus documentos rectores antes de cambiar el repositorio. |
| C20 | conventions-context-loaded-without-skill | La selección de la skill falta, pero la traza confirma carga y resolución de los documentos rectores. No se etiqueta como omisión de convenciones ni se supone un resultado incorrecto. |
| C21 | material-gaps-left-unresolved | Quedaban decisiones materiales al preparar tickets; no se resolvieron mediante investigación ni entrevista. |
| C22 | interview-not-required | La spec aprobada ya cierra los requisitos materiales; continuar sin repetir entrevista respeta el encargo. |
| C23 | owned-worktree-not-prepared | Se hicieron cambios del repositorio en un checkout compartido, sin worktree propio preparado o reutilizado. |
| C24 | existing-owned-worktree-reused | Se verificó y reutilizó un worktree propio configurado. No crear otro no constituye omisión. |
| C25 | material-clarification-after-approved-artifact | La implementación solicitada desde un artefacto aprobado descubre una brecha material de dominio, desviación de alcance o falta de respaldo documental. Tras investigar, preguntar por la decisión pendiente es válido. |
| C26 | conventions-skill-not-applicable | La tarea no encaja con el trigger de la skill. Su disponibilidad no obliga a seleccionarla para una explicación general fuera de un repositorio. |

El control C20 conserva una falta de selección de la skill, aunque demuestra consulta efectiva de convenciones. C26 omite la selección porque la tarea no encaja con su trigger. C22 evita repetir una entrevista con requisitos cerrados y documentación suficiente. C25 permite preguntar por una brecha material nueva después de investigar, aun con spec aprobada e implementación solicitada. C24 permite reutilizar el worktree propio preparado. Una tarea de sólo lectura tampoco exige crear un worktree para cambios.

Para registrar una omisión real hay que comprobar que la tarea encaja con el trigger, el procedimiento estaba disponible y se omitió en la traza del trabajo. Una traza incompleta deja la clasificación indeterminada. Las fuentes S17, S18 y S19 prueban procedimientos y S20 conserva criterios de revisión; no demuestran que ocurrieran estas omisiones. La recuperación semántica puede encontrar el escenario, pero no prueba por sí sola un fallo ni decide corregir instrucciones.

## Casos que necesitan revisión

| Caso | Consulta ambigua | Propuesta para revisar | Información o decisión pendiente |
|---|---|---|---|
| V01 | Reflect volvió a preguntar lo que ya habíamos decidido. | Priorizar R02 como incidente y presentar R08 y R14 como contexto con funciones distintas. No asumir la causa de una nueva fricción por similitud. | ¿Buscamos primero el fallo de continuidad, la corrección evaluada o el criterio de preservar autorizaciones? |
| V02 | Una skill instalada no apareció en la sesión. | Comprobar catálogo, disponibilidad, exposición, compatibilidad del contexto con el trigger y selección. R22 aporta la distinción de evidencias; R31 prepara los controles de aplicabilidad. No atribuir una omisión a una skill que no aplicaba. | ¿Qué tarea y contexto tenía la sesión, encajaban con el trigger y qué evidencia hay de exposición y carga? |
| V03 | El bootstrap no guardó el resultado. | Dividirla por fase antes de fijar un único antecedente esperado. C05 y C12 ya muestran las versiones explícitas. | ¿Dividimos esta consulta según se refiera al documento en la base o al informe exportado? |
| V04 | El agente me interrumpe con preguntas innecesarias antes de implementar. | Una spec o ticket aprobado con implementación solicitada permite preguntas para nuevas brechas materiales. Investigar primero lo que responden los documentos. C22 prepara continuar sin brechas y C25 preguntar por una brecha nueva; no repetir autorizaciones conservadas. | ¿La pregunta repite una autorización o cierra una brecha material de dominio, desviación de alcance o falta de respaldo documental después de investigar? |
| V06 | Busca un antecedente de un agente consumiendo demasiada GPU durante tareas de Reflect. | No hay un incidente de GPU excesiva en este corpus. R29 describe una prueba de MiniLM y R21 una edición de instrucciones; ninguno satisface la búsqueda del incidente. Si se muestran, deben figurar como contexto y no contar como aciertos. | ¿Además de indicar ausencia del incidente, resulta útil mostrar la prueba de MiniLM como contexto separado? |

Los cinco casos conservan grades=null e include_in_scoring=false en labels.json. Los criterios de V02 y V04 se aclararon con Mario, pero sus consultas originales siguen sin describir el contexto suficiente para una etiqueta única. C19/C26 y C22/C25 preparan los contrastes explícitos. V03 aún requiere distinguir fases.

V05 es un control histórico de cobertura, excluido de las ambigüedades activas y de puntuación. V05 también conserva grades=null e include_in_scoring=false, en excluded_from_comparison. No se ha aportado evidencia nueva de captura completa.

V06 pregunta por un incidente de consumo excesivo de GPU. R29 sólo describe una prueba de MiniLM; R21 describe una edición de instrucciones. Ninguno confirma ese incidente. La respuesta propuesta indica ausencia en este corpus; falta revisar si se muestra alguno como contexto separado o se omite.

## Comprobaciones antes de comparar modelos

Primero se revisan las etiquetas y se conserva una versión congelada. La ejecución posterior usará el mismo texto, ámbitos y expectativas para cada modelo, con FTS5 como referencia y comparación híbrida separada. El modelo de producción y los dos candidatos adicionales no se eligen mediante este borrador.

La medición propuesta distingue recuperación de antecedentes directos en top 3 y top 5, contexto útil, falsas asociaciones en consultas sin antecedente y fugas de ámbito. Se separan idiomas, tipos de fuente, episodios y controles sin candidatos. Latencia y memoria se medirán después, en un protocolo local común. No se transforma el total de traducciones, controles o decisiones de una misma sesión en una tasa de fiabilidad de incidentes.

V05 impide convertir una puntuación histórica en prueba de captura completa. R02 y R08 conservan fallo y seguimiento; R01 y R10 conservan perfiles e intentos distintos; R06 y R28 distinguen publicación de evidencia de persistencia anterior al modelo. R25 registra el cierre del 13 de octubre, sin presentarlo como identificación de la instalación activa actual.

## Reproducción y verificación

records.json y queries.json son entradas curadas. prepare.py genera fuentes, extractos, etiquetas, este documento y manifest.json. Los generados se actualizan mediante ese script, sin editarlos manualmente. Las fuentes congeladas completas permanecen fuera de Git, en mstack-tasks/maintenance-laya/embedding-corpus-evidence/draft-02/sources bajo el Git common directory canónico. Se conserva la versión anterior en draft-01.

Con uv 0.10.11 y el entorno Python 3.13.2 ya bloqueado, desde esta carpeta:

```fish
env PYTHONDONTWRITEBYTECODE=1 uv run --locked --project ../2026-10-14-chroma python prepare.py --canonical-root /ruta/repositorio/canonico --private-snapshots /ruta/privada/fuentes
env PYTHONDONTWRITEBYTECODE=1 uv run --locked --project ../2026-10-14-chroma python verify.py --private-snapshots /ruta/privada/fuentes
```

La preparación usa sólo biblioteca estándar y archivos locales. Si una fuente congelada difiere de la fuente actual, se usa otro directorio de snapshots y se revisa la diferencia. Los hashes prueban identidad de fuentes y estructura; no pueden decidir por sí solos la pertinencia semántica de cada etiqueta. La [verificación](verification.json) documenta los checks realizados y ese límite.
