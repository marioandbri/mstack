# AM-015: sistema de mantenimiento y evaluación de agentes

Estado: fuente revisada para los 14 tickets cuya división y bloqueos aprobó Mario. El tracker elegido es local, con un archivo por ticket y un [índice de entregas](../../../.scratch/agent-maintenance/README.md). La implementación, las nuevas evaluaciones y la instalación conservan sus autorizaciones propias.

## Problem Statement

Mario necesita mantener y mejorar su entorno de agentes sin tener que detectar y señalar personalmente cada instrucción problemática. Hoy existen captura de observaciones, revisión con Reflect, instalación por versiones y evaluaciones acotadas. Falta unir esas capacidades en un proceso repetible que encuentre oportunidades en el conjunto, conserve sus decisiones y compruebe si una intervención ayuda.

La información disponible tampoco permite equiparar una skill instalada con una skill descubierta, cargada o ejecutada correctamente. Una regla puede estar bien escrita y fallar por su activación, competir con otra o no estar disponible en el entorno que la necesita. Añadir instrucciones sin distinguir estos casos puede aumentar la complejidad y conservar el problema original.

Las anotaciones de clasificación carecen de persistencia estructurada propia; los contratos actuales de concurrencia necesitan mecanismos verificables. Los experimentos de Reflect ya produjeron evidencia útil, pero la exportación de una suite exigió recuperación manual. La instalación conserva recibos y respaldos, aunque falta demostrar el ciclo completo con comprobación conductual posterior y reversión ensayada.

## Solution

Completar el sistema dentro del repositorio canónico, reutilizando sus skills, registros, validadores, evaluaciones e instalador. La capacidad funcional prioritaria será una auditoría proactiva del conjunto. Mario podrá pedir que se audite su entorno sin aportar previamente una instrucción o incidente concreto. El resultado será un inventario con cobertura declarada y oportunidades priorizadas, sustentadas en fuentes y abiertas a la decisión de no cambiar.

La captura seguirá registrando evidencia durante el trabajo. La auditoría buscará oportunidades dentro del alcance solicitado. Reflect organizará su revisión con Mario y conservará decisiones y preguntas pendientes. La evaluación comparará intervenciones pertinentes. El instalador aplicará lo aprobado y permitirá comprobar y revertir esa promoción.

El flujo deberá admitir solicitudes naturales como "audita mi entorno", "registra esta fricción", "retomemos esta oportunidad" y "compara este cambio con lo actual". Cada solicitud conservará las autorizaciones anteriores aplicables. Auditar no iniciará automáticamente una entrevista sobre cada hallazgo, y capturar no iniciará Reflect. Proactividad significa descubrir oportunidades dentro de una auditoría solicitada; no supone un servicio periódico.

## User Stories

1. Como Mario, quiero pedir una auditoría del conjunto sin señalar primero una regla, para encontrar oportunidades que todavía no he detectado.
2. Como Mario, quiero conocer las fuentes, versiones y límites de cada auditoría, para saber qué se revisó y qué sigue sin comprobarse.
3. Como Mario, quiero distinguir el global, las instrucciones del repositorio y las skills de cada propietario, para dirigir una propuesta al lugar adecuado.
4. Como Mario, quiero distinguir lo declarado, instalado, expuesto, seleccionado, cargado y ejecutado, para no atribuir un fallo al componente equivocado.
5. Como Mario, quiero que la auditoría considere metadata externa pertinente, para detectar posibles interacciones con mis skills gestionadas sin importarla ni modificarla.
6. Como Mario, quiero que las fuentes inaccesibles y la configuración desconocida aparezcan como límites, para no recibir un informe que simule cobertura completa.
7. Como Mario, quiero detectar referencias rotas y diferencias entre fuente e instalación, para corregir problemas estructurales antes de atribuirlos al agente.
8. Como Mario, quiero detectar duplicación real, contradicciones y estado temporal en instrucciones duraderas, para mantener responsabilidades claras.
9. Como Mario, quiero que una afirmación de obsolescencia cite la fuente que la reemplaza o contradice, para evitar descartes arbitrarios.
10. Como Mario, quiero recibir recomendaciones KEEP, REMOVE, MOVE, MERGE, SPLIT, ADD o MECHANIZE justificadas, para elegir la intervención adecuada.
11. Como Mario, quiero poder conservar lo actual o pedir más evidencia, para no convertir cada auditoría en una obligación de cambiar.
12. Como Mario, quiero probar solicitudes positivas y negativas de skills potencialmente competidoras, para distinguir ambigüedad textual de interferencia real.
13. Como Mario, quiero que capacidades complementarias puedan actuar juntas, para no confundir colaboración entre skills con duplicación.
14. Como Mario, quiero registrar una fricción durante otra tarea sin abrir una revisión, para conservar evidencia sin perder el foco.
15. Como agente de captura, quiero guardar el original antes de clasificarlo, para conservarlo aunque el clasificador falle o no esté disponible.
16. Como Mario, quiero separar hechos, fallos observados, preferencias, riesgos textuales y nuevas capacidades, para revisar cada hallazgo con el criterio adecuado.
17. Como Mario, quiero distinguir copias de un incidente de recurrencias independientes, para no inflar su frecuencia.
18. Como Mario, quiero conservar ámbitos diferentes y evidencia contradictoria, para evitar fusiones que oculten diferencias relevantes.
19. Como Mario, quiero que un incidente grave único siga visible, para que la prioridad no dependa sólo de repetición.
20. Como mantenedor, quiero anotaciones versionadas con un contrato independiente del proveedor, para poder sustituir la clasificación sin rehacer la captura ni borrar su historia.
21. Como agente de mantenimiento, quiero rechazar referencias desconocidas, categorías inválidas y sugerencias fuera de alcance, para que una anotación no se convierta en autorización.
22. Como Mario, quiero que varias sesiones guarden registros simultáneamente sin perder datos, para trabajar con más de un agente de forma segura.
23. Como Mario, quiero recuperar registros después de una escritura interrumpida o un índice incompleto, para no reconstruir manualmente el trabajo.
24. Como Mario, quiero buscar oportunidades por ámbito, asunto o estado, para retomar sólo las que me interesan.
25. Como Mario, quiero conservar rechazos, aplazamientos y decisiones anteriores al reanudar, para no responder otra vez lo ya resuelto.
26. Como Mario, quiero aprobar un comportamiento sin aprobar todavía su destino, para poder revisar ambas decisiones por separado.
27. Como Mario, quiero que un cambio de fuente reabra sólo las decisiones afectadas, para reconciliar diferencias sin reiniciar toda la revisión.
28. Como Mario, quiero que "no aplicar" permita guardar un borrador y que "sólo en el chat" evite escrituras, para controlar tanto la persistencia como la instalación.
29. Como Mario, quiero convertir incidentes reales en casos reutilizables con resultados esperados y negativos cercanos, para mantener un benchmark personal pertinente.
30. Como mantenedor, quiero ejecutar un caso mediante un runner que preserve trazas y artefactos legibles, para evaluar sin reparaciones manuales de recogida.
31. Como Mario, quiero distinguir un fallo conductual de un fallo de infraestructura, timeout o resultado ausente, para interpretar correctamente cada intento.
32. Como Mario, quiero conservar intentos fallidos y recuperaciones posteriores por separado, para no borrar las limitaciones del experimento.
33. Como Mario, quiero comparar una intervención pertinente en el global, una skill o un check con la baseline, para elegir con evidencia y poder concluir que no hace falta cambiar.
34. Como Mario, quiero medir resultado de la tarea, intervenciones humanas y acciones innecesarias, para priorizar utilidad sobre ahorro de tokens.
35. Como Mario, quiero fijar condiciones y presupuesto antes de cada experimento, para mantener comparaciones interpretables y controlar su ejecución.
36. Como Mario, quiero que las evaluaciones comprueben el contexto cargado y mantengan estable aislado del candidato, para proteger el entorno que uso a diario.
37. Como Mario, quiero ver qué casos se prepararon, ejecutaron o quedaron inconclusos, para no confundir una lista de pruebas con evidencia obtenida.
38. Como Mario, quiero que mis preferencias explícitas puedan aceptarse sin exigir una mejora estadística, para conservar el control sobre mi entorno.
39. Como Mario, quiero promover un candidato aceptado usando el instalador existente, para conservar versiones, recibos y configuración ajena.
40. Como Mario, quiero comprobar el comportamiento afectado después de promover, para verificar algo más que la presencia de los archivos.
41. Como Mario, quiero ensayar la reversión y conservar la evidencia de la restauración, para poder regresar al estado anterior con conocimiento de sus límites.
42. Como Mario, quiero que el sistema detecte cambios locales antes de aplicar o revertir, para no sobrescribir trabajo posterior.
43. Como Mario, quiero que los registros contengan sólo evidencia necesaria y saneada, para mantener credenciales y conversaciones ajenas fuera de los artefactos.
44. Como Mario, quiero revisar esta spec antes de dividirla en tickets, para acordar el sistema completo antes de ordenar su implementación.
45. Como Mario, quiero identificar el harness, sesión y evento donde ocurrió una observación y dónde se capturó, para recuperar su origen sin confundir ambas sesiones.
46. Como Mario, quiero recuperar antecedentes mediante filtros, texto y similitud semántica, para encontrar incidentes expresados de formas distintas.
47. Como Mario, quiero que una observación quede conservada aunque fallen sus embeddings, para no depender de la indexación al registrar evidencia.
48. Como Mario, quiero una persistencia embebida sin otro servicio permanente, para mantener sencillo el funcionamiento local del sistema.
49. Como Mario, quiero que la observación conserve un resumen factual con extractos y referencias, para revisar el incidente en otra sesión aunque la conversación de origen deje de estar accesible.
50. Como agente de Reflect, quiero reconocer hechos, hipótesis, contexto faltante y versiones del resumen, para contrastar evidencia posterior sin inventar una reconstrucción ni perder las decisiones previas.

## Implementation Decisions

Las siguientes decisiones conservan el alcance discutido y concretan los contratos del borrador. El empaquetado técnico que todavía no está resuelto se indica como tal.

### Responsabilidades y fuentes

1. El repositorio canónico sigue siendo la fuente del sistema. Se reutilizan el catálogo gestionado, los contratos de Reflect y captura, los validadores, los runners acotados y el instalador por versiones. El sistema no requiere otro repositorio ni una plataforma separada.
2. Inventario, auditoría, captura, clasificación, revisión, evaluación e instalación tienen responsabilidades separadas. Esta división no fija un número de skills. No se creará una skill por cada componente sólo para reflejar la arquitectura.
3. El inventario recibe el alcance solicitado y las fuentes accesibles. Devuelve identidades, versiones o hashes disponibles, propietarios, procedencia, relaciones, controles de activación y cobertura. Conserva estados desconocidos y motivos de inaccesibilidad.
4. La cobertura distingue declaración, instalación y evidencia de exposición, selección, lectura y ejecución por entorno. La ausencia de trazas no demuestra ausencia de uso. Leer una fuente durante investigación tampoco demuestra ejecutar correctamente su procedimiento.
5. La inspección estructural cubre las skills del catálogo gestionado vigente, sus referencias, el global seleccionado y configuración pertinente declarada. No fija el número histórico de 30 como límite del producto. La metadata externa se inspecciona según pertinencia y accesibilidad, registrando lo excluido.
6. La configuración se consulta por claves necesarias. Credenciales, conversaciones ajenas y material privado no pertinente quedan fuera. Los artefactos compartibles contienen evidencia mínima saneada; las trazas privadas conservan su almacenamiento separado.

### Auditoría y vigencia

7. La auditoría combina comprobaciones mecánicas, análisis semántico del agente y evidencia conductual disponible, distinguiendo cada nivel. El inventario completo no permite afirmar una revisión semántica completa de cuerpos que no se leyeron.
8. Cada hallazgo contiene identidad, ámbito, fuente exacta y versión disponible, tipo de evidencia, observación, impacto, incertidumbre, recomendación y razón. La causa sospechada permanece separada de los hechos. Las limitaciones de búsqueda y cobertura acompañan el resultado.
9. El conjunto de operaciones propuestas es KEEP, REMOVE, MOVE, MERGE, SPLIT, ADD y MECHANIZE. Se conserva la opción de ningún cambio o más evidencia. No hay cuotas por operación ni obligación de emitir hallazgos.
10. La auditoría evalúa duplicación por significado, responsabilidad y ámbito; contradicciones por sus condiciones de aplicación; vigencia mediante fuentes que reemplazan o contradicen. Longitud, edad y frecuencia observada no bastan para retirar contenido.
11. La posible competencia entre skills se formula como hipótesis con solicitudes que distingan sus límites. La similitud textual no prueba conflicto. La selección conjunta de capacidades complementarias puede ser correcta. No se añaden selectores globales para compensar un problema de descubrimiento.
12. El orden de revisión considera impacto, evidencia, relación con el objetivo, contradicciones pendientes y recurrencias independientes. No impone pesos numéricos sin validación ni oculta incidentes graves únicos.

### Registros, clasificación y revisión

13. Observación original, hallazgo de auditoría, anotación provisional, decisión del usuario y resultado de evaluación son conceptos distintos. Se relacionan mediante identificadores y fuentes, sin sobrescribir unos con otros. Un riesgo estático nunca se registra como fallo conductual sólo por compartir el mismo formato de almacenamiento.
14. Se preservan los esquemas actuales de observación y revisión. Se define un contrato versionado propio para anotaciones y una representación estructurada de hallazgos. El esquema exacto y su ubicación se resolverán al dividir la implementación, sin introducir campos incompatibles en los registros existentes.
15. La clasificación inicial sigue siendo el procedimiento del agente. El contrato de entrada incluye evidencia, ámbito, fuentes, registros relevantes, decisiones aceptadas, categorías permitidas y catálogo de componentes. La salida identifica proveedor y versión, referencias de entrada, categoría sugerida o abstención, razones, límites, relaciones y antecedentes de la anotación.
16. Categoría, prioridad y recurrencia son resultados distintos. Los enlaces distinguen mismo incidente, recurrencia independiente, relación y conflicto. Una identidad incierta permanece como posible coincidencia; la deduplicación no elimina originales. Cualquier puntuación opcional conserva su significado y no se presenta como confianza calibrada sin evidencia.
17. El llamador valida esquema, referencias, categorías, ámbito y evidencia antes de aceptar una anotación. Una salida inválida o un proveedor ausente conserva el original y deja clasificación pendiente. Ninguna salida puede aprobar revisiones, evaluaciones, descartes o promociones.
18. La persistencia crea originales sin sobrescribir, realiza escrituras atómicas y detecta conflictos de actualización. El índice se puede reconstruir desde los registros duraderos. La recuperación informa operaciones incompletas; no convierte una escritura fallida en un guardado exitoso.
19. Reclasificar conserva versiones anteriores. Las decisiones aceptadas, rechazadas o aplazadas permanecen recuperables. Los registros existentes siguen siendo legibles; una adopción estructurada no inventa autoría, aprobaciones ni hashes históricos ausentes.
20. La recuperación se limita al ámbito solicitado. Cuando el índice está incompleto, consulta registros del mismo ámbito y comunica la limitación. Un elemento resuelto no reaparece como oportunidad nueva sin nueva evidencia.
21. Reflect conserva la revisión explícita con Mario, una pregunta activa y el historial compartido. Distingue aprobación de comportamiento, destino, evaluación e integración. Ante cambios de fuente, reconcilia las decisiones afectadas. Guarda revisiones y propuestas salvo prohibición expresa de escritura.

### Evaluación y promoción

22. La biblioteca conserva casos reales saneados y casos sintéticos identificados como tales. Cada caso describe situación inicial, solicitud, conducta esperada, evidencia, entorno y comprobaciones. Ante un fallo del agente, se define el caso antes de recomendar una reescritura conductual y se busca reproducirlo dentro de la evaluación autorizada. Incluye un negativo cercano cuando corresponda. Las variantes del mismo incidente no cuentan como nuevos incidentes independientes.
23. El runner reutilizable parte de los transportes y controles existentes. Antes de usarlo para nuevas comparaciones desatendidas debe reproducirse y corregirse el defecto de exportación conocido mediante una prueba determinista. La causa no se da por establecida a partir del reporte histórico.
24. Cada intento conserva condiciones, fuentes, límites, eventos y artefactos recogidos. Resultados conductuales, fallos de infraestructura, timeouts y resultados ausentes se registran por separado. Una recuperación queda vinculada al intento original; los reintentos consumen presupuesto explícito y no lo ocultan.
25. Cada comparación fija baseline, candidato, casos, rúbrica, modelo, razonamiento, versiones de herramientas, entorno y presupuesto antes de ejecutar. Comprueba aislamiento y contexto cargado. Mantiene iguales las condiciones relevantes y declara diferencias inevitables o incidentes que afecten la comparación.
26. Se seleccionan intervenciones según el problema: global, skill, control mecánico o conservar lo actual. No es obligatorio probar todas las alternativas para cada incidente. Si la baseline no reproduce el fallo, se conserva esa incertidumbre y se considera no cambiar o investigar más.
27. Las métricas principales son cumplimiento de la tarea, correcciones o intervenciones humanas y acciones innecesarias o fuera de alcance. La selección y ejecución se informan separadamente. Tokens, llamadas y tiempo son medidas secundarias. No se crea una puntuación global que mezcle infraestructura, resultados ausentes y conducta.
28. Un fallo de autorización, pérdida de evidencia o promoción directa invalida el candidato para el caso afectado. Los márgenes de calidad y repeticiones de un experimento se acuerdan antes de su ejecución, sin reutilizar umbrales o presupuestos históricos por inferencia.
29. El estado cambiante de casos y evaluaciones vive en registros de evidencia enlazados desde los procedimientos. Se distingue preparado, ejecutado, recuperado, inconcluso y pendiente de cobertura, conservando las limitaciones originales.
30. La promoción usa el instalador existente y un commit aceptado. Conserva recibo, versión anterior, respaldos y autorización aplicable. Se comprueba el comportamiento pertinente después de la promoción y se ensaya la reversión primero en destinos aislados. Las transferencias de propiedad externas requieren conservar sus pasos adicionales cuando existan.
31. La reversión detecta drift, restaura el estado autorizado y verifica contenido, configuración gestionada y comportamiento afectado. No sobrescribe cambios ajenos ni borra evidencia posterior. Un resultado conductual desfavorable produce una recomendación y respeta la autorización de reversión disponible; no concede permiso nuevo por sí solo.
32. Las preferencias explícitas y hechos confirmados no requieren demostrar una mejora estadística. Las afirmaciones sobre rendimiento o fiabilidad sí deben apoyarse en la evaluación pertinente y declarar sus límites.

### Persistencia y recuperación propuestas durante la revisión

33. Mario eligió SQLite con sqlite-vec como persistencia local, sin otro servicio permanente. La persistencia debe coordinar a los escritores y reconocer reintentos mediante una identidad de operación estable. Los ensayos anteriores conservan la comparación con LanceDB y Chroma, sin exigir instalar esos backends. El ensayo de LanceDB encontró duplicados con merge_insert simultáneo; SQLite resolvió ese recorrido con restricciones y transacciones sin un bloqueo externo. Chroma 1.5.9 genera embeddings con su función por defecto, pero esa captura ocurre después del embedding y no satisface por sí sola el guardado previo del original. Se conserva la separación entre los originales duraderos y los índices derivados, con compatibilidad para los registros existentes.
34. La procedencia propuesta incluye harness y versión disponible, sesión de origen, evento o turno disponible, sesión de captura, contexto del proyecto y fechas pertinentes. Admite varias fuentes y valores desconocidos. La evidencia mínima saneada sigue siendo recuperable cuando un enlace a la sesión deja de funcionar. Una identidad de sesión no demuestra por sí sola duplicación o recurrencia.
35. La recuperación semántica propuesta combina metadata, texto y vectores. Los embeddings son datos derivados que conservan identidad y versión del modelo, hash de entrada y estado de indexación. Se generan después de persistir la observación y fuera de la sección de escritura coordinada. Su similitud sólo recupera candidatos para clasificación; no fusiona registros ni concede permisos. Mario eligió google/embeddinggemma-300m para los embeddings del sistema. La calidad cotidiana y la calibración de abstención siguen pendientes.

El perfil inicial usa la revisión `57c266a740f537b4dc058e1b0cda161fd15afa75`, 768 dimensiones, normalización L2 y recuperación por coseno. Conserva la ventana de 2.048 tokens y los prefijos ensayados: `task: search result | query: ` para consultas y `title: none | text: ` para documentos. La entrada documental es el texto del registro. El [protocolo de la comparación](../evaluations/2026-10-14-embedding-models/protocol.json) fija ese perfil y su procedencia. Se conserva como configuración del adaptador, junto al índice derivado, para poder reconstruir los vectores al cambiar el perfil.

### Reconstrucción factual para Reflect

36. Cada observación se vincula a un resumen factual del incidente, extractos mínimos saneados y referencias a las fuentes pertinentes. El agente de origen lo prepara durante la captura, con el contexto disponible. El conjunto debe permitir revisar los hechos conservados aunque la sesión original no se pueda abrir. Harness, sesión y evento ayudan a localizar el origen; no garantizan recuperar su conversación ni reconstruir todo el contexto cargado.
37. El resumen tiene un contrato propio versionado, separado de la observación original y de las anotaciones de clasificación. No añade campos incompatibles a los esquemas actuales. Conserva los siguientes datos; lo desconocido se marca explícitamente.

| Información | Contenido mínimo |
|---|---|
| Solicitud | Objetivo del usuario, alcance y restricciones relevantes. |
| Hechos | Acciones observables, su autor cuando se conoce, resultados y orden conocido, vinculados a sus fuentes. No inventa fechas ni secuencias ausentes. |
| Decisiones | Correcciones y autorizaciones explícitas del usuario, con su alcance y referencia; separadas de sugerencias del agente. |
| Contexto aplicable | Instrucciones y skills pertinentes, versiones disponibles y evidencia de disponibilidad, selección o carga. Distingue el contexto histórico comprobado del consultado después. |
| Expectativa | Comportamiento esperado cuando esté respaldado por una instrucción, artefacto o decisión del usuario. |
| Límites | Hipótesis de causa, contradicciones e información faltante, separadas de los hechos. |
| Evidencia | Extractos mínimos suficientes para revisar los hechos principales, referencias a mensajes, herramientas o artefactos y hashes cuando estén disponibles. |
| Procedencia del resumen | Observaciones vinculadas, versión, fecha de elaboración, autoría disponible, fuentes utilizadas y estado de completitud. Distingue elaboración en origen de reconstrucción posterior. |

38. La captura persiste primero el original. Un fallo al elaborar o guardar el resumen conserva la observación, deja su reconstrucción pendiente y permite volver a la tarea sin iniciar Reflect. Para registros históricos, el agente utiliza sólo evidencia accesible y declara la elaboración posterior; no atribuye al agente original contexto que no puede comprobar. Las credenciales y material ajeno quedan fuera del resumen y los extractos.
39. Evidencia posterior, correcciones o una nueva síntesis producen otra versión vinculada a sus fuentes y a la versión anterior. No sobrescriben el original, borran contradicciones ni convierten versiones de un resumen en incidentes independientes. Las decisiones del usuario conservan su historia; se reabren sólo las afectadas por la nueva evidencia.
40. Al abrir Reflect, el agente recupera la observación, el resumen con su versión y límites, los extractos, antecedentes pertinentes y decisiones previas. Verifica las fuentes necesarias dentro del acceso y alcance disponibles. La recuperación de conversación por harness es una ampliación opcional, no un requisito para leer los hechos ya conservados. Si falta evidencia esencial, declara qué conclusiones quedan pendientes y pregunta por la brecha material; no completa los huecos por inferencia. Mario recibe hechos y fuentes, análisis provisional, límites y el siguiente paso recomendado. La síntesis sigue siendo evidencia derivada, no una decisión aprobada ni instrucciones ejecutables.

## Testing Decisions

### Frontera principal

La aceptación se comprobará desde las operaciones que usa el agente o Mario y sus artefactos persistidos. Un escenario integrado recorrerá auditoría, conservación de una oportunidad, revisión reanudada, evaluación, promoción aislada y reversión. Se comprobarán resultados y decisiones visibles; no el número de funciones, clases o llamadas internas.

Se reutilizarán las fronteras públicas existentes del validador, almacenamiento e instalador. Las pruebas de concurrencia y recuperación usarán procesos y archivos temporales reales. Los fallos del exportador se probarán en la frontera de recogida de artefactos. No se creará una interfaz de producción adicional sólo para facilitar mocks. Los tickets conservan estos recorridos, sin fragmentarlos en pruebas que sólo reflejen la implementación.

### Criterios de aceptación

| ID | Recorrido o condición | Resultado exigido |
|---|---|---|
| A01 | Solicitar auditoría sin aportar incidente. | Produce inventario y hallazgos trazables del alcance seleccionado, con cobertura y prioridades; no modifica instrucciones activas. |
| A02 | Inspeccionar fuente vigente, instalación diferente y catálogo parcial. | Representa las tres evidencias por separado; no afirma carga o fallo de selección sin trazas. |
| A03 | Auditar una referencia rota, una fuente inaccesible y configuración desconocida. | Identifica cada condición y su límite; conserva los resultados útiles sin declarar cobertura completa. |
| A04 | Auditar frases parecidas de distinto ámbito y capacidades complementarias. | No las fusiona ni elimina sólo por similitud; justifica KEEP o una hipótesis pendiente. |
| A05 | Auditar una contradicción documentada y una regla reemplazada por una fuente vigente. | Expone ambas fuentes, versiones y ámbito; propone una operación sin aplicarla. |
| A06 | Probar el contrato de recomendaciones y la salida sin hallazgos. | Admite las siete operaciones y la abstención de cambiar; cada recomendación tiene evidencia y alternativa de conservación. |
| A07 | Registrar una corrección durante otra tarea o discutir el diseño de Reflect. | La captura pertinente persiste evidencia y vuelve a la tarea. La mención de Reflect no inicia revisión, evaluación ni promoción. |
| A08 | Capturar con clasificador ausente, malformado o fuera de ámbito. | Conserva el original, rechaza la anotación inválida y comunica clasificación pendiente. |
| A09 | Clasificar copias de un incidente, una recurrencia independiente y evidencia contradictoria. | Cuenta sólo incidentes independientes y conserva ámbitos y conflictos; no borra originales ni inventa consenso. |
| A10 | Capturar simultáneamente y actualizar desde una revisión obsoleta. | Cada escritura confirmada sigue recuperable; un conflicto se informa sin sobrescribir datos. Colisiones de ID no reemplazan originales. |
| A11 | Interrumpir escritura antes y después de guardar el original, o perder el índice. | No expone archivos parciales como registros válidos. Recupera lo duradero y reconstruye el índice sin inventar decisiones. |
| A12 | Leer registros históricos y reclasificar una observación. | Los esquemas actuales siguen válidos, el original conserva sus bytes y las versiones previas siguen accesibles. |
| A13 | Reanudar una revisión en otra sesión, con rechazos y destino pendiente. | Recupera decisiones y propuestas; pregunta sólo por lo pendiente. Un cambio de fuente reabre únicamente lo afectado. |
| A14 | Revisar con "no aplicar" y, por separado, "sólo en el chat". | En el primer caso guarda estado y candidato sin activar; en el segundo no escribe y explica el límite de reanudación. |
| A15 | Ejecutar solicitudes positivas y negativos cercanos del catálogo real. | Conserva evidencia de disponibilidad, selección, carga y resultado. Una invocación explícita no acredita selección automática. |
| A16 | Reproducir el recorrido histórico de exportación defectuosa. | El reproducer falla antes de la corrección y pasa después, con artefactos legibles y hashes verificables, sin reparación manual ni llamadas al modelo para probar el recolector. |
| A17 | Recoger un archivo ilegible, salida parcial, proceso interrumpido o resultado ausente. | Devuelve el estado de infraestructura correspondiente, preserva evidencia disponible y no inventa un resultado conductual. Una recuperación conserva el intento original. |
| A18 | Preparar un caso real y su negativo cercano. | Ambos tienen condiciones y rúbrica anteriores a la salida; la biblioteca distingue evidencia histórica, datos sintéticos y nuevas ejecuciones. |
| A19 | Comparar una intervención pertinente con baseline. | Mantiene condiciones comparables, verifica el contexto cargado y presenta métricas conductuales, intervención humana y acciones innecesarias separadas del coste y la infraestructura. |
| A20 | No reproducir el fallo histórico, o recibir una preferencia explícita. | El primer caso conserva incertidumbre y opción de no cambiar; el segundo no exige un experimento de rendimiento para reconocer la preferencia. |
| A21 | Intentar ejecutar sin autorización o superar el presupuesto del experimento. | No inicia llamadas no autorizadas; conserva lo preparado y reporta el límite. Una autorización vigente permite continuar sin pedirla de nuevo. |
| A22 | Preparar y evaluar un candidato aislado. | El entorno estable conserva contenido y configuración. La carga candidata se verifica; un directorio distinto por sí solo no cuenta como aislamiento. |
| A23 | Promover y revertir en un entorno temporal mediante el instalador existente. | Conserva recibos y versiones, comprueba conducta tras promoción y tras reversión, y preserva configuración no gestionada. El dry-run no modifica el HOME de prueba. |
| A24 | Introducir drift antes de promover o revertir. | Detecta el conflicto y evita sobrescrituras; conserva la evidencia y distingue operación pendiente de restauración verificada. |
| A25 | Revisar registros, logs y exportaciones del ciclo. | No contienen credenciales ni material ajeno; los enlaces recuperan la evidencia pertinente y no elevan el nivel de acceso. |
| A26 | Ejecutar el recorrido integrado en sesiones separadas. | Una oportunidad de auditoría llega a revisión, comparación y promoción/reversión aisladas sin perder decisiones ni pedir de nuevo autorizaciones conservadas. Se puede optar por no cambiar y cerrar sin instalación. |
| A27 | Capturar un incidente originado en otra sesión y un origen parcialmente desconocido. | Conserva origen y captura por separado, varias fuentes si existen y la evidencia mínima; no inventa identificadores faltantes. |
| A28 | Buscar antecedentes con filtros, texto y similitud. | Respeta el ámbito y las decisiones previas. Un corpus revisado mide antecedentes relevantes recuperados y asociaciones equivocadas; vectores fijos sólo validan la consulta. |
| A29 | Reintentar una captura simultáneamente desde dos procesos o reutilizar su identidad con otro contenido. | El adaptador conserva una sola captura para la misma operación y reporta la colisión con evidencia distinta. La indexación pendiente no bloquea su guardado. |
| A30 | Capturar una observación y revisarla en otra sesión con el origen inaccesible. | Recupera el resumen, extractos y referencias conservados; permite contrastar solicitud, acciones, resultados y decisiones documentadas. Identifica el contexto histórico comprobado y sus límites sin exigir la transcripción completa. |
| A31 | Fallar la elaboración del resumen o reconstruir un registro histórico con evidencia incompleta. | La observación original sigue guardada. El resumen pendiente o parcial declara los datos desconocidos y su elaboración posterior cuando corresponda. Reflect deja pendientes las conclusiones sin respaldo y consulta sólo la brecha material. |
| A32 | Incorporar evidencia que contradice una síntesis anterior. | Conserva ambas versiones, fuentes y decisiones; refleja la contradicción y reabre sólo lo afectado. La nueva síntesis no cuenta como otra ocurrencia del incidente. |

### Evidencia previa y ejecución

El validador existente ya prueba manifest, metadata y referencias. La suite del instalador usa fuentes Git y HOME temporales, comprueba configuración, rollback y recuperación. El helper de entorno tiene pruebas reales de escritura concurrente y rechazo de revisiones obsoletas. Se aprovecharán esos patrones sin acoplar observaciones al estado del instalador o del entorno.

La prueba local de LanceDB usa el SDK Python 0.40.0 y dos procesos reales. Conservó escrituras distintas, revisiones condicionales y captura sin vector; el reintento nativo concurrente produjo duplicados en diez pares. Un adaptador cooperativo con bloqueo local y lectura fresca dejó una captura por operación en diez pares. Es evidencia para el diseño, no la implementación de los registros definitivos ni una garantía del SDK JavaScript. Sus interrupciones y vectores fijos no cubren corte eléctrico ni calidad de embeddings.

La comparación posterior con SQLite 3.47.1 y sqlite-vec 0.1.9 pasó doce casos. Las mismas tandas de captura y reintento conservaron observaciones únicas mediante restricciones y transacciones; también se comprobó rollback tras interrupción y atomicidad entre registro e índice vectorial. SQLite usa FTS5 y el adaptador aporta la combinación RRF para consultas híbridas. Las ejecuciones en días distintos y sus vectores fijos no constituyen un benchmark de rendimiento o relevancia semántica.

Chroma 1.5.9 se ensayó después con vectores fijos explícitos y la función de embeddings desactivada. El recorrido nativo conservó reintentos por ID y consultas, pero rechazó la captura sin embedding, aceptó dos decisiones desde revisión 0 y devolvió sin error ante colisiones de contenido. El control con acceso serializado detectó revisiones y colisiones; no resolvió la captura sin embedding. La referencia actual menciona conditional, pero esa API no está en el SDK probado. Se conservan versión y diferencias del corpus, sin extrapolar a otros SDK ni al despliegue con servidor.

Mario autorizó después repetir Chroma con la función por defecto. Descargó automáticamente all-MiniLM-L6-v2 y generó vectores locales de 384 dimensiones; add con documentos y query_texts funcionaron sin vectores suministrados. Ocho consultas sobre diez documentos sintéticos recuperaron un antecedente relevante entre los tres primeros, con acierto primero de 3/4 en inglés y 2/4 en español. El corpus y las expectativas se fijaron antes de ejecutar. Una excepción deliberada en la etapa de embedding dejó cero registros nuevos; la captura automática no equivale a guardar el original antes del modelo. No se comparó ese corpus con SQLite o LanceDB ni se evaluó clasificación. El primer recolector falló tras las operaciones y su evidencia se recuperó conservando el intento original.

El [corpus de recuperación preparado para revisión](../evaluations/2026-10-14-embedding-corpus/review.md) incorpora 30 antecedentes históricos y tres escenarios sin ejecutar sobre omisión de convenciones, entrevista y worktree. Propone 26 intenciones de consulta con variantes españolas e inglesas, incluidos controles sin antecedentes y controles que distinguen omisión de reutilización válida o requisitos ya cerrados. Selección de una skill, compatibilidad con su trigger y cumplimiento efectivo se comprueban por separado. Una spec o ticket aprobado con implementación solicitada permite preguntas para brechas materiales nuevas de dominio, desviación de alcance o falta de respaldo documental, tras investigar. Se distinguen relevancia directa, contexto y negativos cercanos; cinco ambigüedades y un control histórico quedan fuera de puntuación. Las etiquetas todavía no están aprobadas; la autorización posterior permite una comparación exploratoria sobre esas propuestas. El paquete conserva procedencia y extractos por hash, sin presentar escenarios, traducciones, seguimientos o fixtures como incidentes independientes.

La comparación posterior de embeddings ejecutó google/embeddinggemma-2 y Qwen/Qwen3-Embedding-0.6B, con MiniLM y FTS5 como referencias. Qwen recuperó primero el directo esperado en 41/46 consultas y Gemma en 37/46; ambos lograron 46/46 en top 3. MiniLM obtuvo 27/46 primeros directos y FTS5 34/46. La ejecución usa texto, prefijos de búsqueda, dimensiones completas, float32 y CPU en un entorno aislado. Conserva el fallo inicial de dependencias de Gemma y la repetición completa tras corregirlo. Se verificaron 150 consultas vectoriales reabriendo las bases y comparando coseno de NumPy. El [informe](../evaluations/2026-10-14-embedding-models/report.md) separa idiomas, recursos y pérdidas de la combinación híbrida; no decide un modelo de producción ni calibra abstención o clasificación.

La ampliación solicitada completó google/embeddinggemma-300m e intfloat/multilingual-e5-small y repitió los cinco perfiles con corpus, revisiones y dependencias idénticos. Gemma 300M obtuvo 45/46 primeros directos y 46/46 en top 3, con mediana de generación de consulta 48,7 ms y RSS máximo muestreado 1,15 GiB. E5 obtuvo 39/46 y 45/46, con prefijos query:/passage: también en español, mediana 14,6 ms y RSS 0,98 GiB. Los cuatro perfiles repetidos conservaron rankings y métricas. La verificación independiente reabrió 250 consultas vectoriales. Se conservan los rechazos de acceso 401/403 anteriores a aceptar Mario las condiciones y autorizar su cuenta para Gemma 300M. Los resultados actuales usan la pasada completa; la combinación híbrida de pesos iguales redujo los primeros directos de Gemma 300M a 43/46. Esta evidencia amplía la comparación exploratoria; no adopta un modelo ni modifica el alcance aprobado.

Los ensayos históricos de apoyo y persistencia de Reflect aportan casos de clasificación, revisión, decisiones conservadas y excepción de sólo chat. El seguimiento de persistencia pasó cuatro etapas, pero excluyó el recorrido de exportación defectuosa. Los resultados recuperados de la suite anterior no equivalen a una ejecución limpia. La nueva biblioteca conservará esas distinciones y reutilizará lo disponible, sin recalificar el historial.

La verificación tendrá dos niveles. Las pruebas deterministas comprueban contratos y fallos de almacenamiento, inventario, recogida e instalación. Las evaluaciones con modelos comprueban selección, ejecución y revisión en el entorno seleccionado. Ningún nivel sustituye al otro. La ejecución conductual necesita un protocolo acotado con autorización, modelo, entorno, repeticiones y presupuesto propios.

La cobertura se informará por entorno. La presencia en destinos de Agents, Claude, Codex y Pi no acredita conducta en todos ellos. No se exigirá una afirmación universal de fiabilidad para cerrar una entrega; sí evidencia del comportamiento cubierto y una lista explícita de lo pendiente. La matriz concreta de ejecuciones se fijará al preparar los experimentos.

Se mantendrán los checks obligatorios del repositorio con Bun 1.3.14, incluida la suite Python del instalador y su verificación. No se añadirán pruebas que sólo busquen frases en instrucciones como sustituto de resultados observables.

## Out of Scope

- Integrar Laya, desarrollar su adaptador, continuar su comparación o reabrir su descarte actual.
- Crear otro laboratorio, repositorio, plataforma, base de datos central o servicio periódico de auditoría.
- Crear automáticamente una skill por responsabilidad o importar skills externas sin revisión de procedencia y licencia.
- Recopilar conversaciones ajenas, credenciales o datos privados no pertinentes; agregar registros de todos los proyectos o inventar un destino global para sesiones sin proyecto.
- Reescribir el global ya aceptado o aplicar automáticamente las recomendaciones que produzca la auditoría.
- Eliminar por antigüedad, longitud o falta de uso observado; deduplicar mediante borrado de originales; convertir probabilidad en permiso o garantía.
- Reemplazar el instalador, la infraestructura de benchmarks de programación o los workflows de entrega existentes.
- Automatizar publicaciones, merges, promociones o reversiones fuera de autorizaciones explícitas conservadas.
- Ejecutar nuevas comparaciones con modelos o instalar candidatos por la sola preparación de la spec o de sus tickets.

## Further Notes

### Orden de trabajo y decisiones pendientes

Mario eligió preparar esta spec, revisarla y después dividirla en tickets. Tras revisar los modelos de embeddings y el contexto factual para Reflect, solicitó avanzar con to-tickets y aprobó la división en 14 entregas con sus bloqueos. Los tickets locales conservan este alcance. Publicarlos no inicia su implementación.

La división conserva cinco áreas de entrega: inventario y auditoría, registros robustos, runner y biblioteca de casos, comparación de intervenciones, y promoción con reversión. Cada ticket debe cerrar un recorrido verificable, con dependencias que lo bloqueen realmente. La auditoría es la prioridad funcional. Los registros pueden desarrollarse con observaciones existentes, y la reproducción determinista del exportador puede prepararse sin esperar al inventario. Las comparaciones dependen de recogida fiable; el cierre de promoción requiere la evidencia pertinente o una preferencia explícita aplicable.

Quedan por concretar durante la preparación de la implementación el empaquetado del inventario y auditoría, el esquema exacto de hallazgos/anotaciones y la interfaz pública que reutilizará el agente. Los parámetros de cada evaluación, incluidos matriz de entornos, casos, modelo, repeticiones, rúbrica y presupuesto, se fijarán antes de ejecutarla. Estos pendientes no autorizan al implementador a cambiar el comportamiento definido aquí.

Mario confirmó el resumen factual con extractos y referencias como contexto de reconstrucción para Reflect. Sus contenidos, elaboración, versionado y límites quedan definidos en las decisiones 36–40 y A30–A32. La implementación concretará el esquema y almacenamiento compatibles y las capacidades de acceso de cada harness; conservar el resumen no depende de disponer de lectura completa de sesiones. La confirmación de este contrato se conserva al preparar los tickets.

### Revisión de persistencia y búsqueda

Mario señaló la utilidad de procedencia por harness y sesión, búsqueda semántica y persistencia robusta con agentes en paralelo. Prefirió evitar otro servicio y eligió ensayar LanceDB embebido. El [informe de la prueba](../evaluations/2026-10-13-lancedb/report.md) conserva el resultado nativo desfavorable de reintento y el resultado del adaptador; no se activó un backend de captura.

El contrato actual almacena JSON y propuestas legibles por proyecto. Adoptar una base embebida será una evolución explícita de ese contrato. La implementación deberá conservar lectura o importación de registros existentes, esquemas compatibles, exportación legible y recuperación de decisiones; no puede tratar la base y los archivos como dos fuentes independientes de verdad. Historial, migración, backup/restauración y sincronización de índices siguen pendientes de diseño y verificación. El versionado de tablas de la base no sustituye por sí solo al historial de decisiones del usuario.

Mario autorizó después una [prueba de SQLite con extensión vectorial](../evaluations/2026-10-14-sqlite-vector/report.md) y confirmó SQLite con sqlite-vec al pasar a tickets. Es el backend seleccionado; no se instalarán también los backends comparados. Mario eligió EmbeddingGemma 300M tras la comparación de modelos. La adopción conserva la evaluación pendiente con más observaciones independientes y la calibración de abstención. Las primeras pruebas de almacenamiento usaron vectores fijos.

La [comparación con Chroma](../evaluations/2026-10-14-chroma/report.md) conserva evidencia de sus contratos. El acceso serializado resolvió parte de ellos, pero dejó pendiente guardar originales antes de indexarlos. La selección posterior de SQLite no activa un backend ni inicia la implementación.

El [seguimiento con la función por defecto de Chroma](../evaluations/2026-10-14-chroma-default-embeddings/report.md) comprueba la descarga y ejecución local autorizadas de all-MiniLM-L6-v2. Corrige el límite de cobertura de la primera configuración y acredita una muestra de búsqueda real, sin elegir ese modelo para producción ni autorizar llamadas a proveedores alojados. El guardado previo, coordinación y calidad habitual en español siguen siendo decisiones pertinentes para la revisión.

Al aprobar la división, Mario cambió el destino de GitHub Issues a un tracker local. Cada ticket se guarda por separado bajo `.scratch/agent-maintenance/issues/`, con estado ready-for-agent y bloqueos por número y título. La [configuración del tracker](../../agents/issue-tracker.md) describe sus operaciones. La implementación posterior mantendrá esta fase separada de la entrega anterior y comprobará su base remota antes de publicar cambios de código.

### Referencias y trazabilidad

- [AM-014: descubrimiento y decisiones de alcance](AM-014-maintenance-discovery.md). Sus secciones históricas sobre Laya quedan diferidas por la decisión posterior registrada al inicio.
- [AM-014: auditoría inicial, hallazgos I-01 a I-07 y entregas propuestas](AM-014-inventory-audit.md).
- [Snapshot de fuentes y cobertura](AM-014-inventory.json). Identifica también por raíz y hash las fuentes históricas de investigación y los reportes de apoyo y persistencia que no forman parte de este worktree.
- [Captura](../../../skills/capture-observations/SKILL.md), [Reflect](../../../skills/reflect/SKILL.md), [clasificación](../../../skills/reflect/references/classification.md), [registros](../../../skills/reflect/references/records.md) y [evaluación](../../../skills/reflect/references/failure-evaluation.md).
- [Persistencia actual](../persistence.md) y [versión aceptada e instalada](AM-013-installation.md).

| Capacidad del reporte original | Cobertura del borrador |
|---|---|
| Captura sin promoción directa | Historias 14–16; decisiones 13–18 y 21; A07–A08, A14. |
| Clasificación, deduplicación y prioridad | Historias 16–21; decisiones 12–17; A08–A09, A12. |
| Fallos convertidos en evaluaciones | Historias 29–32; decisiones 22–24 y 29; A16–A18. |
| Comparar global, skill, check o ningún cambio | Historias 33–35 y 38; decisiones 25–28 y 32; A19–A21. |
| Auditoría proactiva del conjunto | Historias 1–11; decisiones 3–10; A01–A06. |
| Competencia entre skills | Historias 12–13; decisión 11; A04 y A15. |
| Operaciones sistemáticas de mejora | Historias 8–11; decisiones 8–10; A05–A06. |
| Benchmark personal | Historias 29–37; decisiones 22–29; A15–A22. |
| Separación estable y candidato | Historias 4 y 36; decisiones 4, 25 y 30; A02 y A22. |
| Promoción, comprobación posterior y reversión | Historias 39–42; decisiones 30–31; A23–A26. |
| Contexto factual para reanudar una reflexión | Historias 45 y 49–50; decisiones 34 y 36–40; A27 y A30–A32. |

Las pruebas de la auditoría previa validan sus documentos y el estado existente. No constituyen aceptación de esta spec ni evidencia de que sus capacidades pendientes estén implementadas.
