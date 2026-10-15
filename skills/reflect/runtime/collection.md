# Recogida de artefactos

collector.py prepara y exporta un workspace sintético de evaluación. Sólo requiere la biblioteca estándar de Python 3.13.2. No lee credenciales ni ejecuta modelos, y no sustituye al transporte o al grader.

```fish
python collector.py create --workspace /ruta/nueva/fixture --attempt intento-01
python collector.py collect --source /ruta/nueva/fixture --destination /ruta/nueva/recogida --attempt intento-01 --terminal completed --timeout 30
```

create exige un directorio nuevo y guarda una identidad ligada al directorio físico, propietario e intento. El productor prepara allí únicamente la evidencia saneada del caso. result.json y events.jsonl conservan el resultado y los eventos del transporte.

Antes de collect, el ejecutor debe haber detenido y esperado a todos los procesos que consumían ese workspace. El ID debe coincidir con la preparación; el nombre de una carpeta no prueba propiedad. No usar este comando para exportar proyectos o worktrees de otros agentes.

La exportación exige un destino nuevo y privado fuera del origen. No sigue symlinks, no lee inodos de archivos compartidos y excluye auth.json, credenciales y carpetas privadas conocidas. La exclusión se registra como límite, no se reemplaza por contenido supuesto. Si un archivo propio carece de lectura del propietario, el recolector añade ese permiso temporalmente y restaura el modo original al terminar. No modifica permisos de snapshots externos ni concede capacidades al contenedor.

Los archivos exportados quedan legibles por el propietario. El informe conserva modo original, normalización automática, bytes y SHA-256 contrastado reabriendo el destino. Un archivo inaccesible deja evidencia parcial sin abortar la recogida restante.

collection.json se guarda antes de copiar, con estado in-progress, y se reemplaza atómicamente al cerrar. Un proceso muerto puede dejar ese estado y archivos parciales; no se interpreta como éxito. Se distinguen collection_status, execution_status, infraestructura y behavioral_status. Recoger archivos no aprueba la conducta. Un resultado ausente y una traza truncada permanecen diferenciados.

terminal admite completed, timeout, interrupted, infrastructure-error y not-executed. Lo determina el transporte después de esperar al proceso. timeout limita la recogida y no reutiliza el presupuesto de modelos. La salida del CLI indica fallos de recogida; la conducta se juzga por separado.

Para recuperar evidencia, usar otro destino y recovery-of con el intento original. El estado queda recovered y conserva el vínculo. No se sobrescribe el recibo anterior ni se reclasifica el intento histórico como ejecución limpia. Los permisos legibles acreditan recogida, no carga efectiva de una skill ni fiabilidad de un harness.
