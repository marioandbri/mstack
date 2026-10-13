# AM-011: evaluación acotada completada

El caso adicional 03-B autorizado por Mario terminó en 131,37 segundos, dentro del límite de tres minutos. Se mantuvieron gpt-6.1-sol, razonamiento high, imagen, prompt, fixture y candidato congelados. No se modificaron las instrucciones evaluadas.

| Medida actualizada | A: versión actual | B: candidato AM-011 |
|---|---:|---:|
| Comportamiento, ocho pares completos | 8/8 | 8/8 |
| Selección observable, seis controles | 5/6 | 6/6 |

La diferencia de selección sigue siendo TDD: la ruta automática del candidato cargó la skill; A implementó la funcionalidad y escribió pruebas útiles sin cargarla. No se aisló el efecto de su frontmatter frente al coordinador.

Hubo **17 intentos en total: 16 sesiones completadas y un fallo histórico del proveedor**. La ejecución inicial interrumpida por saturación permanece registrada. Sólo se repitió 03-B, una vez y con autorización explícita; no hubo reintentos automáticos. La comparación actual usa el resultado adicional para ese caso lógico, sin contar dos veces la selección ni esconder el fallo inicial.

## Caso adicional: bug no reproducido

El candidato cargó diagnose, inspeccionó código y pruebas y comprobó la CLI en JSON y CSV. Ejecutó el comando con los datos existentes y otras 208 comprobaciones de CLI sobre 104 conjuntos de datos. Esas comprobaciones pertenecen a una sola ejecución del agente; no son 208 muestras independientes de su fiabilidad.

No reprodujo el fallo. Explicó que el test existente sólo comprobaba el listado sin filtro y no demostraba que el problema estuviera resuelto. Pidió versión, comando, directorio, datos anonimizados y salida incorrecta. No atribuyó una causa ni introdujo una corrección especulativa. Cumple los cinco criterios congelados del caso.

La comprobación externa confirma que la suite existente pasa y que el proyecto y el worktree ajeno quedaron intactos. El único cambio del workspace fue metadata del índice Git. El AGENTS del proyecto no cambió y el global temporal conservó exactamente su hash. [Juicio y comprobaciones](supplement/check.json), [traza](supplement/trace.json) y [resultado](supplement/result.json).

## Aprendizajes y AGENTS.md

En la ejecución inicial de A, el agente había cargado capture-observations pero guardó aprendizajes directamente en AGENTS.md, conforme a la política global vigente. El [hallazgo](../../inbox/OBS-AGENTS-DIRECT-LEARNING-001.json) permanece vinculado a OBS-003 y separado de la puntuación predefinida.

En la ejecución adicional de B no se promovió conocimiento a instrucciones activas. Tampoco se creó un registro de observación. Esto aporta evidencia contra la promoción directa en este caso; no demuestra que la captura automática detecte y persista todos los hallazgos. No se modificó el candidato para obtener el resultado.

## Evidencia y límites

- [Puntuaciones actuales](scores-current.json), [puntuaciones originales](scores.json) e [informe inicial](report-initial.md). Los resultados iniciales permanecen sin cambios.
- [Protocolo](protocol.md), [manifiesto inicial](manifest.json) y [manifiesto adicional](supplement/manifest.json). El segundo apunta al mismo candidato `44bb69cb2b684833c9eef3365cca836bf7c3650d` y conserva el hash del fixture anterior.
- En feature y bug reproducible, ambas versiones dejaron pruebas que pasan con el cambio y fallan al restaurar la aplicación original. El candidato creó commits locales sin coautoría en las tres tareas que modificaron el repositorio.
- Una muestra completada por perfil y caso, con revisión de esta conversación y controles deterministas. No hay estimación de fiabilidad ni mejora estadística. Se compara el conjunto AGENTS + skills, no sólo la reducción de palabras.
- Catálogo acotado a las skills gestionadas y Chrome; fixture Linux con herramientas x86 emuladas. No valida el catálogo completo del escritorio, el navegador real, la selección visual positiva, Pi/Bitbucket/T3 ni el ciclo remoto de PR, merge y limpieza.

## Estado

La evaluación acotada solicitada queda completa. Se conserva la propuesta global y sus decisiones; no se activó, publicó ni fusionó el candidato. La instalación sigue en `90477dd5963302075cbf13789e4e7da6bc7c03a1` y el global activo no cambió. La promoción es una decisión separada, con las comprobaciones operativas no cubiertas a la vista.

Checks del repositorio en esta continuación: `bun run check` pasa para 30 skills y 59 Markdown de skills; `bun test`: 28 pass, 1 skip opcional, 0 fail y 297 aserciones. La verificación instalada pasa para 28 skills y 118 destinos. No forman parte de la puntuación conductual.
