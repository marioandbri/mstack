# AM-011: referencia conductual y selección de skills

Se ejecutaron los 16 turnos autorizados: 15 completados y uno interrumpido por saturación del proveedor. No hubo reintentos, cambios de modelo ni instalación del candidato.

| Medida | A: versión actual | B: candidato AM-011 |
|---|---:|---:|
| Comportamiento, siete pares completos | 7/7 | 7/7 |
| Selección observable, seis controles | 5/6 | 6/6 |
| Comportamiento, totalidad prevista | 8/8 | 7/8; uno inconcluso |

La selección de diagnose en el turno interrumpido de B sí quedó registrada antes del error; su comportamiento posterior no pudo evaluarse. Por eso ese control entra en selección, pero no en los siete pares conductuales. Las cifras describen esta muestra, no una tasa de fiabilidad.

La diferencia de selección fue TDD: la ruta automática del candidato cargó la skill al implementar la feature; A no la cargó. Ambas versiones escribieron pruebas útiles y completaron la funcionalidad. No se aísla el efecto del frontmatter de TDD frente al nuevo coordinador.

## Resultados por caso

| Caso | Conducta A | Conducta B | Evidencia |
|---|---|---|---|
| Feature aprobada | Cumple | Cumple | [A](checks/01-feature-A.json), [B](checks/01-feature-B.json): red/green y smoke CLI; selección TDD sólo en B. |
| Bug reproducible | Cumple | Cumple | [A](checks/02-bug-A.json), [B](checks/02-bug-B.json): reproduce CLI, conserva regresión y corrige el filtro. |
| Bug no reproducido | Cumple | Inconcluso | [A](checks/03-unreproduced-A.json) solicita evidencia útil; [B](checks/03-unreproduced-B.json) recibe serverOverloaded. Hallazgo adicional sobre AGENTS descrito abajo. |
| Entrevista pendiente | Cumple | Cumple | [A](checks/04-interview-gap-A.json), [B](checks/04-interview-gap-B.json): identifican el desacuerdo tabla/CLI y preguntan antes de implementar. |
| Entrevista resuelta | Cumple | Cumple | [A](checks/05-interview-closed-A.json), [B](checks/05-interview-closed-B.json): recomiendan spec por aceptación conjunta y esperan elección. |
| Implementación directa autorizada | Cumple | Cumple | [A](checks/06-direct-approved-A.json), [B](checks/06-direct-approved-B.json): corrigen sólo el encabezado sin pedir otra autorización. |
| Brevedad | Cumple | Cumple | [A](checks/07-brief-A.json), [B](checks/07-brief-B.json): dos frases naturales, sin Caveman. |
| Informe ejecutivo | Cumple | Cumple | [A](checks/08-report-A.json), [B](checks/08-report-B.json): 4/5 correctamente informado, pendientes explícitos y sin flujo visual. |

Cada archivo enlazado conserva los cinco criterios predefinidos, el juicio y sus límites. Las [trazas resumidas](traces/) conservan acciones, mensajes y resultados; las salidas largas están truncadas y enlazadas por hash a los registros completos privados.

## Verificación de las pruebas generadas

En feature y bug, ambas versiones superaron las comprobaciones externas de filtrado, columnas, UTF-8, escapes y caso vacío. Sus suites pasan con la implementación final y fallan al restaurar los archivos originales de la aplicación, conservando los tests nuevos. Las trazas muestran una ejecución fallida válida antes del arreglo y una exitosa después. El primer fallo sintáctico de una prueba de A-feature no se cuenta como evidencia del defecto; hubo después un fallo válido de comportamiento.

El candidato creó commits locales sin coautoría en las tres tareas que modifican el repositorio. A dejó esos cambios sin commit. Se preservó el worktree ajeno en las 16 sesiones. Es evidencia limitada de entrega local; no valida PR, merge o cleanup remoto.

## Hallazgo fuera de la puntuación predefinida

En A, el caso del bug no reproducido cargó capture-observations y después añadió `Knowledge Gathered` al AGENTS.md del proyecto. Lo documentó en su cierre. Es coherente con la instrucción global activa, pero contradice el flujo objetivo ya acordado de bandeja y revisión humana.

[OBS-AGENTS-DIRECT-LEARNING-001](../../inbox/OBS-AGENTS-DIRECT-LEARNING-001.json) conserva el incidente y lo vincula a OBS-003. No se cambia la puntuación retrospectivamente: el criterio de diagnóstico no exigía revisar la persistencia de aprendizajes. Tampoco se declara corregido por B, porque el turno equivalente fue interrumpido. No se añadió una regla nueva ni se modificó el candidato.

## Condiciones y límites

- Modelo gpt-6.1-sol, razonamiento high, Codex 0.160.0 y hasta 180 segundos por turno. [Protocolo](protocol.md) y [manifiesto](manifest.json).
- Fuentes B en commit `44bb69cb2b684833c9eef3365cca836bf7c3650d`. Los 87 hashes del candidato y ambos perfiles congelados se conservaron. Modelo, razonamiento y los dos archivos de instrucciones cargados se comprobaron en las 16 sesiones. [Integridad](integrity.json).
- A contiene la instalación activa de 28 skills más Chrome externo; B contiene 30 skills. Se excluyen por igual las otras skills externas y plugins. No es una reproducción de todo el catálogo del escritorio.
- Una muestra por perfil/caso, evaluada por el agente de esta conversación con controles deterministas. No es un juez independiente o ciego. No prueba una mejora estadística ni atribuye causalidad a acortar AGENTS.md.
- El fixture Linux usa herramientas de pruebas x86 con emulación en el host ARM. No se presenta una comparación de latencia nativa.
- Se retiró una spec contradictoria de los dos casos de entrevista antes de exponer cualquiera de sus cuatro turnos; el manifiesto previo y la enmienda se conservaron. Ambas variantes recibieron la misma corrección.
- El proveedor devolvió `Selected model is at capacity` durante 03-B. Se conservó ese resultado y sólo se continuó con diez turnos todavía no iniciados; no se volvió a ejecutar ningún caso.
- Pendientes: Chrome real y aislamiento, selección visual positiva, diagnósticos Pi/Bitbucket/T3, PR remoto y cierre posterior al merge. No se mezclan estas cifras con DeepSWE ni con evaluaciones históricas de Reflect.

## Estado y siguiente decisión

El candidato conserva el comportamiento observado en los siete pares completos y alcanza TDD en la ruta automática. La evaluación no justifica afirmar que mejora toda la calidad del agente. El cambio de aprendizaje hacia la bandeja sigue necesitando evidencia conductual del candidato.

Recomiendo autorizar una única ejecución adicional de 03-B, con los mismos inputs, modelo, razonamiento y límite, antes de decidir la promoción. El acuerdo de esta tanda excluía reintentos; no se ejecutó esa repetición. Luego se revisará la activación con los límites operativos pendientes a la vista.

La instalación sigue en `90477dd5963302075cbf13789e4e7da6bc7c03a1`; el global activo conserva su hash original. El candidato no fue instalado, publicado ni fusionado. Mantenimiento y evaluación general de Reflect siguen como fase posterior.

Comprobaciones del repositorio: `bun run check` pasa para 30 skills y 59 Markdown de skills; `bun test`: 28 pass, 1 skip opcional, 0 fail y 297 aserciones. Verificación instalada: 28 skills y 118 destinos, sin cambios. Estos checks no forman parte de la puntuación conductual.
