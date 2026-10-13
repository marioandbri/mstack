# AM-014: mantenimiento del sistema de agentes

Estado: descubrimiento y propuesta de componentes, con exploración local ejecutada. No es una spec aprobada ni una instalación. Continúa el sistema completo pedido por Mario: auditoría proactiva, captura, revisión, evaluación y promoción. Reflect coordina la revisión con el usuario. Laya es una hipótesis de apoyo al clasificador.

## Decisiones conservadas

Mario confirmó avanzar con las capacidades del reporte, usar el playground para entender Laya y comparar su contribución de forma aislada. La auditoría debe encontrar oportunidades sin esperar a que el usuario identifique una instrucción concreta. Su ejecución inicial puede ser solicitada; no implica un servicio programado. La captura ocurre durante trabajo activo y la reflexión sigue siendo explícita.

Se conserva la entrega instalada de AM-013. Esta fase tiene rama y worktree separados, basados en `e2dd80e`; no se añade al PR anterior ni se despliega. Las decisiones pendientes de esta propuesta no reabren la aceptación de las instrucciones globales.

## Componentes y contratos propuestos

| Componente | Entrada | Salida y responsabilidad |
|---|---|---|
| Inventario del sistema | Global seleccionado, skills.json, metadata, referencias y configuración declarada pertinente | Snapshot con rutas, hashes, propietario, relaciones y límites de cobertura. Distingue declarado, instalado y cargado. |
| Auditoría | Snapshot, convenciones y evidencia de evaluaciones | Hallazgos con fuente exacta, ámbito, fundamento, impacto, incertidumbre y operaciones candidatas. Puede devolver ningún cambio. |
| Captura | Fricción observada y evidencia mínima | Observación persistida antes de cualquier clasificación. Reutiliza capture-observations. |
| Registros y clasificación | Observación o hallazgo, fuentes y catálogo permitido | Anotación versionada, enlaces y razones. La inferencia opcional no bloquea la conservación del original. |
| Reflect | Hallazgos seleccionados y decisiones anteriores | Revisión con Mario y propuesta acordada, conservando decisiones y preguntas pendientes. |
| Evaluación | Incidente o hipótesis, baseline, candidato y caso negativo cercano | Resultados, trazas, errores de infraestructura y límites, vinculados a las fuentes exactas. |
| Instalador y comprobación posterior | Cambio aceptado, commit y entorno de destino | Recibo existente, smoke conductual pertinente y evidencia de reversión. |

Son responsabilidades, no siete skills nuevas. Inventario y validación mecánica pueden ser comandos o bibliotecas pequeñas del repo; la auditoría semántica usa al agente. Reflect mantiene referencias y coordinación. Se decide el empaquetado al cerrar requisitos del componente.

## Auditoría del conjunto

El inventario inicial debe cubrir instrucciones globales, las 30 skills gestionadas en la revisión base, referencias y controles de activación declarados. Las skills externas que puedan competir se incluyen por su metadata y procedencia, sólo dentro del catálogo accesible. No se importan ni se editan como copias gestionadas. La configuración privada se consulta únicamente por las claves necesarias; credenciales y conversaciones ajenas quedan fuera.

Separar tres capas de evidencia:

1. Checks de estructura: nombres, referencias resolubles, manifest, propietarios y discrepancias de instalación. Reutilizar scripts/validate.ts y el instalador.
2. Análisis semántico: duplicación con el mismo ámbito, contradicciones, estado temporal en instrucciones duraderas, responsabilidades mezcladas y posibles límites mecanizables. Requiere fuentes y puede abstenerse.
3. Pruebas conductuales: solicitudes positivas y negativas que distingan skills competidoras, verificación de carga por entorno y resultado de la tarea. Similitud textual no demuestra competencia real.

Cada hallazgo propone KEEP, REMOVE, MOVE, MERGE, SPLIT, ADD o MECHANIZE con razón y alternativa de no cambiar. Un hallazgo puede requerir evidencia adicional. No se elimina por antigüedad, longitud, poca frecuencia o ausencia de trazas de uso. La obsolescencia necesita una fuente que reemplace o contradiga el contenido.

El informe prioriza impacto, evidencia y relación con el objetivo, manteniendo visibles incidentes graves únicos. Recurrencia cuenta incidentes independientes, no mensajes o copias. Laya no contará incidentes ni resolverá su identidad.

## Registros intercambiables

Mantener los esquemas actuales de observación y revisión. Añadir un esquema propio de anotaciones cuando se implemente el componente. Su contrato propuesto incluye versión, ID, referencias a fuentes y hashes, proveedor y versión, estado `suggested` o `abstained`, etiquetas, puntuaciones opcionales, razones, límites y vínculos con anotaciones anteriores. Las probabilidades del modelo y la confianza validada se representan por separado.

El agente completa razones y vínculos; Laya sólo aporta respuestas tipadas sobre el texto. La validación comprueba referencias existentes, categorías permitidas y ámbito. Ninguna salida del proveedor autoriza acciones. Una entrada inválida o un proveedor caído deja pendiente la clasificación sin perder la observación.

La persistencia debe crear originales sin sobrescribir, usar escritura atómica y evitar pérdidas entre escritores concurrentes. El índice será reconstruible desde registros, con detección de entradas faltantes. Reclasificar agrega una versión y conserva evidencia y decisiones anteriores. El mecanismo concreto de exclusión y recuperación se elegirá con pruebas de fallo, usando la biblioteca estándar si basta.

## Lugar de Laya según la exploración

El [ensayo local](../evaluations/2026-10-13-laya/report.md) probó clasificación de observaciones y de fragmentos, además de preguntas binarias. La clasificación amplia falló en contenido mixto y restricciones. Dos positivos de fallos no se detectaron ni siquiera con la pregunta binaria.

Recomendación: proveedor opcional y experimental, fuera del flujo activo. Preferencias y pasos operativos merecen una prueba con ejemplos nuevos. No usarlo ahora para descartar hallazgos, elegir cambios de instrucciones, certificar fallos o decidir permisos. Si no aporta una mejora medible, el sistema conserva el procedimiento actual y prescinde del adaptador.

El adaptador, si se justifica, recibirá texto breve, idioma explícito y una versión de preguntas. Devolverá etiqueta o abstención, probabilidades originales, modelo, parámetros y duración. Las referencias, IDs y comparaciones numéricas las resuelve el código. La ruta seguirá funcionando con el servicio apagado. No convertir el playground en una dependencia permanente por su disponibilidad actual.

## Comparación que sí mide la contribución

Comparar A, agente con el procedimiento actual, y B, el mismo agente más la anotación opcional de Laya. Mantener idénticos modelo mayor, razonamiento, herramientas, fuentes, casos y límites. Alternar el orden y separar sesiones para reducir contaminación. Un tercer resultado, Laya solo, sirve para diagnóstico, no como sustituto del contrato completo.

Preparar casos reales saneados con etiquetas y acciones esperadas revisadas antes de ver las salidas. Separar desarrollo y comprobación por familias de incidente, no por copias o paráfrasis. Incluir contenido mixto, negación, instrucciones citadas, idiomas, falta de contexto, truncamiento, proveedor caído y sugerencias erróneas con probabilidad alta. Reservar ejemplos nuevos para el seguimiento binario; los 36 casos de esta exploración ya no son datos nuevos.

Medir por separado:

- Calidad final: categorías, omisiones de fallos/restricciones, relaciones incorrectas entre registros y razones respaldadas por evidencia.
- Utilidad: intervenciones y correcciones de Mario, hallazgos válidos recuperados y acciones innecesarias.
- Coste: llamadas y tokens del modelo mayor, tiempo total y coste adicional de Laya. Si B sigue llamando al mismo agente para todo, no asumir ahorro.
- Robustez: captura sin clasificador, abstenciones, anotaciones inválidas, concurrencia, índices incompletos y recuperación de escritura.

El criterio propuesto es conservar calidad y límites del flujo y mejorar al menos una medida útil. Los fallos de autorización, pérdida de evidencia o promoción directa invalidan el candidato. Antes de una tanda confirmatoria deben cerrarse el margen aceptable de calidad, corpus revisado, modelo, repeticiones y presupuesto. No fijar un umbral de probabilidad a partir de esta pequeña muestra ni gastar un presupuesto antiguo.

## Entregas propuestas

| Orden | Entrega | Comprobación concreta |
|---|---|---|
| 1 | Inventario y auditoría inicial del conjunto | Hallazgos trazables, cobertura declarada, operaciones propuestas y negativos que eviten falsos duplicados. Sin cambios activos. |
| 2 | Registros de hallazgos/anotaciones y persistencia robusta | Capturas concurrentes sin pérdida, fallo de escritura recuperable, índice reconstruible y proveedor ausente. |
| 3 | Runner reutilizable y casos reales | Reproducir y corregir el defecto de exportación ya observado; conservar evidencia legible sin recuperación manual. Diferenciar infraestructura de fallo conductual. |
| 4 | Comparación A/B del clasificador opcional | Casos nuevos, etiquetas revisadas, resultados finales y coste comparables. Adoptar, ajustar o descartar según evidencia. |
| 5 | Ciclo de promoción y reversión | Candidato aceptado, instalación existente, comprobación conductual posterior y reversión ensayada con recibos. |

Las entregas 1 y 2 pueden prepararse sin esperar a Laya. La entrega 3 desbloquea evaluaciones desatendidas fiables; la 4 depende de registros y del runner. La 5 conserva la aceptación de cambios e instalación por Mario. La propuesta cubre también vigencia del conocimiento y competencia entre skills, dentro de la auditoría y sus pruebas.

Recomiendo convertir estas entregas en tickets con dependencias, porque tienen aceptación propia y Laya puede descartarse sin bloquear el sistema. El siguiente paso material es concretar el inventario y la auditoría inicial. Esta propuesta no decide aún crear otra skill, un repositorio, un servicio o una automatización periódica.

## Fuentes y continuidad

La autoridad de contratos sigue en [clasificación](../../../skills/reflect/references/classification.md), [registros](../../../skills/reflect/references/records.md) y [evaluación](../../../skills/reflect/references/failure-evaluation.md). La instalación aceptada está en [AM-013](AM-013-installation.md).

La investigación original y reportes históricos adicionales residen en el checkout canónico, bajo docs/agent-maintenance. No todos forman parte del commit base de este worktree. El registro sources.json junto al ensayo identifica rutas y hashes de lo consultado; no se copiaron directorios completos ni se modificaron originales. Su afirmación histórica de que ningún caso fue ejecutado está desactualizada y no se usa como estado actual.
