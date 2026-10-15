# Recuperación local

Los originales y las decisiones son durables; FTS5 y los vectores son índices reconstruibles. No hay un servidor ni búsqueda entre proyectos. [El contrato aprobado](../../../docs/agent-maintenance/changes/AM-015-agent-maintenance.spec.md) mantiene clasificación y decisiones fuera del ranking.

Desde el CLI de registros, index text crea o reconstruye FTS5; las capturas posteriores lo actualizan en la misma transacción. search con text, scope, state, category y limit devuelve IDs, hashes y texto coincidente. Sin índice textual usa los originales e informa text-fallback. get sigue leyendo por ID, sin modelo ni extensión vectorial. El filtro category sólo usa anotaciones actuales no pendientes.

## Embeddings

index vectors requiere model-path explícito al snapshot local aceptado y el extra embeddings del entorno uv. El [perfil fijado](embedding_profile.json) conserva modelo, revisión, hashes de los archivos, 768 dimensiones, L2, coseno, 2048 tokens y ambos prefijos. La entrada es únicamente observation.observation; no se añaden metadata, títulos, resúmenes ni etiquetas. El proveedor verifica los archivos antes de cargar pesos locales, sin código remoto ni descarga implícita. Registra tokens y truncamiento. La ventana y los prefijos corresponden a la [model card de Google](https://huggingface.co/google/embeddinggemma-300m).

```fish
env HF_HUB_OFFLINE=1 uv run --locked --extra embeddings --project skills/reflect/runtime python skills/reflect/runtime/record_cli.py --database /ruta/records.sqlite3 --project proyecto index vectors --model-path /ruta/snapshot
```

La generación ocurre fuera de la transacción de escritura. La publicación comprueba entrada y perfil, y guarda vector, metadata y versión juntos. Un reintento antiguo no sustituye una versión posterior. La captura no importa Torch ni carga sqlite-vec.

search con semantic y model-path usa [sqlite-vec](https://alexgarcia.xyz/sqlite-vec/python.html), con extensión habilitada sólo durante su carga. El coseno exacto se calcula sobre los candidatos ya filtrados. Este recorrido lineal evita perder candidatos al filtrar después de top-k; no promete rendimiento de ANN para corpus grandes. Los vectores viven en una tabla ordinaria para poder respaldar y leer originales sin cargar la extensión.

Si falla el modelo o la extensión, la consulta devuelve texto con el error y límites explícitos. index status informa IDs pendientes y actuales. index reset-vectors descarta sólo la caché y deja el trabajo pendiente; reconstruir conserva historia y decisiones. No se fusionan rankings mediante RRF por defecto.

## Evidencia y mantenimiento

La suite normal usa vectores fijos para verificar transacciones, consultas y filtros. El smoke optativo en test_search.py usa los pesos reales y el CLI; activarlo con MSTACK_GEMMA_MODEL_PATH y el extra embeddings. Conserva antes de ejecutar tres registros del corpus exploratorio: un incidente y dos contextos cercanos. Verifica una consulta positiva y mantiene como candidatos los vecinos de una consulta sin antecedente. No ajusta umbrales ni convierte las etiquetas propuestas en gold. El [informe exploratorio](../../../docs/agent-maintenance/evaluations/2026-10-14-embedding-models/report.md) conserva cobertura y asociaciones del corpus completo, sin modificar esos experimentos.

Los extras reutilizan versiones ensayadas: Sentence Transformers 6.1.0 y Transformers 5.19.0 (Apache 2.0), PyTorch 2.14.1 y Torchvision 0.29.1 (BSD), NumPy 2.5.4 (BSD) y Pillow 12.3.0 (HPND). Son dependencias mantenidas con soporte documentado del checkpoint; el lock conserva la resolución exacta. El modelo mantiene la licencia Gemma aceptada previamente por Mario. No se distribuyen pesos ni tokens. Los extras son opcionales para que captura y recuperación textual no dependan del stack de inferencia.
