# Migración y recuperación

SQLite es la fuente durable. Los JSON históricos se leen donde están; migrarlos requiere seleccionar sus rutas explícitamente. El adaptador no elimina archivos ni mantiene una segunda escritura en JSON. Los exports legibles sirven para inspección.

El comando base de [registros](README.md) admite estas operaciones:

```fish
# Primero inicializar una base privada con init.
# entradas.json contiene [{"kind":"observation","path":"/ruta/observacion.json"},
#                         {"kind":"review","path":"/ruta/revision.review.json"}].
python record_cli.py --database /ruta/records.sqlite3 --project proyecto archive import --manifest entradas.json
python record_cli.py --database /ruta/records.sqlite3 --project proyecto archive export --destination /ruta/respaldo-nuevo
python record_cli.py --database /ruta/records.sqlite3 --project proyecto archive inspect --source /ruta/respaldo-nuevo
python record_cli.py --database /ruta/records.sqlite3 --project proyecto archive restore --source /ruta/respaldo-nuevo --destination /ruta/recuperada.sqlite3
python record_cli.py --database /ruta/recuperada.sqlite3 --project proyecto archive restored-status
```

Ejecutar con Python 3.13.2 y el lockfile mediante uv 0.10.11, como indica el comando completo del README. Las rutas del ejemplo son parámetros seleccionados por el operador.

La importación valida todo el lote antes de una transacción. Conserva los bytes de cada archivo, sus rutas y el registro original. Copias del mismo ID y contenido JSON no crean otra observación ni suman recurrencia. Un ID con contenido diferente causa conflicto y revierte el lote. Los autores, harness, sesiones, hashes históricos y autorizaciones ausentes siguen desconocidos. La fecha de importación es una fecha técnica, no la del incidente.

Las revisiones importadas conservan respuestas y fuentes. Su dominio queda unknown cuando no consta estructurado; el texto libre de scope no se convierte en autorización. Sin una nueva solicitud explícita, la revisión permite sólo leer evidencia. Los originales no suministrados se muestran como lagunas. Al reanudar, las respuestas resueltas quedan protegidas y la procedencia de importación permanece en la historia.

## Respaldo consistente

El export usa el mecanismo de backup de SQLite dentro de una instantánea de lectura. Un escritor puede confirmar después sin perder su escritura en la base activa; el manifiesto declara exactamente los originales y versiones incluidos en el respaldo. Una transacción posterior al snapshot no aparece en esa copia.

El directorio privado contiene records.sqlite3, records.json y manifest.json. Sólo status ready confirma integridad, claves foráneas, hash de las tablas durables, lista de originales y hashes de ambos archivos. El JSON conserva originales, anotaciones, resúmenes, decisiones, revisiones y enlaces. No se marca listo un export interrumpido. inspect distingue incomplete de ready; una copia modificada se rechaza.

## Restauración

restore exige un destino nuevo del mismo project. No sobrescribe una base activa, aunque el respaldo sea anterior, y no borra escrituras posteriores. Primero copia, verifica y reconstruye en un archivo privado provisional. Publica el archivo completo sin reemplazar un destino concurrente. Si el proceso muere antes de publicar, el destino no existe; después de publicar, restored-status permite recuperar el acuse desde la base completa.

Los originales y toda la historia durable se verifican contra el respaldo. FTS se reconstruye, los vectores quedan pendientes y se conserva su historia de generación. Reindexar no cambia observaciones ni decisiones. Las respuestas de Reflect también forman parte del contexto de clasificación; una respuesta posterior deja obsoleta una anotación anterior. La búsqueda muestra el estado y las decisiones: un registro resuelto o descartado sigue siendo antecedente histórico, sin presentarse como una oportunidad nueva.

Para cambiar la base usada por los agentes, coordinar primero que no queden escritores en la anterior y seleccionar después la nueva ruta común. El adaptador no cambia la configuración ni mueve bases en uso. Los provisionales interrumpidos conservan evidencia y no se reutilizan como respaldos listos.
