# AM-023: Reflect reanudable

El ticket 08 persiste revisiones versionadas y sus candidatos en SQLite. El registro interno conserva sin cambios el esquema público de propuestas. Un sobre separado contiene petición de reflexión, una pregunta activa, dominios de decisión, fuentes de respuestas y dependencias de cada oportunidad.

Al reabrir se recuperan originales, resúmenes con extractos y límites, clasificación y decisiones. El contexto conservado y el disponible ahora se presentan por separado. Una síntesis parcial o clasificación pendiente no bloquea la evidencia original. La reconciliación registra hashes y fuentes del cambio, conserva respuestas históricas y reabre sólo las oportunidades afectadas.

Cinco pruebas públicas cubren reanudación con resumen retenido, conducta aprobada con destino pendiente, drift selectivo, rechazos, escritores obsoletos, una pregunta, propuesta sin aplicar y sólo chat. Este último se verifica también por CLI contra una ruta inexistente: no crea ni el directorio de almacenamiento. Una propuesta sin aplicar conserva candidato completo, diff y destino sin modificar archivos activos.

La suite obligatoria pasó: bun run check para 30 skills y 65 Markdown; bun test con 43 pass, 1 skip opcional, 0 fail y 376 aserciones, incluyendo 33 pruebas Python ejecutadas y el smoke Gemma optativo ya realizado en 07; fish install/verify.fish y git diff --check. No se iniciaron evaluaciones generativas.

Standards y Spec: los seis criterios de 08 quedan cubiertos por el adaptador y sus recorridos. Las pruebas verifican persistencia y límites; el comportamiento autónomo del agente en el catálogo real se evaluará con el runner y un presupuesto específico. Las respuestas atribuidas al usuario requieren su fuente real; el almacenamiento no autentica autores ni convierte respuestas en permiso automático de evaluación o instalación.
