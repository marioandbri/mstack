# AM-014: inventario inicial y entregas pendientes

Esta continuación de [AM-014](AM-014-maintenance-discovery.md) concreta la auditoría proactiva y la aceptación propuesta del sistema. Es descubrimiento guardado, no una spec aprobada, una revisión de preferencias globales ni una implementación. Laya queda fuera por decisión de Mario del 13 de octubre de 2026.

## Evidencia y cobertura

El [snapshot](AM-014-inventory.json) fija las fuentes de esta inspección mediante SHA-256. Parte del worktree propio en `be50bafe98819c0e9224e408bcef58d4252854ca`; el recibo activo sigue en `3b2789839c27ed90709c88758761ab59f1ebd1ff`.

| Capa | Comprobación de esta sesión | Límite |
|---|---|---|
| Declaración | Metadata de las 30 skills de skills.json y hashes de sus 77 archivos. | Un hash no acredita revisión semántica de todo el cuerpo. |
| Instalación | 120 entrypoints presentes en Agents, Claude, Codex y Pi. Los entrypoints de Codex coinciden con la fuente. | Presencia y contenido no prueban carga ni ejecución. La verificación del instalador cubre el resto de destinos. |
| Global | La fuente y el global activo tienen SHA-256 `e2ea594f4b122950d5299652a6a591d046a055ef8504f106512547e744b25b12`. Codex resuelve al global de Agents. | Se comprueba identidad; no se reabre la revisión aceptada. |
| Catálogo del turno | El contexto de esta sesión expone metadata de 23 skills gestionadas. | No equivale al catálogo de otros entornos ni a las skills ejecutadas. |
| Referencias | 57 enlaces relativos Markdown comprobados, ninguno roto. | No comprueba anchors, rutas dentro de bloques de código, referencias dinámicas ni herramientas disponibles. |
| Externas | Muestra de metadata de skill-creator, frontend-design, vercel-react-best-practices y react-doctor. | No es cobertura de todas las skills externas o de plugins. No se importaron ni editaron. |
| Semántica | Contratos de Reflect, captura, clasificación, registros, revisión de instrucciones, autoría y evaluación; flujo de entrega y descubrimiento. | Los demás cuerpos no reciben un dictamen por haber inventariado sus archivos. |
| Comportamiento | Se consultaron los reportes históricos de apoyo y persistencia de Reflect. Cero llamadas nuevas a modelos. | No se reprodujo todavía el defecto del runner ni se ensayaron nuevas selecciones. |

Las siete skills gestionadas sin metadata expuesta en este turno son implement, lavish, reflect, to-spec, to-tickets, visual-companion y wayfinder. Sus fuentes existen. Sus controles de invocación son evidencia pertinente, pero esta inspección no establece la causa de la ausencia ni que sea imposible invocarlas explícitamente. Las lecturas de fuentes realizadas para investigar el sistema tampoco prueban que su workflow se ejecutó.

No se consultaron credenciales ni conversaciones ajenas. El snapshot registra rutas saneadas, hashes y metadata. Las fuentes históricas que sólo existen en el checkout canónico quedan identificadas por raíz y hash; no se copiaron directorios de investigación.

## Hallazgos y operaciones candidatas

Cada operación es una recomendación pendiente. Conservar el contenido actual sigue siendo una alternativa. Los riesgos textuales no se presentan como fallos conductuales reproducidos.

| ID | Fuente y evidencia | Impacto y límite | Operación propuesta |
|---|---|---|---|
| I-01 | [Captura](../../../skills/capture-observations/SKILL.md) y [Reflect](../../../skills/reflect/SKILL.md) separan registro durante trabajo y revisión solicitada. | Comparten recursos por contrato. La coincidencia temática no justifica fusionarlos. | KEEP. Usar este par como control contra falsos duplicados. |
| I-02 | [records.md](../../../skills/reflect/references/records.md) exige preservar originales y cambios concurrentes, pero deja el sidecar y adaptador pendientes. | Releer antes de escribir no excluye una carrera entre escritores. Es un riesgo del mecanismo, sin nueva pérdida observada en esta sesión. | MECHANIZE la persistencia y ADD anotaciones versionadas. Mantener esquemas actuales y captura sin clasificador. |
| I-03 | [failure-evaluation.md](../../../skills/reflect/references/failure-evaluation.md) y records.md describen runner y casos pendientes; los reportes del 8 de octubre contienen ejecuciones acotadas. | Puede confundirse cobertura pendiente con ausencia total de evidencia. Ya existe OBS-REFLECT-EVALUATION-DOCS-001; no se crea otra ocurrencia. | MOVE el estado cambiante a un índice de evidencia y enlazarlo desde el procedimiento. Revisar la redacción exacta con esa entrega. |
| I-04 | El reporte histórico de apoyos documenta exportaciones ilegibles y recuperación manual de resultados. El seguimiento de persistencia excluye ese recorrido. | Bloquea declarar fiable la recogida desatendida. Causa y regresión requieren reproducción; no basta repetir el smoke que evitó el recorrido. | MECHANIZE la recogida verificable en un runner reutilizable, con un caso de fallo determinista antes de nuevas llamadas. |
| I-05 | skills.json, el recibo y el catálogo del turno muestran capas distintas de disponibilidad. | Confundir instalado con cargado puede atribuir al texto un fallo de descubrimiento. La diferencia observada no prueba un defecto del harness. | ADD un inventario por entorno con evidencia separada de declaración, exposición, lectura y ejecución. |
| I-06 | [grill-me](../../../skills/grill-me/SKILL.md) y [grill-with-docs](../../../skills/grill-with-docs/SKILL.md) comparten entrevista; el segundo añade contexto y cierre de ingeniería. [Skill support](../../../skills/reflect/references/skill-support.md) ya distingue autoría gestionada de skill-creator. | Hay solicitudes potencialmente ambiguas, pero no resultados que demuestren competencia perjudicial. | KEEP provisional. Preparar pruebas que distingan responsabilidades antes de recomendar MERGE, SPLIT o REMOVE. |
| I-07 | [AM-013](AM-013-installation.md) acredita instalación y conserva rollback, pero declara que no ejecutó la reversión del cierre. | Un recibo estructural no demuestra el ciclo conductual completo. La transferencia externa de Chrome tiene un paso adicional. | ADD un ensayo aislado de promoción y reversión con los recibos existentes y comprobación conductual pertinente. |

No hay evidencia en esta inspección para recomendar REMOVE, MERGE o SPLIT. El futuro auditor debe admitir esas operaciones sin convertirlas en cuotas. La vigencia depende de fuentes que reemplazan o contradicen contenido; ni antigüedad ni ausencia de uso observado bastan para retirarlo.

## Casos que distinguen responsabilidades

Son casos preparados, no ejecutados. Cada ejecución deberá conservar catálogo, versión, controles, lecturas observables y resultado. La selección y la corrección de la tarea se califican por separado.

| Frontera | Positivo | Negativo cercano o complemento | Aceptación propuesta |
|---|---|---|---|
| Captura y Reflect | Durante una tarea, el usuario corrige una acción y pide conservar la fricción. | Se discute el diseño de Reflect o se registra una observación sin pedir revisión. | Guarda evidencia y vuelve a la tarea; no inicia entrevista ni promoción. Una revisión explícita sí recupera las decisiones guardadas. |
| Entrevistas | Hay requisitos materiales pendientes antes de preparar una entrega del repositorio. | Hay una spec aprobada y una orden de ejecutarla; o se pide una entrevista personal sin proyecto. | No reabre decisiones aprobadas. Distingue la entrevista de ingeniería del propósito general de grill-me. |
| Autoría | Se pide crear una skill; otro caso pide actualizar una existente. | Sólo se pide leer o explicar una skill. | Resuelve un propietario con cobertura suficiente, reutiliza respuestas y no combina manuales ni edita por una simple explicación. |
| Diagnóstico y TDD | Se reporta un bug con un síntoma reproducible. | Se pide una capacidad nueva sin fallo reportado. | Diagnóstico conserva reproducción fiel; TDD cubre comportamiento nuevo. Usar ambos puede ser correcto y no cuenta como competencia por sí solo. |
| Frontend y comprobadores | Se autoriza construir una interfaz React. | Se pide analizar un texto que menciona React. | Diseño, rendimiento y comprobación pueden ser complementarios; la mención textual sola no exige implementar ni ejecutar comprobadores. |

## Entregas con aceptación propuesta

Recomiendo tickets locales con dependencias. Cada entrega produce un resultado utilizable y verificable; ninguna requiere incorporar Laya. Esta tabla concreta la recomendación, pero no publica tickets ni autoriza implementación.

| Entrega | Resultado observable | Aceptación y dependencias |
|---|---|---|
| E1. Inventario y auditoría solicitada | Una petición de auditar el conjunto produce fuentes versionadas, cobertura, hallazgos y opciones de conservar. Reutiliza validate.ts y la verificación del instalador. | Fixtures con referencia rota, instalación distinta, fuente inaccesible, regla reemplazada y duplicación aparente de distinto ámbito. Ninguna ausencia se presenta como prueba de desuso; no cambia instrucciones activas. Este snapshot es evidencia exploratoria, no el producto terminado. |
| E2. Registros y recuperación | Captura guarda el original; un proveedor añade una anotación aparte; una sesión posterior recupera evidencia y decisiones. | Escritores concurrentes no pierden registros, IDs duplicados no sobrescriben, fallo entre original e índice permite reconstrucción, proveedor ausente o inválido deja captura pendiente y reclasificar conserva historia. Define el esquema nuevo sin modificar incompatiblemente los actuales. Puede empezar con observaciones existentes sin esperar E1. |
| E3. Runner y casos reales | Ejecuta un caso aislado y devuelve trazas legibles, resultado y estado de infraestructura sin reparación manual. | Reproduce primero la exportación defectuosa y prueba su corrección sin llamadas al modelo. Cubrir archivo ilegible, salida parcial, proceso interrumpido y resultados ausentes; conservar el intento original y cualquier recuperación. Reutiliza transporte y protección de credenciales existentes. No depende de E2 para la regresión determinista. |
| E4. Comparación de intervenciones | Para un incidente seleccionado, contrasta el cambio pertinente en AGENTS, skill o check con baseline y opción de no cambiar. | Depende de E3; toma casos de E1/E2 cuando corresponda. Fijar fuentes, modelo, razonamiento, presupuesto, rúbrica y negativos antes de ejecutar. Reportar conducta, intervención humana, acciones innecesarias e infraestructura por separado. Tokens y tiempo son secundarios. No es la comparación de Laya diferida. |
| E5. Promoción y reversión | Un candidato aceptado atraviesa el instalador existente, comprobación posterior y reversión ensayada. | Depende de evidencia pertinente de E4 o de aceptación explícita de una preferencia sin hipótesis de rendimiento. Ensayar primero en destinos aislados; comprobar hashes, recibos, detección de drift, configuración ajena preservada y conducta afectada. Despliegue real sólo con la autorización correspondiente. |

El inventario puede ser una biblioteca o comando del repo y la auditoría semántica un procedimiento de Reflect. No se ha demostrado necesidad de otra skill, servicio, base de datos o repositorio. La automatización programada, el agregador entre proyectos y la integración de proveedores externos siguen fuera de esta fase.

La revisión de [mstack_fs.py](../../../install/mstack_fs.py) encuentra escritura mediante archivo temporal, fsync, reemplazo y bloqueo del instalador. Son mecanismos a evaluar para reutilización, no un adaptador de observaciones ya terminado. El reemplazo existente permite sobrescribir: por sí solo no satisface creación exclusiva ni coordinación entre registro e índice.

El [helper de local-env](../../../skills/local-env/scripts/state.mjs) también implementa bloqueo y control de revisión para impedir escrituras obsoletas, con pruebas concurrentes existentes. E2 debe revisar ambos precedentes antes de crear mecanismos nuevos, manteniendo sus contratos de instalación y entorno separados del contrato de observaciones.

## Base y siguiente decisión

La comprobación remota mantiene el PR anterior #2 abierto, en borrador y sin merge. Su rama está en `e2dd80e`; main remoto está en `6630d2f`. La investigación propia conserva sus dos commits posteriores y no cambia esa base. Antes de publicar una implementación habrá que preparar su dependencia explícita o actualizarla tras el merge, conservando los commits de investigación. No se añade esta fase silenciosamente al PR anterior.

Mario eligió después preparar una spec, revisarla y sólo entonces dividirla en tickets. El [borrador AM-015](AM-015-agent-maintenance.spec.md) conserva las capacidades, exclusiones y criterios de esta investigación; reemplaza la recomendación de pasar directamente a tickets. No quedan preguntas sobre el global aceptado, el descarte de Laya ni la inclusión de auditoría proactiva. Los límites y presupuesto de ejecuciones con modelos se cerrarán para cada experimento concreto; un presupuesto histórico no se reutiliza.

## Verificación de este avance

Con Bun 1.3.14, `bun run check` pasó para 30 skills y 59 Markdown; `bun test` terminó con 28 pass, 1 skip opcional de Portless, 0 fail y 297 aserciones. `fish install/verify.fish` confirmó el commit activo, 30 skills y 126 destinos. El control adicional del snapshot contrasta hashes de fuentes, entrypoints de los cuatro destinos, muestra externa y enlaces de los dos documentos. `git diff --check` pasó.

Son comprobaciones de este avance documental y del estado existente. No acreditan E1–E5 implementadas, no corrigen el runner y no sustituyen las evaluaciones conductuales pendientes.
