# Chroma con su función de embeddings por defecto

Chroma 1.5.9 acepta documentos sin vectores suministrados cuando se crea la colección como indica la documentación, sin especificar embedding_function. Descargó automáticamente all-MiniLM-L6-v2 y generó embeddings locales de 384 dimensiones. La captura y query_texts funcionaron. El rechazo del informe anterior corresponde a embedding_function=None y no describe la captura automática normal.

Mario autorizó esta nueva configuración, incluida la descarga y ejecución local del modelo. Se reutilizó el entorno bloqueado de la prueba anterior, sin servidor ni llamadas a modelos alojados. No se activó un backend de producción.

## Configuración comprobada

```python
collection = client.create_collection(name="observations")
collection.add(ids=["origin-001"], documents=["Approval was requested again after it had been granted."])
collection.query(query_texts=["The agent asked for permission twice."], n_results=1)
```

Los ensayos añaden metadata de procedencia y desactivan telemetría. No pasan embeddings a add ni query_embeddings a las consultas. La configuración persistida contiene la función default y distancia L2. El [bootstrap](bootstrap.json) confirma que el cache privado estaba vacío antes del primer add, el archivo descargado de 83.178.821 bytes y su hash esperado por el SDK. Los archivos extraídos, incluidos modelo ONNX y tokenizer, quedan identificados por hashes.

Sólo se redirigió DOWNLOAD_PATH de la clase ONNX del SDK a almacenamiento privado de la tarea, dentro de cada proceso. Es un ajuste de cache específico de esta versión; no cambia el modelo, algoritmo, parámetros de colección ni archivos del SDK. El cache normal del usuario permanece ajeno al ensayo.

La [documentación de Chroma](https://docs.trychroma.com/docs/embeddings/embedding-functions) describe la selección y descarga automática. La [ficha del modelo](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) identifica licencia Apache-2.0, vectores de 384 dimensiones y lenguaje inglés. ONNX Runtime 1.31.0 y tokenizers 0.23.3 ya estaban en el lockfile de Chroma 1.5.9; no se añadió otra dependencia.

## Recuperación con texto real

El [corpus y rúbrica](corpus.json) se fijaron antes de ejecutar las consultas: diez documentos sintéticos, ocho consultas y dos antecedentes equivalentes por tema, uno inglés y otro español. Dos documentos de otro proyecto prueban el filtro. query_texts genera el vector de la consulta con la función por defecto.

| Lenguaje de consulta | Consultas | Antecedente relevante primero | Antecedente relevante entre los tres primeros | Recall medio de los dos antecedentes entre los tres primeros |
|---|---:|---:|---:|---:|
| Inglés | 4 | 3 | 4 | 0,5 |
| Español | 4 | 2 | 4 | 0,5 |

Ningún resultado se salió del proyecto. Las consultas sobre alcance en inglés y sobre referencias y alcance en español ordenaron antes otro tema. Las consultas recuperaron una versión lingüística del antecedente, pero no las dos entre los tres primeros. No se presenta esta muestra como validación multilingüe ni como clasificador.

Ambas variantes dieron los mismos IDs, métricas y orden en esta muestra. Los [resultados](results.json) conservan distancias y expectativas por consulta.

Este ensayo acredita recuperación usando embeddings reales en Chroma. SQLite y LanceDB no se ejecutaron con este corpus y modelo, por lo que no hay un ganador entre bases en calidad semántica o rendimiento. Elegir un modelo para el uso habitual, especialmente en español, sigue requiriendo un corpus mayor y revisado.

## Persistencia y separación de etapas

La captura automática pasa el recorrido de documentos sin embeddings suministrados. Es distinto de guardar el original antes de ejecutar el modelo. Una excepción local deliberada en la etapa de embedding impidió que add persistiera el registro: quedaron cero filas. La configuración normal no sufrió una interrupción del modelo; el fallo se inyectó en un proceso desechable para comprobar esa frontera. La captura independiente de embeddings sigue necesitando diseño en el adaptador.

Los casos se fijaron en el [protocolo](protocol.json), con los mismos dos escritores, tres tandas de 60 observaciones y diez pares de reintentos y revisiones. Los originales no llevan vectores fijos. El SIGKILL ocurre después del anuncio público del batch, que ahora incluye inferencia antes de escritura; no se supone una fase exacta del commit.

| Recorrido | Acceso nativo | Acceso serializado |
|---|---|---|
| Documentos sin vectores suministrados | Original y vector generado recuperables. | Mismo resultado. |
| Capturas paralelas distintas | Tres tandas de 60 completas. | Tres tandas de 60 completas. |
| Reintentos simultáneos | Diez pares dejan una fila por identidad. | Diez pares dejan una fila y reconocen el reintento. |
| Decisiones desde revisión 0 | Los diez pares aceptan ambas decisiones. | Los diez pares producen una aceptación y un conflicto. |
| Colisión de identidad/contenido | Conserva el original y devuelve sin error. | Detecta la colisión y conserva el original. |
| Nueva lectura y vector inválido | Reabre datos confirmados; dimensiones inválidas no sobrescriben. | Mismo resultado. |
| SIGKILL tras anuncio del batch | Seis confirmaciones conservadas y batch de 5.461 ausente en tres intentos. | Mismo resultado en tres intentos. |
| Excepción inyectada antes de generar embedding | Cero filas nuevas. | Cero filas nuevas. |

Son once casos por variante: ocho pasan y tres revelan contratos pendientes en el acceso nativo; diez pasan y queda la captura independiente del modelo en el control serializado. Los runners no tuvieron errores de infraestructura. Esta cuenta incluye un caso de fallo nuevo y no es una puntuación comparable con las tandas anteriores.

La restricción documentada de [varios procesos escribiendo sobre una misma ruta local](https://cookbook.chromadb.dev/core/system_constraints/) sigue aplicando. La función de embeddings no cambia la coordinación de escritores ni el contrato de revisión. El control de acceso serializado conserva las condiciones y límites del ensayo anterior.

## Evidencia y reproducción

El primer bootstrap terminó la descarga, captura y consulta, pero falló al publicar JSON porque collection.configuration contiene un objeto DefaultEmbeddingFunction. Se conserva el [intento fallido](bootstrap-attempt.json), sus fuentes y log privados. La recuperación usa configuration_json y reabre el registro confirmado sin repetir la descarga. El tiempo frío quedó null porque no fue guardado; no se reconstruyó ni presentó el intento como una ejecución limpia del recolector.

Las fuentes congeladas, bases, modelo y logs están en el Git common directory canónico, bajo mstack-tasks/maintenance-laya/chroma-default-evidence/run-01. El modelo permanece fuera de Git. El [verificador](verify.py) contrasta archivos y operaciones mediante nuevas lecturas SDK, sin reutilizar el actor escritor.

El [manifest](manifest.json) fija fuente de ejecución, código, corpus, SDK y lockfile reutilizados, binarios, licencia, modelo descargado y resultados. La revisión de licencia usa una ficha del repositorio del modelo en un commit identificado; el archivo ONNX separado se fija por su hash, sin atribuirle ese commit por inferencia.

Desde esta carpeta, usando uv 0.10.11 y el entorno bloqueado de la prueba de Chroma:

```fish
uv sync --locked --project ../2026-10-14-chroma --python 3.13.2
env PYTHONDONTWRITEBYTECODE=1 uv run --locked --project ../2026-10-14-chroma python bootstrap.py --output /ruta/privada/nueva
env PYTHONDONTWRITEBYTECODE=1 uv run --locked --project ../2026-10-14-chroma python default_probe.py --output /ruta/privada/nueva
env PYTHONDONTWRITEBYTECODE=1 uv run --locked --project ../2026-10-14-chroma python default_probe.py --output /ruta/privada/nueva --mode serialized-owner
env PYTHONDONTWRITEBYTECODE=1 uv run --locked --project ../2026-10-14-chroma python verify.py --raw-run /ruta/privada/archivada
```

Los runners mantienen exit 1 cuando detectan contratos pendientes. El verificador compara los resultados publicados con el run archivado; una nueva ejecución conserva sus propios resultados y manifest. No hace falta instalar sentence-transformers ni descargar PyTorch: la función predeterminada probada utiliza el modelo ONNX del SDK.

## Verificación del avance

El verificador pasó al reabrir 67 bases, comprobar fuentes, intento recuperado y modelo, regenerar vectores de muestra y repetir las consultas. Los contratos pendientes conservan su estado. El primer fallo de publicación queda en [OBS-CHROMA-ARTIFACT-RECOVERY-001](../../inbox/OBS-CHROMA-ARTIFACT-RECOVERY-001.json), fuera de instrucciones activas.

Con Bun 1.3.14, bun run check pasó para 30 skills y 59 Markdown. bun test terminó con 28 pass, 1 skip opcional de Portless, 0 fail y 297 aserciones en 15,84 segundos. fish install/verify.fish verificó la instalación activa 25e722daafadb2b39ea597adbc19b41632e48b4a, con 30 skills y 126 destinos. También pasaron el esquema de la observación, sintaxis Python, JSON, fuentes congeladas y enlaces; se conservaron 48 historias y 29 criterios en la spec.

Los [resultados de verificación](verification.json) registran el worktree propio mstack-maintenance-laya y el cwd del hilo engineering-skills. La asociación en T3 sigue sin verificarse; los comandos y cambios apuntan explícitamente al worktree propio. Este avance no instala el backend ni aprueba la spec.
