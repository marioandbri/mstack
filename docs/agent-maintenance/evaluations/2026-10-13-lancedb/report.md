# LanceDB como persistencia local del sistema

LanceDB embebido resulta viable como candidato con un adaptador de captura que coordine las escrituras. El SDK de Python conservó observaciones distintas escritas en paralelo, detectó actualizaciones con revisión obsoleta y permitió búsqueda vectorial, textual e híbrida. El recorrido nativo de reintento concurrente dejó duplicados; el adaptador experimental con bloqueo local y lectura fresca evitó ese resultado en los diez pares ensayados.

Mario autorizó la prueba con "perfecto entonces hagamos la prueba con lancedb" y pidió continuar después de la interrupción. El experimento usa datos sintéticos y vectores fijos; no ejecutó modelos, instaló componentes en los agentes ni aprobó la spec completa.

## Resultados

| Caso | SDK nativo | Adaptador experimental |
|---|---|---|
| Captura sin embeddings | El original y su procedencia sobreviven al reabrir, con vector null. | Mismo resultado. |
| Dos escritores con IDs distintos | Tres tandas de 60 observaciones, todas conservadas con IDs y procedencia exactos. | Tres tandas de 60, todas conservadas. |
| Repetir una captura secuencialmente | Cuatro operaciones dejan un solo registro. | Una captura confirmada y tres respuestas already-captured. |
| Dos reintentos simultáneos del mismo ID | Diez pares dejaron dos filas cada uno; ambas operaciones informaron inserción. | Diez pares dejaron una fila cada uno, con una confirmación y un reconocimiento del registro existente. |
| Dos decisiones desde revisión 0 | Diez pares producen una actualización y un conflicto detectable, con revisión final 1. | Diez pares mantienen ese resultado. |
| Visibilidad entre procesos | La conexión por defecto siguió viendo cero filas. Refresco por lectura y refresco explícito vieron la fila confirmada por otro proceso. | Refresco configurado ve la captura de otro proceso. |
| SIGKILL después de anunciar un batch | En tres intentos se conservaron las seis filas previamente confirmadas. Las 12.000 filas del batch quedaron ausentes; no se observó un batch parcial. | Se comprobó aparte que un escritor posterior puede capturar después de matar al propietario del bloqueo. |
| Consultas con vectores fijos y filtro de proyecto | Vectorial, textual e híbrida respetan el filtro; la búsqueda textual recupera también el original sin vector. | Usa la misma capacidad de consulta; no se repitió como una prueba de calidad semántica. |
| Mismo ID con contenido u operación diferentes | No es una garantía de unicidad obtenida por merge_insert en este experimento. | Rechaza ambos conflictos y conserva el original sin modificar. |

Los [resultados completos](results.json) conservan los resultados nativos, las comprobaciones del adaptador y los eventos de interrupción. No se calcula una tasa global de fiabilidad combinando estos casos dependientes.

## Qué requiere el diseño

La captura debe disponer de una identidad de operación estable para reconocer un reintento. Ese identificador no decide si dos observaciones describen el mismo incidente: esa relación pertenece al análisis posterior. Una identidad reutilizada con evidencia diferente debe producir conflicto, no sobrescribir el original.

El [adaptador experimental](guarded_store.py) adquiere un bloqueo de archivo común antes de comprobar la identidad y escribir. Abre la tabla bajo ese bloqueo y configura refresco por lectura. El bloqueo se libera al terminar o al morir el proceso y tiene espera acotada. Es coordinación cooperativa, no una restricción de unicidad impuesta a todos los clientes de LanceDB. Un escritor que use el SDK directamente puede eludirla.

La revisión condicional emplea el número de filas actualizado que devuelve el SDK. Si la revisión ya cambió, cero filas actualizadas representa conflicto. Los casos usan una fila sintética para comprobar ese mecanismo; no implementan todavía el historial real de decisiones o la separación entre originales y anotaciones.

La captura y procedencia pueden conservarse juntas en un registro con vector ausente. La generación de embeddings debe quedar fuera de la sección de escritura coordinada. Un fallo de indexación no puede descartar una observación confirmada. Cada embedding deberá conservar el modelo, versión y hash de la entrada que lo produjo; esa parte queda por implementar.

## Condiciones y reproducción

- Python 3.13.2, LanceDB 0.40.0, macOS ARM y almacenamiento local. PyArrow 26.0.0, NumPy 2.5.4 y Pydantic 2.14.1; dependencias completas fijadas por [uv.lock](uv.lock).
- SDK tomado de PyPI; licencia Apache-2.0 comprobada contra el tag v0.40.0. El [manifest](manifest.json) conserva hashes de licencia, fuentes, protocolo, lockfile y resultados. Es una dependencia del experimento, sin importación de skills ni cambios de instalación activa.
- Dos procesos independientes mediante spawn. La barrera sincroniza el comienzo de cada operación después de abrir las tablas. Tres tandas de append, diez de reintento y diez de revisión por variante, cuatro reintentos secuenciales y tres interrupciones.
- Las bases y copias congeladas de fuentes permanecen en el estado privado de la tarea, bajo el Git common directory canónico, en mstack-tasks/maintenance-laya/lancedb-evidence/run-01. Los artefactos compartidos contienen sólo datos sintéticos.
- Ningún servidor, contenedor, modelo alojado o servicio de embeddings. No quedaron procesos propios en ejecución al terminar los runners.

Desde la carpeta del experimento, usando el uv 0.10.11 ya disponible:

```fish
uv sync --locked --python 3.13.2
env PYTHONDONTWRITEBYTECODE=1 uv run --locked python probe.py --output /ruta/privada/nueva
env PYTHONDONTWRITEBYTECODE=1 uv run --locked python probe.py --mode guarded --case concurrent_retry --case conflicting_revision --case concurrent_append --case sequential_retry --case capture_without_embedding --case reader_freshness --output /ruta/privada/nueva
env PYTHONDONTWRITEBYTECODE=1 uv run --locked python adapter_checks.py --output /ruta/privada/nueva
```

La primera orden de ejecución devuelve exit 1 por el contrato de reintento concurrente incumplido. Ese fallo queda conservado como resultado del experimento; no debe ocultarse para hacer pasar la comparación. Las dos ejecuciones del adaptador devolvieron exit 0. La ruta debe estar vacía antes de iniciar el recorrido y ser común a las tres ejecuciones; cada variante crea sus propias tablas.

## Límites y recomendación

La prueba acredita operaciones del SDK Python 0.40.0 en este Mac. No establece comportamiento del SDK JavaScript ni de otros sistemas de archivos. Las diez reproducciones de duplicados son incidentes sintéticos del mismo mecanismo, no diez fricciones independientes de uso cotidiano ni un diagnóstico de la causa interna de LanceDB.

El SIGKILL se envió después de una notificación anterior al método público add, con retrasos de 0, 5 y 20 ms. No se inyectó en una fase exacta del commit. Los tres batches quedaron ausentes. Esto comprueba conservación de confirmaciones anteriores en esos intentos, no resistencia a corte eléctrico o todos los puntos posibles de fallo.

Los vectores se escogieron manualmente para comprobar la consulta. La consulta híbrida devolvió también un vecino sin la palabra buscada; sus resultados no acreditan relevancia semántica ni mejora de clasificación. Sigue pendiente evaluar un modelo multilingüe y medir recuperación de antecedentes relevantes y falsas asociaciones.

No se probaron transacciones entre tablas, migración de registros existentes, backup y restauración, recuperación de índices o rendimiento con un corpus grande. El prototipo utiliza el alias create_fts_index, que el SDK marcó como obsoleto; la implementación deberá usar la API vigente create_index con configuración FTS.

La recomendación es conservar LanceDB como candidato preferido para una persistencia embebida única y convertir la coordinación de escritores, idempotencia y detección de conflictos en requisitos del adaptador. La selección definitiva necesita resolver y verificar historial, migración y recuperación. La [spec AM-015](../../changes/AM-015-agent-maintenance.spec.md) sigue siendo un borrador; esta prueba no instala su solución.

## Verificación del avance

El [verificador](verify.py) reabrió las bases y contrastó hashes, resultados, IDs, procedencia, duplicados nativos, unicidad del adaptador y conflictos de revisión. Pasó. Los enlaces de los documentos y los 48 relatos de usuario y 29 criterios de AM-015 también se comprobaron; git diff --check pasó.

Con Bun 1.3.14, el check del repositorio pasó para 30 skills y 59 Markdown. La primera suite terminó con 27 pass, 1 skip y un timeout en la integración del instalador. Su repetición aislada pasó en 13,28 segundos y la segunda suite completa terminó con 28 pass, 1 skip opcional de Portless, 0 fail y 297 aserciones en 16,33 segundos. No se atribuye una causa al timeout ni se elimina ese intento.

La verificación de instalación pasó para 30 skills y 126 destinos. Durante el trabajo una actualización externa cambió el commit activo a `25e722daafadb2b39ea597adbc19b41632e48b4a`. El global sigue coincidiendo con este worktree y el entrypoint de repository-workflow cambió. Esta tarea no realizó esa instalación. La prueba de almacenamiento no carga skills ni depende de ese cambio.

Los cambios están en el worktree propio mstack-maintenance-laya. El entorno del hilo continúa declarando engineering-skills como cwd; no hay una herramienta expuesta para verificar o cambiar su asociación de worktree en T3. La evidencia de Git procede explícitamente del worktree propio, sin afirmar que los diffs o checkpoints del hilo lo sigan. Los [resultados de verificación](verification.json) conservan ambos paths y estados.

## Fuentes técnicas

La [documentación de consistencia](https://docs.lancedb.com/tables/consistency) explica el refresco entre procesos y la [búsqueda híbrida](https://docs.lancedb.com/search/hybrid-search) describe el recorrido local utilizado. El [SDK](https://pypi.org/project/lancedb/0.40.0/) y la [licencia de su tag](https://github.com/lancedb/lancedb/blob/v0.40.0/LICENSE) identifican el componente probado. Las conclusiones de compatibilidad anteriores proceden de nuestras ejecuciones, no de asumir garantías del marketing o del reporte histórico de otro SDK.
