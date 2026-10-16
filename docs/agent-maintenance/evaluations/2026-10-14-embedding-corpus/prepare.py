"""Generate review artifacts from authored examples and evidence already on disk."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import shutil

HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[3]
SOURCE_FILES = {
    "S01": ("worktree", "docs/agent-maintenance/inbox/OBS-AGENTS-DIRECT-LEARNING-001.json"),
    "S02": ("canonical", "docs/agent-maintenance/inbox/OBS-REFLECT-PERSISTENCE-001.json"),
    "S03": ("canonical", "docs/agent-maintenance/evaluations/2026-10-08-reflect-support/report.md"),
    "S04": ("canonical", "docs/agent-maintenance/inbox/OBS-REFLECT-EVALUATION-DOCS-001.json"),
    "S05": ("worktree", "docs/agent-maintenance/inbox/OBS-MAINTENANCE-SCOPE-001.json"),
    "S06": ("worktree", "docs/agent-maintenance/inbox/OBS-CHROMA-ARTIFACT-RECOVERY-001.json"),
    "S07": ("worktree", "docs/agent-maintenance/evaluations/2026-10-13-am011/report.md"),
    "S08": ("canonical", "docs/agent-maintenance/evaluations/2026-10-08-reflect-persistence/report.md"),
    "S09": ("worktree", "docs/agent-maintenance/changes/AM-010-global-agents.review.json"),
    "S10": ("worktree", "docs/agent-maintenance/changes/AM-011-editorial-result.md"),
    "S11": ("worktree", "docs/agent-maintenance/changes/AM-014-inventory-audit.md"),
    "S12": ("worktree", "docs/agent-maintenance/changes/AM-013-installation.md"),
    "S13": ("worktree", "docs/agent-maintenance/evaluations/2026-10-13-lancedb/report.md"),
    "S14": ("worktree", "docs/agent-maintenance/evaluations/2026-10-14-sqlite-vector/report.md"),
    "S15": ("worktree", "docs/agent-maintenance/evaluations/2026-10-14-chroma-default-embeddings/report.md"),
    "S16": ("worktree", "docs/agent-maintenance/evaluations/2026-10-14-chroma-default-embeddings/verification.json"),
    "S17": ("worktree", "skills/conventions-aware-engineering/SKILL.md"),
    "S18": ("worktree", "skills/grill-with-docs/SKILL.md"),
    "S19": ("worktree", "skills/repository-workflow/SKILL.md"),
    "S20": ("worktree", "docs/agent-maintenance/evaluations/2026-10-14-embedding-corpus/review-feedback.json"),
}


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    path = HERE / name
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def pointer(data, path):
    for part in path.strip("/").split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        data = data[int(part)] if isinstance(data, list) else data[part]
    return data


def collect_sources(canonical_root, snapshot_dir):
    sources, paths = {}, {}
    for identity, (origin, relative) in SOURCE_FILES.items():
        root = REPOSITORY if origin == "worktree" else canonical_root
        path = root / relative
        assert path.is_file(), path
        sources[identity] = {"origin": origin, "path": relative, "sha256": sha(path)}
        paths[identity] = path
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot = snapshot_dir / (identity + path.suffix)
        if snapshot.exists():
            assert sha(snapshot) == sha(path), f"Source drift for {identity}; use a new private snapshot directory"
        else:
            shutil.copy2(path, snapshot)
    return sources, paths


def evidence(records, paths):
    excerpts = []
    for row in records:
        references = [row] + row.get("additional_sources", [])
        for reference in references:
            path = paths[reference["source"]]
            if "pointer" in reference:
                excerpt = pointer(read(path), reference["pointer"])
                location = {"json_pointer": reference["pointer"]}
            else:
                excerpt = reference["quote"]
                assert excerpt in path.read_text(), (row["id"], reference["source"], excerpt)
                location = {"exact_quote": excerpt}
            excerpts.append({"record_id": row["id"], "source_id": reference["source"], "location": location, "excerpt": excerpt})
    return excerpts


def build_labels(records, queries):
    record_ids = {row["id"] for row in records}
    assert len(record_ids) == len(records)
    output = []
    for case in queries["cases"]:
        direct, context, negatives = (set(case[key]) for key in ("direct", "context", "hard_negatives"))
        assert not (direct & context or direct & negatives or context & negatives), case["id"]
        assert direct | context | negatives <= record_ids
        no_match = case.get("expected_no_match", False)
        assert bool(direct) != no_match
        filters = case.get("filters", queries["default_filters"])
        eligible = [row["id"] for row in records if filters["project"] == "mstack"]
        assert direct | context | negatives <= set(eligible)
        workflow = case.get("workflow_expectation")
        if workflow:
            assert workflow["label"] in queries["workflow_label_definitions"]
            assert workflow["execution_status"] == "not-executed"
            assert all(row["kind"] == "prepared-scenario" for row in records if row["id"] in direct)
        for language in ("es", "en"):
            output.append({
                "id": case["id"] + "-" + language, "case_id": case["id"], "language": language,
                "text": case[language], "intent": case["intent"], "filters": filters,
                "judgment_status": "proposed", "user_approved": False,
                "direct_ids": case["direct"], "context_ids": case["context"], "hard_negative_ids": case["hard_negatives"],
                "candidate_ids": eligible,
                "grades": {identity: 2 if identity in direct else 1 if identity in context else 0 for identity in eligible},
                "expected_no_match": no_match, "absence_reason": case.get("absence_reason"), "rationale": case["rationale"],
                **({"workflow_expectation": workflow} if workflow else {}),
            })
    pending, excluded = [], []
    for case in queries["review_cases"]:
        assert set(case["proposal"]["direct"] + case["proposal"]["context"]) <= record_ids
        target = excluded if case.get("role") == "historical-coverage-control" else pending
        target.append({"id": case["id"] + "-es", "case_id": case["id"], "language": "es", "text": case["query"],
                        "filters": queries["default_filters"], "judgment_status": "out-of-scope" if target is excluded else "needs-decision", "user_approved": False,
                        "grades": None, "include_in_scoring": False, "proposed_ids": case["proposal"],
                        "question": case["question"], "recommendation": case["recommendation"], "ambiguity": case["ambiguity"],
                        "role": case.get("role", "retrieval-ambiguity"), "decision_status": case.get("decision_status", "needs-review"),
                        "review_feedback": case.get("review_feedback")})
    identities = [row["id"] for row in output + pending + excluded]
    assert len(identities) == len(set(identities)) == 2 * len(queries["cases"]) + len(queries["review_cases"])
    return {"schemaVersion": 1, "status": "proposed", "user_approved": False, "frozen_for_execution": False,
            "grading": {"2": "Directly answers the explicit retrieval intent", "1": "Useful context, without satisfying the direct target", "0": "Does not answer this query in this bounded corpus"},
            "workflow_label_definitions": queries["workflow_label_definitions"],
            "direct_hit_requires_grade": 2, "queries": output, "held_out_for_review": pending, "excluded_from_comparison": excluded}


def render_review(records, queries):
    kinds = {"incident": "Incidente", "audit-finding": "Hallazgo documental", "evaluation-result": "Resultado de evaluación",
             "review-decision": "Decisión de Mario", "review-result": "Revisión editorial", "installation-result": "Instalación histórica", "storage-probe": "Prueba sintética de base", "prepared-scenario": "Escenario sin ejecutar"}
    catalog = ["| ID | Antecedente | Tipo | Fuente |", "|---|---|---|---|"]
    for row in records:
        catalog.append(f"| {row['id']} | {row['title']} | {kinds[row['kind']]} | {row['source']} |")
    cases = ["| Caso | Consulta en español | Directo, grado 2 | Contexto, grado 1 | Negativos cercanos, grado 0 |", "|---|---|---|---|---|"]
    for case in queries["cases"]:
        fields = [", ".join(case[key]) or "Ninguno" for key in ("direct", "context", "hard_negatives")]
        cases.append(f"| {case['id']} | {case['es']} | {fields[0]} | {fields[1]} | {fields[2]} |")
    review = ["| Caso | Consulta ambigua | Propuesta para revisar | Información o decisión pendiente |", "|---|---|---|---|"]
    historical = []
    for case in queries["review_cases"]:
        if case.get("role") == "historical-coverage-control":
            historical.append(f"{case['id']} es un control histórico de cobertura, excluido de las ambigüedades activas y de puntuación.")
        else:
            review.append(f"| {case['id']} | {case['query']} | {case['recommendation']} | {case['question']} |")
    workflow = ["| Caso | Etiqueta de comportamiento propuesta | Criterio esperado si se ejecuta |", "|---|---|---|"]
    for case in queries["cases"]:
        if expectation := case.get("workflow_expectation"):
            label = expectation["label"]
            workflow.append(f"| {case['id']} | {label} | {queries['workflow_label_definitions'][label]} |")
    result = f"""# Ejemplos y etiquetas para comparar recuperación en Reflect

El conjunto reúne {len(records)} registros trazables a {len(SOURCE_FILES)} fuentes del mantenimiento de mstack. Hay {len(queries['cases'])} intenciones de consulta con variantes en español e inglés, {2 * len(queries['cases'])} consultas propuestas, cinco casos ambiguos separados y un control histórico fuera de la comparación. Los datos y etiquetas son un borrador para revisión. No se ejecutaron modelos ni se congeló un benchmark.

Los 30 antecedentes históricos mezclan cinco registros de incidente, nueve decisiones de Mario, cuatro hallazgos documentales, siete resultados de evaluación, una revisión editorial, un cierre histórico de instalación y tres pruebas sintéticas de almacenamiento. Tres de los cinco incidentes proceden de evaluaciones con fixtures; los otros dos son una corrección de esta conversación y un fallo del recolector local. Se añaden tres escenarios pedidos por Mario sobre convenciones, entrevista y worktree, todavía sin ejecutar. Sus fuentes son procedimientos y criterios de esta revisión, sin trazas de incidentes. No son 33 fricciones independientes de uso cotidiano.

## Cómo leer las etiquetas

- Grado 2. El antecedente responde directamente a la intención explícita de la consulta.
- Grado 1. Aporta contexto útil, pero no satisface por sí solo lo que se busca.
- Grado 0. No responde a esa consulta en este corpus, aunque comparta palabras o tema.
- Sin antecedente. La consulta no tiene un resultado pertinente en el conjunto preparado. No afirma ausencia en otros proyectos o sesiones.
- Pendiente. La consulta admite varias interpretaciones. Sus etiquetas propuestas no se usarán para puntuar hasta resolverla.

Las etiquetas viven fuera del texto que recibirá el modelo. Se codifica sólo text de cada antecedente; IDs, relevancia, fuentes, tipo y metadata no se añaden a la entrada del embedding. Un vecino cercano no pasa a ser un duplicado ni una nueva ocurrencia por ese resultado.

Los [antecedentes](records.json), [consultas y razones](queries.json) y [etiquetas generadas](labels.json) conservan sus IDs. Las [fuentes y extractos](sources.json) fijan los archivos revisados por hash y cada cita o JSON Pointer. Los originales sin session_id disponible mantienen ese valor desconocido. No se consultaron las sesiones completas ni credenciales.

## Catálogo de antecedentes

""" + "\n".join(catalog) + """

Las fuentes S02, S03, S04 y S08 sólo están en el checkout canónico de investigación y se leyeron sin modificarlas. Las otras proceden del worktree propio. Se preservaron copias congeladas privadas de las 20 fuentes; el paquete público contiene los extractos mínimos para comprobar las etiquetas sin copiar directorios históricos completos. S20 conserva los [comentarios de Mario en esta revisión](review-feedback.json), sin convertirlos en instrucciones activas ni en aprobación de todas las etiquetas.

## Consultas con etiquetas propuestas

Cada fila tiene una variante inglesa equivalente en queries.json. Los antecedentes están redactados en español con sus nombres técnicos originales; las consultas inglesas prueban recuperación entre idiomas sobre esos mismos textos. Son ejemplos redactados para la prueba a partir de evidencia existente; no se presentan como nuevas preguntas naturales de Mario. Las traducciones del mismo caso tampoco son muestras independientes del problema.

""" + "\n".join(cases) + """

Para la intención explícita, los demás antecedentes elegibles se proponen con grado 0. Las razones y negativos cercanos están en queries.json. Son juicios del preparador, pendientes de revisión, no etiquetas aprobadas por el usuario ni un dictamen independiente.

C16 tiene cero candidatos por filtro de proyecto. Se informará aparte de C17 y C18, que mantienen candidatos pero no tienen un incidente relevante. Estos últimos permiten medir asociaciones incorrectas o abstención; un KNN que siempre devuelve vecinos necesita distinguir candidato de antecedente confirmado.

## Omisiones de procedimiento y controles

R31, R32 y R33 contienen los escenarios solicitados. C19 a C26 preparan omisiones y controles cercanos. Las etiquetas siguientes describen el comportamiento esperado en una futura ejecución. Se conservan fuera del texto del embedding y no sustituyen los grados de relevancia de recuperación.

""" + "\n".join(workflow) + """

El control C20 conserva una falta de selección de la skill, aunque demuestra consulta efectiva de convenciones. C26 omite la selección porque la tarea no encaja con su trigger. C22 evita repetir una entrevista con requisitos cerrados y documentación suficiente. C25 permite preguntar por una brecha material nueva después de investigar, aun con spec aprobada e implementación solicitada. C24 permite reutilizar el worktree propio preparado. Una tarea de sólo lectura tampoco exige crear un worktree para cambios.

Para registrar una omisión real hay que comprobar que la tarea encaja con el trigger, el procedimiento estaba disponible y se omitió en la traza del trabajo. Una traza incompleta deja la clasificación indeterminada. Las fuentes S17, S18 y S19 prueban procedimientos y S20 conserva criterios de revisión; no demuestran que ocurrieran estas omisiones. La recuperación semántica puede encontrar el escenario, pero no prueba por sí sola un fallo ni decide corregir instrucciones.

## Casos que necesitan revisión

""" + "\n".join(review) + """

Los cinco casos conservan grades=null e include_in_scoring=false en labels.json. Los criterios de V02 y V04 se aclararon con Mario, pero sus consultas originales siguen sin describir el contexto suficiente para una etiqueta única. C19/C26 y C22/C25 preparan los contrastes explícitos. V03 aún requiere distinguir fases.

""" + "\n".join(historical) + """ V05 también conserva grades=null e include_in_scoring=false, en excluded_from_comparison. No se ha aportado evidencia nueva de captura completa.

V06 pregunta por un incidente de consumo excesivo de GPU. R29 sólo describe una prueba de MiniLM; R21 describe una edición de instrucciones. Ninguno confirma ese incidente. La respuesta propuesta indica ausencia en este corpus; falta revisar si se muestra alguno como contexto separado o se omite.

## Comprobaciones antes de comparar modelos

Primero se revisan las etiquetas y se conserva una versión congelada. La ejecución posterior usará el mismo texto, ámbitos y expectativas para cada modelo, con FTS5 como referencia y comparación híbrida separada. El modelo de producción y los dos candidatos adicionales no se eligen mediante este borrador.

La medición propuesta distingue recuperación de antecedentes directos en top 3 y top 5, contexto útil, falsas asociaciones en consultas sin antecedente y fugas de ámbito. Se separan idiomas, tipos de fuente, episodios y controles sin candidatos. Latencia y memoria se medirán después, en un protocolo local común. No se transforma el total de traducciones, controles o decisiones de una misma sesión en una tasa de fiabilidad de incidentes.

V05 impide convertir una puntuación histórica en prueba de captura completa. R02 y R08 conservan fallo y seguimiento; R01 y R10 conservan perfiles e intentos distintos; R06 y R28 distinguen publicación de evidencia de persistencia anterior al modelo. R25 registra el cierre del 13 de octubre, sin presentarlo como identificación de la instalación activa actual.

## Reproducción y verificación

records.json y queries.json son entradas curadas. prepare.py genera fuentes, extractos, etiquetas, este documento y manifest.json. Los generados se actualizan mediante ese script, sin editarlos manualmente. Las fuentes congeladas completas permanecen fuera de Git, en mstack-tasks/maintenance-laya/embedding-corpus-evidence/draft-02/sources bajo el Git common directory canónico. Se conserva la versión anterior en draft-01.

Con uv 0.10.11 y el entorno Python 3.13.2 ya bloqueado, desde esta carpeta:

```fish
env PYTHONDONTWRITEBYTECODE=1 uv run --locked --project ../2026-10-14-chroma python prepare.py --canonical-root /ruta/repositorio/canonico --private-snapshots /ruta/privada/fuentes
env PYTHONDONTWRITEBYTECODE=1 uv run --locked --project ../2026-10-14-chroma python verify.py --private-snapshots /ruta/privada/fuentes
```

La preparación usa sólo biblioteca estándar y archivos locales. Si una fuente congelada difiere de la fuente actual, se usa otro directorio de snapshots y se revisa la diferencia. Los hashes prueban identidad de fuentes y estructura; no pueden decidir por sí solos la pertinencia semántica de cada etiqueta. La [verificación](verification.json) documenta los checks realizados y ese límite.
"""
    (HERE / "review.md").write_text(result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--private-snapshots", type=Path, required=True)
    args = parser.parse_args()
    assert not args.private_snapshots.resolve().is_relative_to(REPOSITORY)
    records, queries = read(HERE / "records.json")["records"], read(HERE / "queries.json")
    sources, paths = collect_sources(args.canonical_root, args.private_snapshots)
    excerpts = evidence(records, paths)
    labels = build_labels(records, queries)
    write("sources.json", {"schemaVersion": 1, "sources": sources, "evidence": excerpts,
                           "roots": {"worktree": "owned task checkout", "canonical": "read-only historical maintenance sources outside this checkout"},
                           "limits": "Full source hashes bind reviewed files, not inaccessible underlying sessions; source_session stays unknown when not exposed"})
    write("labels.json", labels)
    render_review(records, queries)
    write("manifest.json", {"schemaVersion": 1, "status": "prepared-not-executed", "source_commit": "38f88a622100f2bd7302642de9602aa41646a315",
                            "authorization": "Mario requested examples, labels and cases to review, then conventions/interview/worktree omissions; this does not authorize new model executions",
                            "runtime": {"python": platform.python_version(), "external_dependencies": 0},
                            "inputs": {name: sha(HERE / name) for name in ("records.json", "queries.json", "review-feedback.json", "prepare.py", "verify.py")},
                            "outputs": {name: sha(HERE / name) for name in ("sources.json", "labels.json", "review.md")},
                            "counts": {"records": len(records), "source_files": len(sources), "record_kinds": dict(Counter(row["kind"] for row in records)),
                                       "unexecuted_scenarios": sum(row["kind"] == "prepared-scenario" for row in records),
                                       "source_episodes": len({row["episode"] for row in records}),
                                       "historical_source_episodes": len({row["episode"] for row in records if row["kind"] != "prepared-scenario"}),
                                       "base_query_intents": len(queries["cases"]),
                                       "proposed_queries": len(labels["queries"]), "languages": dict(Counter(row["language"] for row in labels["queries"])),
                                       "no_match_queries": sum(row["expected_no_match"] for row in labels["queries"]), "held_out_queries": len(labels["held_out_for_review"]),
                                       "excluded_historical_queries": len(labels["excluded_from_comparison"])},
                            "new_embedding_calls": 0, "new_hosted_model_calls": 0, "user_approved_labels": False,
                            "limits": ["Only mstack maintenance sources; source diversity and incident count are limited", "Authored queries and translations, not natural query logs",
                                       "Provisional relevance judgments by the preparing agent, not an independent judge", "Five unresolved cases and one excluded historical control have no scoring grades",
                                       "Three user-requested workflow scenarios use procedures and review feedback; no execution trace or observed incident",
                                       "Related records, follow-ups and language variants are not independent incident recurrences", "No model selection, benchmark winner or production adoption"]})
    print(json.dumps({"records": len(records), "proposed_queries": len(labels["queries"]), "held_out": len(labels["held_out_for_review"]), "excluded_historical": len(labels["excluded_from_comparison"]), "sources": len(sources), "embedding_calls": 0}))


if __name__ == "__main__":
    main()
