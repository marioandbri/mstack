# SQLite con sqlite-vec para el sistema de mantenimiento

SQLite con sqlite-vec pasó los doce casos preparados. Conservó las escrituras de dos procesos, reconoció reintentos simultáneos sin duplicar observaciones y detectó revisiones obsoletas. La búsqueda vectorial y textual respetó el ámbito, y una combinación RRF implementada en el adaptador produjo consultas híbridas. No se generaron embeddings ni se midió calidad semántica.

La evidencia favorece SQLite para el registro transaccional de observaciones y decisiones de este sistema. La unicidad y coordinación de escritores se apoyan en restricciones y transacciones de la base; no requieren el bloqueo de archivo cooperativo que añadimos al prototipo de LanceDB. La extensión vectorial y la combinación de resultados siguen teniendo un contrato de mantenimiento propio.

Mario autorizó "realiza una prueba con sqlite y plugin vectorial". Es una comparación local, sin instalación de un backend activo ni aprobación integral de la spec.

## Resultados y comparación

| Contrato | SQLite y sqlite-vec | Evidencia previa de LanceDB |
|---|---|---|
| Dos procesos capturan observaciones distintas | Tres tandas de 60, con todos los IDs y su procedencia conservados. | Tres tandas de 60 conservadas, tanto nativo como con adaptador. |
| Cuatro capturas secuenciales de la misma operación | Una confirmación y tres already-captured; una fila. | Una fila en ambas variantes. |
| Dos reintentos simultáneos de la misma operación | Diez pares dejan una fila; una confirmación y un reconocimiento por par. | Nativo deja dos filas en diez pares; el adaptador con bloqueo deja una en diez pares. |
| Dos decisiones desde revisión 0 | Diez pares producen una aceptación y un conflicto, con revisión final 1. | Mismo resultado en los diez pares de ambas variantes. |
| Captura sin embedding ni extensión cargada | Guarda y recupera original y procedencia, con vector null. | Captura y reabre sin embedding; ese ensayo sí cargó el SDK completo. |
| Lectura después del commit de otro proceso | Una nueva lectura autocommit ve la fila. Una transacción de lectura mantenida conserva su snapshot hasta terminar. | Refresco configurado ve la fila; la conexión por defecto quedó en su vista anterior. |
| SIGKILL después de anunciar un batch | En tres intentos conserva las seis confirmaciones anteriores y no deja un batch parcial. | Los tres intentos previos conservaron seis confirmaciones; los batches quedaron ausentes. |
| Interrupción dentro de una transacción abierta | Después de insertar 37 filas sin commit, SIGKILL deja sólo las seis confirmaciones previas. | No se inyectó ese punto exacto en LanceDB; no se compara como resultado equivalente. |
| Colisión de identidad o evidencia diferente | Rechaza la colisión y conserva el original. | Comprobado en el adaptador experimental, sin restricción de unicidad nativa. |
| Búsqueda vectorial, textual e híbrida | Mismas cinco observaciones y vectores fijos, con filtro de proyecto. | Las mismas comprobaciones de consulta pasaron. No se comparó relevancia. |
| Fallo al publicar embedding | Vector de dimensión incorrecta revierte esa operación y conserva el original previamente confirmado. La publicación válida posterior funciona. | Caso no ejecutado en la tanda anterior. |
| Actualización de registro e índice | Un fallo entre actualizar el vector del registro e insertarlo en el índice revierte ambas modificaciones. El caso válido publica ambas. | Caso no ejecutado en la tanda anterior. |

Los [resultados](results.json) conservan cada repetición y los eventos de interrupción. El [verificador](verify.py) reabre las bases, comprueba integridad, IDs, procedencia, unicidad, revisiones y consultas. Los [resultados de LanceDB](../2026-10-13-lancedb/results.json) y sus fuentes se enlazan mediante hashes en el [manifest](manifest.json).

## Diseño ensayado

El [adaptador experimental](sqlite_store.py) utiliza una tabla STRICT con id y operation_id no nulos y únicos. INSERT con ON CONFLICT reconoce el reintento; la comparación del contenido inmutable distingue una operación repetida de una colisión. Una operación distinta que reutiliza el ID de registro no sobrescribe el original.

Las escrituras usan transacciones BEGIN IMMEDIATE, WAL, synchronous FULL y busy_timeout de cinco segundos. SQLite serializa a los escritores. Dos agentes pueden operar simultáneamente y esperar brevemente para confirmar; esto no demuestra capacidad ilimitada ni ausencia de contención. No hay un archivo de bloqueo propio del adaptador.

La captura conserva procedencia y texto aunque no cargue sqlite-vec. Los vectores se guardan como BLOB derivados y se indexan en una tabla virtual vec0. Un embedding posterior y su índice se publican dentro de la misma transacción. La búsqueda textual usa FTS5 con un trigger que incorpora las nuevas observaciones al confirmar la captura.

La consulta híbrida no es una capacidad completa proporcionada por sqlite-vec. El prototipo combina los rankings textual y vectorial mediante RRF con constante 60 y desempate por ID. LanceDB proporciona una interfaz integrada para ese recorrido. Los dos prototipos no tienen necesariamente el mismo ranking ni la misma configuración de candidatos; se comprobó la recuperación y el filtro, no equivalencia de orden o calidad.

El prototipo incluye campos mutables de revisión en una fila sintética para comprobar actualización condicional. No implementa el historial definitivo de decisiones o anotaciones del sistema. La adopción deberá mantener originales, esquemas y decisiones anteriores, y conservar exportación legible.

## Versiones, procedencia y reproducción

- Python 3.13.2 con SQLite 3.47.1, macOS ARM y sqlite-vec 0.1.9. La identidad completa del build, binario de extensión y ejecutable Python queda en el manifest.
- Una dependencia externa directa, sin dependencias transitivas declaradas, fijada por [pyproject.toml](pyproject.toml) y [uv.lock](uv.lock). Licencias MIT/Apache-2.0 revisadas contra el tag v0.1.9. La documentación pública ya muestra una versión alpha posterior; no se instaló ni se asumieron sus características.
- Los datos sintéticos usan el mismo constructor, IDs, textos, vectores, dos escritores y repeticiones que la prueba de LanceDB. No se carga LanceDB en el entorno SQLite. Las ejecuciones fueron en días distintos; las duraciones son evidencia operativa, no un benchmark controlado.
- Bases y salidas originales permanecen en el estado privado de la tarea, bajo el Git common directory canónico, en mstack-tasks/maintenance-laya/sqlite-vector-evidence/run-01. No hay credenciales ni datos reales en el experimento.
- Cero llamadas a modelos, sin servidores ni contenedores. Los procesos creados por los runners terminaron.

Desde la carpeta del experimento, usando uv 0.10.11 ya disponible y una carpeta privada nueva:

```fish
uv sync --locked --python 3.13.2
env PYTHONDONTWRITEBYTECODE=1 uv run --locked python sqlite_probe.py --output /ruta/privada/nueva
env PYTHONDONTWRITEBYTECODE=1 uv run --locked python verify.py --raw-run /ruta/privada/nueva
```

La ejecución completa devuelve exit 0. Las tablas se crean una sola vez: usar otra carpeta para una nueva tanda. El protocolo y los hashes del código se conservan junto a los resultados.

## Límites y decisión pendiente

Esta prueba acredita una muestra de operaciones concretas en el SQLite incluido con este Python y en sqlite-vec 0.1.9. No prueba comportamiento de todas las versiones, sistemas de archivos o escalas. SIGKILL permite observar rollback y conservación de commits en los puntos ensayados; no es un ensayo de corte eléctrico. El caso de fallo entre registro e índice comprueba la atomicidad de esos cambios, no todas las fases de recuperación posibles.

sqlite-vec sigue siendo un proyecto pre-v1. El pin, compatibilidad con el runtime, actualización de índices y pruebas de migración deben formar parte de una adopción. La biblioteca estándar cubre las transacciones e integridad de datos; la extensión cubre distancia y consulta de vecinos. Ninguna clasifica observaciones por sí sola.

No hay un modelo de embeddings evaluado ni evidencia de mejora de clasificación. También siguen pendientes el historial definitivo, migración de registros existentes, exportación/backup y restauración del conjunto. Las pruebas adicionales de SQLite no se presentan como fallos de LanceDB, pues esos recorridos no se ejecutaron allí.

Recomiendo revisar SQLite con sqlite-vec como primera opción para estos registros: satisface los contratos ensayados con restricciones y transacciones propias de la base y permite consultas vectoriales locales. LanceDB conserva la ventaja de una API de recuperación integrada. La selección final se revisará en [AM-015](../../changes/AM-015-agent-maintenance.spec.md); este experimento no cambia el backend activo.

## Verificación del avance

El verificador reabrió las bases, ejecutó integrity_check y contrastó fuentes, resultados, IDs, procedencia, reintentos, revisiones, rollback y consultas. Pasó. También se comprobaron sintaxis Python, JSON, enlaces de documentos y git diff --check.

Con Bun 1.3.14, el check pasó para 30 skills y 59 Markdown; la suite terminó con 28 pass, 1 skip opcional de Portless, 0 fail y 297 aserciones en 17,18 segundos. La instalación activa `25e722daafadb2b39ea597adbc19b41632e48b4a` pasó su verificación para 30 skills y 126 destinos. Estos checks no sustituyen la aceptación de los contratos pendientes de producción.

Los [resultados de verificación](verification.json) registran el worktree propio mstack-maintenance-laya y el cwd declarado del hilo engineering-skills. La asociación del worktree en T3 sigue sin verificarse; la evidencia de Git y ejecución proviene del checkout propio indicado explícitamente.

## Fuentes técnicas

La [guía de Python](https://alexgarcia.xyz/sqlite-vec/python.html) y las [consultas KNN](https://alexgarcia.xyz/sqlite-vec/features/knn.html) documentan la extensión. Las [restricciones de SQLite](https://www.sqlite.org/lang_createtable.html) y [WAL](https://www.sqlite.org/wal.html) describen los mecanismos utilizados. Las conclusiones de esta comparación proceden de los resultados locales y se limitan a esos recorridos.
