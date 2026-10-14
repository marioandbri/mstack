# Comparación local de embeddings para mantenimiento de agentes

Mario pidió probar google/embeddinggemma-2 y Qwen/Qwen3-Embedding-0.6B. Se compararon con all-MiniLM-L6-v2 y FTS5 sobre los mismos textos y expectativas congeladas antes de inferencia.

El corpus tiene 33 registros, 26 intenciones y 52 variantes ES/EN. Hay 46 consultas con antecedente directo esperado, 23 por idioma. Las otras seis son controles de ausencia o ámbito. Las cinco consultas ambiguas y V05, control histórico, quedan fuera de puntuación. Los juicios siguen propuestos, sin aprobación independiente. Esta ejecución no es una evaluación de agentes realizando los escenarios.

## Búsqueda vectorial y referencia léxica

| Modelo o referencia | ES directo @1 / @3 | EN directo @1 / @3 | nDCG @5 | Embedding de consulta p50 / p95, ms | RSS máximo muestreado, GiB |
|---|---|---|---|---|---|
| FTS5 | 21/23 / 23/23 | 13/23 / 17/23 | 0.733 | No genera embeddings | No medido |
| sentence-transformers/all-MiniLM-L6-v2 | 14/23 / 18/23 | 13/23 / 16/23 | 0.601 | 19.4 / 41.2 | 0.51 |
| google/embeddinggemma-2 | 18/23 / 23/23 | 19/23 / 23/23 | 0.834 | 71.7 / 84.1 | 1.25 |
| Qwen/Qwen3-Embedding-0.6B | 21/23 / 23/23 | 20/23 / 23/23 | 0.876 | 153.4 / 231.9 | 2.52 |

Un acierto directo requiere grado 2. El grado 1 aporta contexto y no cuenta como acierto directo. nDCG incorpora ambos grados con ganancias 3 y 1. Los porcentajes de idioma usan 23 consultas; las traducciones del mismo caso no son incidentes independientes.

Qwen recuperó primero el antecedente directo en 41/46 consultas, Gemma en 37/46 y MiniLM en 27/46. Qwen obtuvo más primeros resultados directos en esta muestra. Gemma consumió aproximadamente la mitad de RSS y tuvo menor mediana de generación de consulta en esta pasada. Ambos recuperaron todos los directos esperados entre los tres primeros. Son candidatos para ampliar la evaluación, sin adopción de producción.

El tiempo de consulta de la tabla mide sólo generación local del embedding, con una consulta por llamada después de calentamiento. RSS incluye el proceso Python, bibliotecas y pesos cargados; se muestrea cada 50 ms. Son mediciones de una pasada en Apple M1 Pro de 16 GiB, CPU con cuatro threads y float32. Descarga y carga quedan separadas en results.json. No se midió capacidad de producción ni aceleración GPU.

MiniLM y Qwen conservaron exactamente sus rankings y métricas del intento anterior. La mediana de MiniLM cambió de 6,9 a 19,4 ms y la de Qwen de 139,0 a 153,4 ms entre los intentos. El entorno de dependencias también cambió. No se aisló el efecto de ese cambio ni de la actividad del sistema; los tiempos son referencias de estas pasadas, no un benchmark controlado de latencia.

## Búsqueda híbrida

FTS5 usa BM25 sobre todos los tokens Unicode de la consulta, unidos con OR, sin afinar stopwords con las etiquetas. La búsqueda híbrida aplica RRF de pesos iguales, constante 60 y diez candidatos por rama. Es combinación del adaptador de evaluación, no una propiedad de sqlite-vec.

| Modelo | Vector @1 / @3 / @5, de 46 | Híbrido @1 / @3 / @5, de 46 | nDCG vector / híbrido @5 |
|---|---|---|---|
| sentence-transformers/all-MiniLM-L6-v2 | 27 / 34 / 35 | 30 / 36 / 41 | 0.601 / 0.690 |
| google/embeddinggemma-2 | 37 / 46 / 46 | 39 / 45 / 45 | 0.834 / 0.837 |
| Qwen/Qwen3-Embedding-0.6B | 41 / 46 / 46 | 42 / 44 / 45 | 0.876 / 0.858 |

La combinación de pesos iguales mejora algunos primeros resultados y pierde algunos directos en top 3/top 5 frente a la búsqueda vectorial de Gemma y Qwen. No se ajustaron pesos después de observar las etiquetas; esta prueba no justifica elegir esa combinación como configuración final.

## Controles sin antecedente

| Modelo | C17/C18 sin antecedente | Distancia coseno del primer candidato | Fuga de ámbito C16 |
|---|---|---|---|
| sentence-transformers/all-MiniLM-L6-v2 | 4/4 devuelven candidatos | 0.458 a 0.810 | 0/6 resultados de los tres métodos |
| google/embeddinggemma-2 | 4/4 devuelven candidatos | 0.254 a 0.365 | 0/6 resultados de los tres métodos |
| Qwen/Qwen3-Embedding-0.6B | 4/4 devuelven candidatos | 0.527 a 0.574 | 0/6 resultados de los tres métodos |

C17 busca exposición de una clave secreta y C18 un fallo de cálculo de IVA. No hay esos incidentes en el corpus. Los vecinos devueltos son candidatos, no confirmaciones. No se fijó un umbral de abstención ni se convierte una distancia en probabilidad calibrada. C16 tiene cero candidatos por proyecto; se informa aparte y no se cuenta como acierto semántico.

## Primeros resultados que no eran directos

| Modelo | Consulta | Primero recuperado | Directo esperado |
|---|---|---|---|
| minilm | C01-es | R12 | R01 |
| minilm | C01-en | R31 | R01 |
| minilm | C02-en | R23 | R02 |
| minilm | C03-es | R02 | R08 |
| minilm | C03-en | R23 | R08 |
| minilm | C06-es | R17 | R04 |
| minilm | C06-en | R07 | R04 |
| minilm | C07-en | R18 | R14 |
| minilm | C08-es | R17 | R16 |
| minilm | C08-en | R10 | R16 |
| minilm | C10-es | R02 | R25 |
| minilm | C10-en | R08 | R25 |
| minilm | C11-es | R12 | R26 |
| minilm | C12-es | R06 | R28 |
| minilm | C13-es | R17 | R29 |
| minilm | C15-es | R09 | R05 |
| minilm | C15-en | R09 | R05 |
| minilm | C22-en | R31 | R32 |
| minilm | C25-en | R10 | R32 |
| gemma | C01-en | R10 | R01 |
| gemma | C02-es | R08 | R02 |
| gemma | C03-es | R02 | R08 |
| gemma | C03-en | R02 | R08 |
| gemma | C06-es | R08 | R04 |
| gemma | C08-es | R10 | R16 |
| gemma | C08-en | R10 | R16 |
| gemma | C12-en | R06 | R28 |
| gemma | C21-es | R15 | R32 |
| qwen | C02-en | R01 | R02 |
| qwen | C10-es | R08 | R25 |
| qwen | C10-en | R08 | R25 |
| qwen | C14-es | R24 | R23 |
| qwen | C14-en | R24 | R23 |

Las consultas, IDs esperados y grados completos están en el [corpus congelado de origen](../2026-10-14-embedding-corpus/review.md) y los rankings en [results.json](results.json). Compartir tema o ser un contexto útil no satisface el objetivo directo de la consulta.

## Configuración y procedencia

- sentence-transformers/all-MiniLM-L6-v2, revisión 1110a243fdf4706b3f48f1d95db1a4f5529b4d41, 384 dimensiones, 22,713,216 parámetros cargados. Máximo documental 219 tokens; 0 documentos superan el límite nativo 256.
- google/embeddinggemma-2, revisión 914f7f89142e33e77833254d9c9b90c3cef7303b, 768 dimensiones, 271,002,624 parámetros cargados. Máximo documental 137 tokens; 0 documentos superan el límite nativo 8192.
- Qwen/Qwen3-Embedding-0.6B, revisión 97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3, 1024 dimensiones, 595,776,512 parámetros cargados. Máximo documental 171 tokens; 0 documentos superan el límite nativo 32768.

EmbeddingGemma 2 carga sólo texto, con vision_config y audio_config desactivados, y usa los prefijos query/document. Qwen usa su instrucción query y documento sin prefijo. MiniLM usa texto sin prefijos. Se conserva el texto completo de cada registro como entrada; los nombres, grados, razones del juez y fuentes no se añaden. Los prefijos son constantes del modelo. Todos los vectores son float32, finitos y normalizados; cada perfil usa sus dimensiones completas.

Se respetaron las configuraciones de las [model cards de Google](https://huggingface.co/google/embeddinggemma-2), [Qwen](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) y [MiniLM](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2). Las revisiones completas y los hashes de archivos fijan lo ejecutado. Los tres checkpoints declaran Apache 2.0. El entorno de evaluación usa paquetes mantenidos de sus proyectos oficiales, versiones exactas en pyproject.toml y resolución completa en uv.lock; no instala un backend activo.

El [protocolo](protocol.json) conserva los hashes del corpus y de los scripts anteriores a ejecución, versiones, prefijos, ámbito y rúbrica. Los modelos, vectores, bases SQLite, logs y copias de fuentes se conservan fuera de Git en embedding-model-evidence del directorio privado de esta tarea. Hub sólo se usó para descarga; la inferencia se ejecutó offline y no envió textos a un proveedor.

El primer intento completó MiniLM y Qwen, pero Gemma no pudo cargar el procesador por ausencia de Pillow, antes de generar embeddings. El preflight posterior identificó también Torchvision. Se conservan como fallos de infraestructura. Tras añadir Pillow 12.3.0 y Torchvision 0.29.1 al entorno aislado se repitieron todos los perfiles; la tabla usa sólo esa repetición. El tokenizer de Gemma exponía un límite centinela indeterminado; se fijó el límite documentado de 8.192 tokens antes de la repetición. Los pesos y el corpus permanecen idénticos, sin segunda descarga. Los tiempos de descarga corresponden a la adquisición inicial, no a una segunda descarga medida.

## Verificación y límites

La comprobación independiente reabre las bases, repite las consultas vectoriales y contrasta distancias y rankings con coseno de NumPy. Verifica integridad, ámbito, vectores finitos, normalización, fuente y pesos por hash, y exclusión de consultas sin grados. La [verificación](verification.json) conserva resultados reales y los checks del repositorio.

El corpus es pequeño, de un proyecto, con consultas redactadas y escenarios agrupados. No demuestra calidad cotidiana, fiabilidad de captura, clasificación automática, deduplicación ni permisos de integración. Elegir un modelo de producción requiere más episodios independientes y una calibración separada de abstención; no se ajustan umbrales sobre este mismo conjunto.

## Reproducción

Con uv 0.10.11 y Python 3.13.2, uv sync --locked prepara el entorno. download.py recibe un directorio privado con metadata pública de las revisiones fijadas; no descarga ni ejecuta código remoto. run.py freeze conserva fuentes y protocolo antes de ejecutar. run.py execute serializa los perfiles con los mismos ajustes de proceso.

```fish
env PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 uv run --locked python run.py execute --private /ruta/privada/congelada
env PYTHONDONTWRITEBYTECODE=1 uv run --locked python verify.py --private /ruta/privada/congelada
env PYTHONDONTWRITEBYTECODE=1 uv run --locked python -m unittest -v test_ranking.py
```

Una nueva ejecución usa un directorio nuevo para conservar intentos previos. publish.py genera este informe y results.json desde la evidencia verificada; los generados se actualizan con ese script.
