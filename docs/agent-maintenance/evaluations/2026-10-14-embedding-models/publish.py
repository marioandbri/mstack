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
    parser.add_argument("--previous-private", type=Path, help="Retained pass used to compare repeated reference profiles")
    args = parser.parse_args()
    private = args.private
    independent = read(private / "independent-verification.json")
    assert independent["status"] == "PASS"
    protocol = read(private / "protocol.json")
    labels = read(private / "corpus/labels.json")
    baseline = read(private / "fts5-results.json")
    result = {"schemaVersion": 2, "status": "executed-exploratory", "user_approved_labels": False,
              "prior_attempt": read(private / "prior-attempt.json"), "prior_repeat_consistency": read(private / "repeat-consistency.json"),
              "reference_repetition": {}, "pending_models": protocol.get("pending_models", {}),
              "fts5": {"summary": summarize(baseline), "queries": baseline}, "models": {}}
    followup = private / "gemma300-followup-access.json"
    if "gemma300" in result["pending_models"] and followup.exists():
        access = read(followup)
        expected = result["pending_models"]["gemma300"]["model"]
        assert access["id"] == expected["id"] and access["revision"] == expected["revision"]
        assert access["access"] == "not-granted"
        result["pending_models"]["gemma300"]["latest_access_check"] = access
    downloads = read(private / "downloads.json")
    for label in protocol["model_order"]:
        actual = read(private / (label + "-result.json"))
        summaries = {method: summarize([row for row in actual["results"] if row["method"] == method]) for method in ("vector", "hybrid")}
        result["models"][label] = {**actual, "summary": summaries,
            "download": {key: downloads[label][key] for key in ("artifact_bytes", "download_seconds", "artifacts")},
            "sqlite_bytes": (private / (label + ".sqlite")).stat().st_size}
    if args.previous_private:
        previous_protocol = read(args.previous_private / "protocol.json")
        assert previous_protocol["corpus_hashes"] == protocol["corpus_hashes"]
        assert previous_protocol["runtime"] == protocol["runtime"]
        previous_check = read(args.previous_private / "independent-verification.json")
        assert previous_check["status"] == "PASS"
        comparisons = {}
        for label in previous_protocol["model_order"]:
            if label not in result["models"]:
                continue
            earlier = read(args.previous_private / (label + "-result.json"))
            current = result["models"][label]
            assert earlier["model"]["revision"] == current["model"]["revision"]
            def judgments(rows):
                return [(row["query_id"], row["method"], [item["id"] for item in row["ranked"]], row["metrics"]) for row in rows]
            comparisons[label] = {"rankings_and_metrics_unchanged": judgments(earlier["results"]) == judgments(current["results"]),
                                  "previous_p50_ms": earlier["resources"]["query_p50_ms"], "current_p50_ms": current["resources"]["query_p50_ms"],
                                  "previous_result_sha256": sha(args.previous_private / (label + "-result.json"))}
        result["reference_repetition"] = {"previous_run": args.previous_private.name, "previous_protocol_sha256": sha(args.previous_private / "protocol.json"),
                                          "previous_execution_sources": previous_protocol["execution_sources"], "runtime_and_corpus_unchanged": True, "models": comparisons}
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
    for pending in result["pending_models"].values():
        table.append(f"| {pending['model']['id']} | Sin ejecutar | Sin ejecutar | — | — | — |")
    details = []
    for label, actual in result["models"].items():
        config, runtime = actual["model"], actual["actual"]
        details.append(f"- {config['id']}, revisión {config['revision']}, licencia {config['license']}, {runtime['dimension']} dimensiones, {runtime['loaded_parameters']:,} parámetros cargados. Máximo documental {runtime['token_counts']['document']['max']} tokens; {runtime['token_counts']['document']['over_native_limit']} documentos superan el límite nativo {runtime['max_seq_length']}.")
    for pending in result["pending_models"].values():
        config, access = pending["model"], pending["access_check"]
        details.append(f"- {config['id']}, revisión solicitada {config['revision']}, licencia {config['license']}. Sin inferencia: descarga rechazada con HTTP {access['http_status']} ({access['error_class']}); acceso de Hugging Face pendiente. No se le asignan métricas.")
        if "latest_access_check" in pending:
            access = pending["latest_access_check"]
            details.append(f"  Comprobación posterior con token disponible en fish interactivo: HTTP {access['http_status']}. {access['reason']}")
    vector_counts = {label: actual["summary"]["vector"]["all"] for label, actual in result["models"].items()}
    leading = max(vector_counts.values(), key=lambda value: value["hit_at_1"])["hit_at_1"]
    winners = [result["models"][label]["model"]["id"] for label, value in vector_counts.items() if value["hit_at_1"] == leading]
    interpretation = "; ".join(f"{actual['model']['id']}: {actual['summary']['vector']['all']['hit_at_1']}/46 primeros directos" for actual in result["models"].values()) + ". "
    interpretation += f"El mayor número de primeros directos fue {leading}/46, obtenido por {', '.join(winners)}. Las tablas separan calidad de recuperación y recursos. Esta muestra no decide la adopción de un modelo de producción."
    repetition = result["reference_repetition"].get("models", {})
    repeat_text = "\n".join(f"- {result['models'][label]['model']['id']}: rankings y métricas {'idénticos' if values['rankings_and_metrics_unchanged'] else 'distintos'} respecto a {result['reference_repetition']['previous_run']}; mediana {values['previous_p50_ms']:.1f} → {values['current_p50_ms']:.1f} ms." for label, values in repetition.items())
    pending_text = ""
    if result["pending_models"]:
        pending_text = "\nGoogle EmbeddingGemma 300M quedó pendiente: Hugging Face exige aceptar sus condiciones y autorizar el acceso con una cuenta. La descarga devolvió 401 y no había sesión local. Se conserva ese resultado separado de las métricas; habilitar el acceso permitirá ejecutarlo con el mismo corpus. [Condiciones y acceso del modelo](https://huggingface.co/google/embeddinggemma-300m)."
        if "latest_access_check" in result["pending_models"].get("gemma300", {}):
            pending_text += " Una comprobación posterior encontró el token en fish interactivo, pero devolvió 403: la cuenta todavía no está en la lista autorizada del modelo."
    report = """# Comparación local de embeddings para mantenimiento de agentes

Mario pidió ampliar la comparación con google/embeddinggemma-300m e intfloat/multilingual-e5-small. Se añadieron los perfiles disponibles y se repitieron las referencias anteriores, con las mismas revisiones, dependencias, textos y expectativas congeladas antes de inferencia. FTS5 conserva la referencia léxica.

El corpus tiene 33 registros, 26 intenciones y 52 variantes ES/EN. Hay 46 consultas con antecedente directo esperado, 23 por idioma. Las otras seis son controles de ausencia o ámbito. Las cinco consultas ambiguas y V05, control histórico, quedan fuera de puntuación. Los juicios siguen propuestos, sin aprobación independiente. Esta ejecución no es una evaluación de agentes realizando los escenarios.

## Búsqueda vectorial y referencia léxica

""" + "\n".join(table) + """

Un acierto directo requiere grado 2. El grado 1 aporta contexto y no cuenta como acierto directo. nDCG incorpora ambos grados con ganancias 3 y 1. Los porcentajes de idioma usan 23 consultas; las traducciones del mismo caso no son incidentes independientes.

""" + interpretation + "\n" + pending_text + """

El tiempo de consulta de la tabla mide sólo generación local del embedding, con una consulta por llamada después de calentamiento. RSS incluye el proceso Python, bibliotecas y pesos cargados; se muestrea cada 50 ms. Son mediciones de una pasada en Apple M1 Pro de 16 GiB, CPU con cuatro threads y float32. Descarga y carga quedan separadas en results.json. No se midió capacidad de producción ni aceleración GPU.

La repetición se contrasta con la pasada anterior conservada. Los hashes del corpus y el entorno de ejecución son idénticos; los scripts conservan su procedencia por pasada. No se aisló la actividad del sistema, por lo que los tiempos son referencias de estas pasadas, no un benchmark controlado de latencia.

""" + repeat_text + """

## Búsqueda híbrida

FTS5 usa BM25 sobre todos los tokens Unicode de la consulta, unidos con OR, sin afinar stopwords con las etiquetas. La búsqueda híbrida aplica RRF de pesos iguales, constante 60 y diez candidatos por rama. Es combinación del adaptador de evaluación, no una propiedad de sqlite-vec.

""" + "\n".join(hybrid) + """

La combinación puede mejorar primeros resultados y perder directos en top 3/top 5. La tabla registra el efecto en cada perfil. No se ajustaron pesos después de observar las etiquetas; esta prueba no justifica elegir esa combinación como configuración final.

## Controles sin antecedente

""" + "\n".join(absence) + """

C17 busca exposición de una clave secreta y C18 un fallo de cálculo de IVA. No hay esos incidentes en el corpus. Los vecinos devueltos son candidatos, no confirmaciones. No se fijó un umbral de abstención ni se convierte una distancia en probabilidad calibrada. C16 tiene cero candidatos por proyecto; se informa aparte y no se cuenta como acierto semántico.

## Primeros resultados que no eran directos

""" + "\n".join(failures) + """

Las consultas, IDs esperados y grados completos están en el [corpus congelado de origen](../2026-10-14-embedding-corpus/review.md) y los rankings en [results.json](results.json). Compartir tema o ser un contexto útil no satisface el objetivo directo de la consulta.

## Configuración y procedencia

""" + "\n".join(details) + """

EmbeddingGemma 2 carga sólo texto, con vision_config y audio_config desactivados, y usa los prompts query/document de su configuración. Qwen usa su instrucción query y documento sin prefijo. MiniLM usa texto sin prefijos. E5 usa query: para consultas y passage: para documentos, también en español. El perfil solicitado de Gemma 300M fija task: search result | query: y title: none | text:. Se conserva el texto completo de cada registro como entrada; los nombres, grados, razones del juez y fuentes no se añaden. Los prefijos son constantes del modelo. Todos los vectores ejecutados son float32, finitos y normalizados; cada perfil usa sus dimensiones completas.

Las configuraciones se apoyan en las model cards de [Google 2](https://huggingface.co/google/embeddinggemma-2), [Google 300M](https://huggingface.co/google/embeddinggemma-300m), [Qwen](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B), [MiniLM](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) y [E5](https://huggingface.co/intfloat/multilingual-e5-small). Las revisiones completas y los hashes de archivos fijan lo ejecutado. Los tres checkpoints iniciales declaran Apache 2.0; E5 declara MIT y Gemma 300M declara la licencia Gemma. El entorno de evaluación usa versiones exactas en pyproject.toml y resolución completa en uv.lock; no instala un backend activo.

El [protocolo](protocol.json) conserva los hashes del corpus y de los scripts anteriores a ejecución, versiones, prefijos, ámbito y rúbrica. Los modelos, vectores, bases SQLite, logs y copias de fuentes se conservan fuera de Git en embedding-model-evidence del directorio privado de esta tarea. Hub sólo se usó para descarga; la inferencia se ejecutó offline y no envió textos a un proveedor.

El primer intento histórico completó MiniLM y Qwen, pero Gemma 2 no pudo cargar el procesador por ausencia de Pillow, antes de generar embeddings. El preflight posterior identificó también Torchvision. Se conservan como fallos de infraestructura. Tras añadir Pillow 12.3.0 y Torchvision 0.29.1 se completó run-02. El tokenizer de Gemma 2 exponía un límite centinela indeterminado; se fijó el límite documentado de 8.192 tokens. La tabla actual usa la nueva pasada completa, no el intento fallido. Las referencias reutilizan los mismos pesos descargados, sin segunda descarga; sus tiempos de descarga corresponden a la adquisición inicial. E5 se descargó en esta ampliación.

## Verificación y límites

La comprobación independiente reabre las bases, repite las consultas vectoriales y contrasta distancias y rankings con coseno de NumPy. Verifica integridad, ámbito, vectores finitos, normalización, fuente y pesos por hash, y exclusión de consultas sin grados. La [verificación](verification.json) conserva resultados reales y los checks del repositorio.

El corpus es pequeño, de un proyecto, con consultas redactadas y escenarios agrupados. No demuestra calidad cotidiana, fiabilidad de captura, clasificación automática, deduplicación ni permisos de integración. Elegir un modelo de producción requiere más episodios independientes y una calibración separada de abstención; no se ajustan umbrales sobre este mismo conjunto.

## Reproducción

Con uv 0.10.11 y Python 3.13.2, uv sync --locked prepara el entorno. download.py recibe un directorio privado con metadata pública de las revisiones fijadas y --models selecciona las descargas; no ejecuta código remoto. --use-local-auth permite usar una sesión existente que tenga acceso al modelo restringido, sin guardar el token en evidencia. run.py freeze --models selecciona los perfiles disponibles y --pending-models conserva accesos pendientes; congela fuentes y protocolo antes de ejecutar. run.py execute serializa los perfiles con los mismos ajustes de proceso.

```fish
env PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 uv run --locked python run.py execute --private /ruta/privada/congelada
env PYTHONDONTWRITEBYTECODE=1 uv run --locked python verify.py --private /ruta/privada/congelada
env PYTHONDONTWRITEBYTECODE=1 uv run --locked python -m unittest -v test_ranking.py
```

Una nueva ejecución usa un directorio nuevo para conservar intentos previos. publish.py --private /ruta/privada/congelada --previous-private /ruta/privada/anterior genera este informe y results.json desde la evidencia verificada y contrasta la repetición de las referencias; los generados se actualizan con ese script.
"""
    (HERE / "report.md").write_text(report)
    manifest = {"schemaVersion": 2, "status": "executed-exploratory", "protocol_sha256": sha(HERE / "protocol.json"), "results_sha256": sha(HERE / "results.json"),
                "report_sha256": sha(HERE / "report.md"), "publication_sources": {name: sha(HERE / name) for name in ("publish.py", "verify.py")}, "execution_sources": protocol["execution_sources"],
                "private_evidence": "task Git common directory: embedding-model-evidence/" + private.name, "models": protocol["models"], "pending_models": result["pending_models"], "independent_verification": independent,
                "reference_repetition": result["reference_repetition"],
                "access_followup_sha256": sha(followup) if "latest_access_check" in result["pending_models"].get("gemma300", {}) else None,
                "prior_attempt": result["prior_attempt"],
                "hosted_inference_calls": 0, "active_backend_installed": False, "labels_independently_approved": False}
    (HERE / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"models": {label: value["summary"]["vector"]["all"] for label, value in result["models"].items()}, "fts5": result["fts5"]["summary"]["all"]}))


if __name__ == "__main__":
    main()
