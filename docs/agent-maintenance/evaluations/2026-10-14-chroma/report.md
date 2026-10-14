# Chroma frente a SQLite y LanceDB

Para el registro de observaciones y decisiones, la comparación sigue favoreciendo SQLite con sqlite-vec. Chroma 1.5.9 recupera los vectores fijos y conserva los reintentos por ID en esta muestra, pero no guarda el original sin embedding cuando la función de embeddings está desactivada. La lectura seguida de update tampoco detecta una revisión concurrente. Un adaptador que serializa el acceso resolvió las revisiones y colisiones ensayadas; la captura sin embedding siguió fallando.

Mario autorizó esta comparación después de las pruebas de LanceDB y SQLite. Se usó Chroma embebido, sin servidor, modelos ni datos reales. La elección definitiva sigue pendiente de revisar AM-015.

## Comparación de los recorridos

| Contrato | SQLite 3.47.1 y sqlite-vec 0.1.9 | LanceDB 0.40.0 | Chroma 1.5.9 |
|---|---|---|---|
| Captura antes de generar embeddings | Conserva original y procedencia, incluso sin cargar la extensión. | Conserva original sin vector. | Rechaza documentos con embedding_function desactivada y sin vector. |
| Dos procesos escriben observaciones distintas | Tres tandas de 60 completas, coordinadas por SQLite. | Tres tandas de 60 completas. | Tres tandas de 60 completas en ambas variantes. El acceso nativo concurrente al mismo directorio no es un despliegue soportado. |
| Reintento simultáneo de la misma identidad | Diez pares dejan una fila, con reconocimiento del reintento. | Nativo duplica en diez pares; adaptador cooperativo conserva una fila. | Diez pares dejan una fila. add nativo devuelve sin distinguir inserción y repetición; el adaptador reconoce el reintento. |
| Dos decisiones desde revisión 0 | Diez pares con una aceptación y un conflicto. | Diez pares con una aceptación y un conflicto. | Lectura seguida de update acepta ambas en diez pares. Acceso serializado produce una aceptación y un conflicto en diez pares. |
| Identidad reutilizada con otro contenido | Rechaza la colisión y conserva el original. | El adaptador rechaza la colisión. | add conserva el original y devuelve sin error. El adaptador detecta la colisión. |
| Recuperación con filtro de proyecto | Vector, FTS5 y RRF aportado por el adaptador. | API vectorial, textual e híbrida integrada. | Vector y filtro de substring; combinación de filtros, sin fusión de rankings ensayada. |
| SIGKILL tras anuncio público del batch | Seis confirmaciones conservadas; batch de 12.000 ausente en tres intentos. | Igual resultado observado para batches de 12.000. | Seis confirmaciones conservadas; batch de 5.461 ausente en tres intentos por variante, limitado por el SDK. |
| Transacción interrumpida y publicación atómica del índice | Se verificaron rollback dentro de una transacción y fallo entre registro e índice. | No se ejecutaron esos casos. | No se ejecutaron esos casos. Un vector con dimensión inválida dejó intacto el registro ya indexado. |

La [evidencia de Chroma](results.json) conserva siete casos nativos que pasan y tres brechas del contrato. Con acceso serializado pasan nueve y queda la captura sin embedding. No hubo errores de infraestructura. Los exit codes de ambos runners son 1 porque conservan esas brechas. Los números de casos no son una puntuación comparable entre bases: SQLite incluyó recorridos adicionales.

La conservación del reintento nativo de Chroma se comprobó usando el mismo ID de registro y operación. No acredita una restricción de unicidad independiente sobre operation_id. La [documentación de add](https://docs.trychroma.com/docs/collections/add-data) explica que un ID existente se ignora sin error; reconocer una operación repetida o rechazar contenido incompatible sigue siendo responsabilidad del adaptador.

## Acceso local y API probados

El [protocolo](protocol.json) compara dos procesos SDK simultáneos con un control de acceso serializado. La [documentación de restricciones](https://cookbook.chromadb.dev/core/system_constraints/) declara que varios escritores de distintos procesos sobre una misma ruta local no son seguros. Que la muestra nativa conserve sus filas no cambia esa condición.

En el control, un coordinador mantiene flock durante toda la vida de cada proceso SDK, incluida inicialización, operaciones, close público y salida. El siguiente SDK se abre después. Las comprobaciones de identidad y revisión ocurren dentro de ese turno. El control depende de que todos los escritores cooperen y no ensaya la caída del coordinador con un hijo todavía activo. No es un adaptador de producción ni un servicio permanente.

La [referencia Python actual](https://docs.trychroma.com/reference/python/collection) ya menciona transacciones conditional. La [inspección de la API instalada](api-surface.json) confirma que Collection de 1.5.9 no expone conditional y que update no recibe una condición de revisión. Por eso el resultado se limita a esta versión y a la lectura seguida de update probada, sin afirmar que todas las versiones de Chroma carezcan de transacciones condicionales.

La captura sin embedding se probó expresamente, sin sustituirlo por un vector ficticio. Los demás casos de almacenamiento usan vectores fijos de tres dimensiones para aislar la persistencia. La consulta reutiliza cuatro observaciones del corpus anterior; excluye y registra la quinta, cuyo vector era null. Estas diferencias impiden presentar las tandas como idénticas o medir una ventaja de rendimiento.

## Reproducción y procedencia

Python 3.13.2, Chroma 1.5.9 y uv 0.10.11 quedaron fijados en [pyproject.toml](pyproject.toml) y [uv.lock](uv.lock). El entorno aislado contiene 84 distribuciones instaladas. Se revisó Apache-2.0 contra el tag de esa versión; el [manifest](manifest.json) conserva licencia, wheel, binario nativo, runtime y hashes de fuentes y resultados previos. No se añadió Chroma al instalador ni a la captura activa.

Las bases, fuentes congeladas y logs originales permanecen en el Git common directory canónico, bajo mstack-tasks/maintenance-laya/chroma-evidence/run-01. El [verificador independiente](verify.py) contrasta los hashes y vuelve a abrir las 64 bases. Las fallas esperadas siguen siendo fallas del contrato aunque se verifique correctamente su evidencia.

Desde la carpeta del experimento, con uv 0.10.11 y una ruta privada nueva:

```fish
uv sync --locked --python 3.13.2
env PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 uv run --locked python chroma_probe.py --output /ruta/privada/nueva
env PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 uv run --locked python chroma_probe.py --output /ruta/privada/nueva --mode serialized-owner
env PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 uv run --locked python verify.py --raw-run /ruta/privada/archivada
```

Los dos runners devuelven 1 por los contratos pendientes. El verificador contrasta los resultados publicados con la carpeta original archivada; una tanda nueva necesita conservar su propio manifest y resultados. Usar otra carpeta para repetir el ensayo, pues las colecciones se crean una sola vez.

## Decisión pendiente

SQLite encaja mejor con captura duradera antes de indexar, idempotencia y decisiones transaccionales sin un servicio. LanceDB conserva la ventaja de recuperación integrada, con coordinación propia en el adaptador. En este ensayo Chroma exige más adaptación para ser el registro principal. Sus consultas vectoriales pasaron; no se demostró una mejora de relevancia o clasificación sobre las otras opciones.

Ninguna de estas pruebas elige un modelo de embeddings ni acredita calidad semántica. SIGKILL no prueba corte eléctrico y el ensayo de Chroma no inyecta fallos en una fase exacta de commit. Historial, migración, backup y restauración siguen pendientes. Los ensayos previos de [SQLite](../2026-10-14-sqlite-vector/report.md) y [LanceDB](../2026-10-13-lancedb/report.md) conservan sus propias condiciones. La [spec AM-015](../../changes/AM-015-agent-maintenance.spec.md) reúne la decisión que debe revisarse antes de dividir la implementación en tickets.

## Verificación del avance

El verificador pasó al reabrir las 64 bases y contrastar integridad, originales, procedencia, reintentos, revisiones, interrupciones, consultas y fuentes. Se comprobaron también sintaxis Python, JSON, URLs del lockfile, enlaces relativos y las 48 historias y 29 criterios de la spec. Las brechas de Chroma permanecen registradas; verificar la evidencia no las convierte en contratos satisfechos.

Con Bun 1.3.14, bun run check pasó para 30 skills y 59 Markdown; bun test terminó con 28 pass, 1 skip opcional de Portless, 0 fail y 297 aserciones en 17,95 segundos. fish install/verify.fish verificó la instalación activa 25e722daafadb2b39ea597adbc19b41632e48b4a, con 30 skills y 126 destinos. Los [resultados de verificación](verification.json) conservan estos límites y el worktree propio mstack-maintenance-laya. La asociación de ese worktree en T3 sigue sin verificarse; Git y los comandos se ejecutaron sobre su ruta explícita.
