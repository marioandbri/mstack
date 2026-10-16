# AM-028: migración y recuperación sin perder decisiones

El ticket 13 incorpora importación explícita de los JSON existentes, export legible, backup consistente de SQLite e instalación de una copia recuperada en un destino nuevo. Los originales y las versiones durables se comprueban por hash. Los índices son reconstruibles: texto queda disponible y vectores pendientes. Una restauración no sustituye escrituras posteriores de la base activa.

Siete pruebas del adaptador usan bases y procesos reales. Matan escritores durante importación y backup, y el restaurador antes y después de publicar el destino. Comprueban atomicidad, diagnóstico de copias incompletas, recuperación del acuse y consistencia mientras otro escritor confirma. Las copias conservan bytes, resúmenes, anotaciones, respuestas y la pregunta pendiente; un archivo histórico copiado no suma otra ocurrencia.

El smoke por el CLI público importó los cuatro originales y las tres revisiones vigentes del repositorio en una base privada de prueba. Repetir creó cero registros. Exportó, inspeccionó y restauró los siete registros, con hashes de los archivos fuente intactos. No migró el almacenamiento de trabajo ni abrió una evaluación generativa. Los metadatos históricos ausentes continúan desconocidos. Una revisión importada requiere una solicitud nueva para continuar, sin perder sus respuestas anteriores.

La prueba de reclasificación verifica también respuestas de Reflect, además de transiciones de estado. Una respuesta nueva vuelve obsoleta la clasificación anterior sin borrarla. La búsqueda muestra estado y decisiones junto a los antecedentes; resolved y discarded se presentan como históricos.

Los checks obligatorios pasaron: bun run check, bun test con 43 pass, un skip opcional y cero fallos, fish install/verify.fish y git diff --check. El runtime ejecutó 66 pruebas Python; el smoke Gemma optativo ya realizado quedó omitido en esta pasada. La verificación del instalador confirmó el snapshot estable sin cambios.

Standards: conserva permisos privados, checksums, transacciones y versiones fijadas; no incorpora dependencias. Spec: los seis criterios del ticket quedan cubiertos con copias temporales y procesos interrumpidos. La verificación con agentes del ciclo integrado conserva su protocolo y presupuesto propios.
