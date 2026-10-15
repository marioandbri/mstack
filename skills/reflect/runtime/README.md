# Registros locales

Este adaptador guarda originales de observaciones en SQLite. El original mantiene el esquema vigente y sus bytes. Procedencia y estados se guardan aparte. No llama a modelos, clasifica, abre Reflect ni instala instrucciones.

Usar uv 0.10.11 con Python 3.13.2 y las versiones de pyproject.toml y uv.lock. Desde el repositorio canónico:

```fish
uv run --locked --project skills/reflect/runtime python skills/reflect/runtime/record_cli.py --database /ruta/proyecto/docs/agent-maintenance/.records/records.sqlite3 --project proyecto-estable capture --operation operacion-estable --original /ruta/observacion.json --provenance /ruta/procedencia.json
```

database es una ruta explícita. Dos agentes del mismo proyecto, incluidos worktrees distintos, deben usar esa misma base y el mismo identificador estable de project. No derivar otro identificador de la sesión ni crear una base alternativa ante un conflicto. Una base con otro project se rechaza. No hay agregación entre proyectos.

La captura inicializa la base cuando hace falta. Los directorios nuevos y la base tienen permisos privados. Si el directorio de la base permite escritura a otros usuarios, o el archivo existente no es privado, el helper se detiene. Las lecturas de una base inexistente no crean archivos.

La carpeta .records contiene datos locales, no instrucciones ni archivos para instalar. Al ejecutar desde un snapshot de skill de sólo lectura, indicar UV_PROJECT_ENVIRONMENT mediante env hacia un entorno privado escribible; no cambiar permisos del snapshot. El intérprete y las dependencias siguen fijados por el mismo lockfile.

## Original y procedencia

original contiene un JSON que cumple [el esquema de observación](../observation.schema.json). El productor prepara evidencia mínima saneada antes de guardar. No incluir credenciales ni transcripciones completas. El adaptador valida el esquema y no reescribe el original.

La procedencia opcional separa origen y captura:

```json
{
  "origin": [{"harness": "pi", "session_id": "sesion-origen", "event_id": "turno-7"}],
  "capture": {"harness": "codex", "session_id": "sesion-captura"}
}
```

Cada identidad admite harness, harness_version, session_id, event_id, turn_id, timestamp y references. Los campos desconocidos se conservan como null y las referencias como lista. No se inventan IDs. origin admite varias fuentes; una sesión por sí sola no demuestra recurrencia. La fecha captured_at es la de la escritura confirmada por este adaptador.

Una operación se identifica antes de guardarla. Reintentar los mismos bytes y procedencia con el mismo operation devuelve already-captured. Cambiar su contenido devuelve operation-conflict; otro operation con el mismo ID devuelve identity-conflict. Ningún conflicto reemplaza el original. Ante pérdida del acuse, consultar por ID o reintentar la misma operación; un error de transporte no prueba que el commit se perdió.

## Consulta y estado

El mismo comando base admite get con id, list con scope y state opcionales, y history con id y kind. get devuelve la observación legible, raw_base64, hash, procedencia, estado y trabajo derivado pendiente. No exige embeddings, clasificación ni resumen.

transition requiere id, expected-revision, state, evidence y operation. evidence es un archivo JSON con answer y source que documentan la decisión del usuario. Los estados son inbox, reviewing, resolved, deferred y discarded. Una revisión obsoleta devuelve revision-conflict. Cada cambio conserva su versión; la observación original continúa con status inbox. El estado operativo no se interpreta como permiso para evaluar o instalar.

SQLite coordina las escrituras con transacciones inmediatas, restricciones, WAL y synchronous FULL. Un lote capture_many es atómico. Al morir un escritor antes del commit no queda una observación parcial; si murió después, el mismo operation permite recuperar el resultado. La espera por un escritor tiene límite de cinco segundos y devuelve un error sin descartar evidencia del llamador.

## Clasificación provisional

El mismo CLI admite classification prepare con id y related repetibles. Devuelve evidencia original, procedencia, decisiones previas, fuentes con hashes, categorías permitidas y componentes disponibles. El procedimiento del agente produce la salida de [annotation.schema.json](../annotation.schema.json); Gemma no clasifica.

classification save recibe context, output, expected-revision y operation. output puede contener null si el proveedor no respondió. La validación rechaza fuentes/versiones desconocidas, categorías no permitidas, rutas ajenas y recuentos que duplican el mismo incidente. Una relación necesita fuentes de ambos registros; una recurrencia exige incidentes independientes de ámbito equivalente. Categoría, impacto y recurrencia permanecen separados, sin pesos ni probabilidades inventados.

classification get recupera la última anotación y su estado; history con kind annotation conserva todas las versiones. Si falla una nueva clasificación, la anterior sigue disponible y el trabajo queda pendiente. La escritura usa comparación de revisión y comprueba que el contexto no haya cambiado. Un reintento confirmado no altera trabajo posterior. La sugerencia nunca autoriza entrevistas, evaluación o instalación.

## Dependencias fijadas

Se reutiliza el [esquema existente](../observation.schema.json) mediante [jsonschema 4.25.1](https://pypi.org/project/jsonschema/4.25.1/), mantenido y con licencia MIT. Evita mantener otro validador parcial. [sqlite-vec 0.1.9](https://pypi.org/project/sqlite-vec/0.1.9/) conserva el plugin ya ensayado para la búsqueda posterior; la captura no carga la extensión. La resolución completa se conserva en uv.lock. No se añaden servicios ni otros backends.
