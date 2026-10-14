"""Generate public tables and provenance from retained, verified local results."""
import argparse
import hashlib
import json
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(rows):
    positive = [row for row in rows if not row["expected_no_match"]]
    output = {}
    for language in ("es", "en", "all"):
        selected = [row for row in positive if language == "all" or row["language"] == language]
        output[language] = {"queries": len(selected), **{f"hit_at_{cutoff}": sum(row["metrics"][f"hit_at_{cutoff}"] for row in selected) for cutoff in (1, 3, 5)},
                            **{key: mean(row["metrics"][key] for row in selected) for key in ("recall_at_3", "recall_at_5", "mrr_at_5", "ndcg_at_5")}}
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--private", type=Path, required=True)
    args = parser.parse_args()
    private = args.private
    independent = read(private / "independent-verification.json")
    assert independent["status"] == "PASS"
    protocol = read(private / "protocol.json")
    labels = read(private / "corpus/labels.json")
    baseline = read(private / "fts5-results.json")
    result = {"schemaVersion": 1, "status": "executed-exploratory", "user_approved_labels": False, "prior_attempt": read(private / "prior-attempt.json"), "repeat_consistency": read(private / "repeat-consistency.json"), "fts5": {"summary": summarize(baseline), "queries": baseline}, "models": {}}
    downloads = read(private / "downloads.json")
    for label in protocol["model_order"]:
        actual = read(private / (label + "-result.json"))
        summaries = {method: summarize([row for row in actual["results"] if row["method"] == method]) for method in ("vector", "hybrid")}
        result["models"][label] = {**actual, "summary": summaries,
            "download": {key: downloads[label][key] for key in ("artifact_bytes", "download_seconds", "artifacts")},
            "sqlite_bytes": (private / (label + ".sqlite")).stat().st_size}
    (HERE / "results.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    table = ["| Modelo o referencia | ES directo @1 / @3 | EN directo @1 / @3 | nDCG @5 | Embedding de consulta p50 / p95, ms | RSS máximo muestreado, GiB |", "|---|---|---|---|---|---|"]
    lexical = result["fts5"]["summary"]
    table.append(f"| FTS5 | {lexical['es']['hit_at_1']}/23 / {lexical['es']['hit_at_3']}/23 | {lexical['en']['hit_at_1']}/23 / {lexical['en']['hit_at_3']}/23 | {lexical['all']['ndcg_at_5']:.3f} | No genera embeddings | No medido |")
    hybrid = ["| Modelo | Vector @1 / @3 / @5, de 46 | Híbrido @1 / @3 / @5, de 46 | nDCG vector / híbrido @5 |", "|---|---|---|---|"]
    absence = ["| Modelo | C17/C18 sin antecedente | Distancia coseno del primer candidato | Fuga de ámbito C16 |", "|---|---|---|---|"]
    failures = ["| Modelo | Consulta | Primero recuperado | Directo esperado |", "|---|---|---|---|"]
    queries = {row["id"]: row for row in labels["queries"]}
    for label, actual in result["models"].items():
        summary, resource = actual["summary"]["vector"], actual["resources"]
        table.append(f"| {actual['model']['id']} | {summary['es']['hit_at_1']}/23 / {summary['es']['hit_at_3']}/23 | {summary['en']['hit_at_1']}/23 / {summary['en']['hit_at_3']}/23 | {summary['all']['ndcg_at_5']:.3f} | {resource['query_p50_ms']:.1f} / {resource['query_p95_ms']:.1f} | {resource['peak_rss_bytes'] / 2**30:.2f} |")
        vector, mixed = (actual["summary"][method]["all"] for method in ("vector", "hybrid"))
        hybrid.append(f"| {actual['model']['id']} | {vector['hit_at_1']} / {vector['hit_at_3']} / {vector['hit_at_5']} | {mixed['hit_at_1']} / {mixed['hit_at_3']} / {mixed['hit_at_5']} | {vector['ndcg_at_5']:.3f} / {mixed['ndcg_at_5']:.3f} |")
        negative = [row for row in actual["results"] if row["method"] == "vector" and row["case_id"] in ("C17", "C18")]
        distances = [row["ranked"][0]["distance"] for row in negative if row["ranked"]]
        empty_scope = [row for row in actual["results"] if row["case_id"] == "C16"]
        absence.append(f"| {actual['model']['id']} | {len(distances)}/4 devuelven candidatos | {min(distances):.3f} a {max(distances):.3f} | {sum(bool(row['ranked']) for row in empty_scope)}/6 resultados de los tres métodos |")
        for row in actual["results"]:
            if row["method"] == "vector" and not row["expected_no_match"] and not row["metrics"]["hit_at_1"]:
                failures.append(f"| {label} | {row['query_id']} | {row['ranked'][0]['id']} | {', '.join(queries[row['query_id']]['direct_ids'])} |")
    details = []
    for label, actual in result["models"].items():
        config, runtime = actual["model"], actual["actual"]
        details.append(f"- {config['id']}, revisión {config['revision']}, {runtime['dimension']} dimensiones, {runtime['loaded_parameters']:,} parámetros cargados. Máximo documental {runtime['token_counts']['document']['max']} tokens; {runtime['token_counts']['document']['over_native_limit']} documentos superan el límite nativo {runtime['max_seq_length']}.")
    vector_counts = {label: actual["summary"]["vector"]["all"] for label, actual in result["models"].items()}
    interpretation = (f"Qwen recuperó primero el antecedente directo en {vector_counts['qwen']['hit_at_1']}/46 consultas, "
                      f"Gemma en {vector_counts['gemma']['hit_at_1']}/46 y MiniLM en {vector_counts['minilm']['hit_at_1']}/46. "
                      "Qwen obtuvo más primeros resultados directos en esta muestra. Gemma consumió aproximadamente la mitad de RSS y tuvo menor mediana de generación de consulta en esta pasada. "
                      "Ambos recuperaron todos los directos esperados entre los tres primeros. Son candidatos para ampliar la evaluación, sin adopción de producción.")
    report = """# Comparación local de embeddings para mantenimiento de agentes

Mario pidió probar google/embeddinggemma-2 y Qwen/Qwen3-Embedding-0.6B. Se compararon con all-MiniLM-L6-v2 y FTS5 sobre los mismos textos y expectativas congeladas antes de inferencia.

El corpus tiene 33 registros, 26 intenciones y 52 variantes ES/EN. Hay 46 consultas con antecedente directo esperado, 23 por idioma. Las otras seis son controles de ausencia o ámbito. Las cinco consultas ambiguas y V05, control histórico, quedan fuera de puntuación. Los juicios siguen propuestos, sin aprobación independiente. Esta ejecución no es una evaluación de agentes realizando los escenarios.

## Búsqueda vectorial y referencia léxica

""" + "\n".join(table) + """

Un acierto directo requiere grado 2. El grado 1 aporta contexto y no cuenta como acierto directo. nDCG incorpora ambos grados con ganancias 3 y 1. Los porcentajes de idioma usan 23 consultas; las traducciones del mismo caso no son incidentes independientes.

""" + interpretation + """

El tiempo de consulta de la tabla mide sólo generación local del embedding, con una consulta por llamada después de calentamiento. RSS incluye el proceso Python, bibliotecas y pesos cargados; se muestrea cada 50 ms. Son mediciones de una pasada en Apple M1 Pro de 16 GiB, CPU con cuatro threads y float32. Descarga y carga quedan separadas en results.json. No se midió capacidad de producción ni aceleración GPU.

MiniLM y Qwen conservaron exactamente sus rankings y métricas del intento anterior. La mediana de MiniLM cambió de 6,9 a 19,4 ms y la de Qwen de 139,0 a 153,4 ms entre los intentos. El entorno de dependencias también cambió. No se aisló el efecto de ese cambio ni de la actividad del sistema; los tiempos son referencias de estas pasadas, no un benchmark controlado de latencia.

## Búsqueda híbrida

FTS5 usa BM25 sobre todos los tokens Unicode de la consulta, unidos con OR, sin afinar stopwords con las etiquetas. La búsqueda híbrida aplica RRF de pesos iguales, constante 60 y diez candidatos por rama. Es combinación del adaptador de evaluación, no una propiedad de sqlite-vec.

""" + "\n".join(hybrid) + """

La combinación de pesos iguales mejora algunos primeros resultados y pierde algunos directos en top 3/top 5 frente a la búsqueda vectorial de Gemma y Qwen. No se ajustaron pesos después de observar las etiquetas; esta prueba no justifica elegir esa combinación como configuración final.

## Controles sin antecedente

""" + "\n".join(absence) + """

C17 busca exposición de una clave secreta y C18 un fallo de cálculo de IVA. No hay esos incidentes en el corpus. Los vecinos devueltos son candidatos, no confirmaciones. No se fijó un umbral de abstención ni se convierte una distancia en probabilidad calibrada. C16 tiene cero candidatos por proyecto; se informa aparte y no se cuenta como acierto semántico.

## Primeros resultados que no eran directos

""" + "\n".join(failures) + """

Las consultas, IDs esperados y grados completos están en el [corpus congelado de origen](../2026-10-14-embedding-corpus/review.md) y los rankings en [results.json](results.json). Compartir tema o ser un contexto útil no satisface el objetivo directo de la consulta.

## Configuración y procedencia

""" + "\n".join(details) + """

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
"""
    (HERE / "report.md").write_text(report)
    manifest = {"schemaVersion": 1, "status": "executed-exploratory", "protocol_sha256": sha(HERE / "protocol.json"), "results_sha256": sha(HERE / "results.json"),
                "report_sha256": sha(HERE / "report.md"), "publication_sources": {name: sha(HERE / name) for name in ("publish.py", "verify.py")}, "execution_sources": protocol["execution_sources"],
                "private_evidence": "task Git common directory: embedding-model-evidence/" + private.name, "models": protocol["models"], "independent_verification": independent,
                "prior_attempt": result["prior_attempt"],
                "hosted_inference_calls": 0, "active_backend_installed": False, "labels_independently_approved": False}
    (HERE / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"models": {label: value["summary"]["vector"]["all"] for label, value in result["models"].items()}, "fts5": result["fts5"]["summary"]["all"]}))


if __name__ == "__main__":
    main()
