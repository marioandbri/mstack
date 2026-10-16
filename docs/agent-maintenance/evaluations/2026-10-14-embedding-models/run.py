"""Freeze and execute an exploratory local comparison without changing the corpus."""
import argparse
import hashlib
from importlib import metadata
import json
from pathlib import Path
import platform
import shutil
import sqlite3
import subprocess
import sys
import time

from ranking import RetrievalIndex, measure

HERE = Path(__file__).resolve().parent
PACKAGES = ("numpy", "pillow", "psutil", "sentence-transformers", "sqlite-vec", "torch", "torchvision", "transformers")
SOURCE_FILES = ("run.py", "ranking.py", "download.py", "test_ranking.py", "pyproject.toml", "uv.lock")
MODEL_PROFILES = {
    "minilm": {"id": "sentence-transformers/all-MiniLM-L6-v2", "dimension": 384, "max_seq_length": 256,
               "query_prompt_name": None, "document_prompt_name": None, "config_kwargs": {}},
    "gemma": {"id": "google/embeddinggemma-2", "dimension": 768, "max_seq_length": 8192,
              "query_prompt_name": "query", "document_prompt_name": "document", "config_kwargs": {"vision_config": None, "audio_config": None}},
    "qwen": {"id": "Qwen/Qwen3-Embedding-0.6B", "dimension": 1024, "max_seq_length": 32768,
             "query_prompt_name": "query", "document_prompt_name": "document", "config_kwargs": {}},
    "gemma300": {"id": "google/embeddinggemma-300m", "dimension": 768, "max_seq_length": 2048,
                 "query_prompt": "task: search result | query: ", "document_prompt": "title: none | text: ", "config_kwargs": {}},
    "e5small": {"id": "intfloat/multilingual-e5-small", "dimension": 384, "max_seq_length": 512,
                "query_prompt": "query: ", "document_prompt": "passage: ", "config_kwargs": {}},
}


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def model_config(private, label):
    info = read(private / (label + "-model-info.json"))
    profile = MODEL_PROFILES[label]
    assert info["id"] == profile["id"]
    return {**profile, "revision": info["sha"], "license": info["cardData"]["license"]}


def retrieval_prompts(config, available):
    output = {}
    for role in ("query", "document"):
        if role + "_prompt" in config:
            assert role + "_prompt_name" not in config, "Specify a literal or named prompt, not both"
            output[role] = config[role + "_prompt"]
        else:
            name = config[role + "_prompt_name"]
            output[role] = "" if name is None else available[name]
    return output


def freeze(private, corpus, selected, pending):
    assert len(selected) == len(set(selected)) and not set(selected) & set(pending)
    frozen = private / "corpus"
    frozen.mkdir()
    for name in ("records.json", "queries.json", "labels.json", "manifest.json", "review-feedback.json"):
        shutil.copy2(corpus / name, frozen / name)
    source = private / "execution-sources"
    source.mkdir()
    for name in SOURCE_FILES:
        shutil.copy2(HERE / name, source / name)
    models = {label: model_config(private, label) for label in selected}
    pending_models = {label: {"model": model_config(private, label), "status": "not-executed-access-required",
                             "access_check": read(private / (label + "-access.json"))} for label in pending}
    protocol = {"schemaVersion": 2, "status": "exploratory-authorized", "authorization": "Mario requested adding google/embeddinggemma-300m and intfloat/multilingual-e5-small; repeat existing profiles as references",
                "corpus_commit": "7cba5d9ddb1bdb5b4de7f16464e3bc272850cc03", "corpus_hashes": {item.name: sha(item) for item in frozen.iterdir()},
                "execution_sources": {name: sha(source / name) for name in SOURCE_FILES}, "runtime": {"python": platform.python_version(), "packages": {name: metadata.version(name) for name in PACKAGES},
                    "sqlite": sqlite3.sqlite_version, "platform": platform.platform(), "device": "cpu", "dtype": "float32", "torch_threads": 4},
                "models": models, "pending_models": pending_models, "model_order": list(models), "model_remote_code": False, "hosted_inference": False,
                "embedding_input": "record.text only, with fixed native retrieval prompts; no titles, IDs, grades, source metadata or judge rationale",
                "encoding": {"document_batch_size": 4, "query_batch_size": 1, "l2_normalize": True, "output_dimensions": "full native", "sequence_limits": "model-card/default retrieval limits, explicitly bound; actual token counts and truncation recorded",
                             "scope_filter_first": True, "warmup_inputs": 2, "measured_query_passes": 1},
                "retrieval": {"vector": "sqlite-vec cosine", "lexical": "FTS5 BM25; OR of all unique unicode query tokens, no tuned stopwords", "hybrid": "equal-weight RRF, constant 60, top 10 candidates per branch", "tie_break": "record ID"},
                "scoring": {"labels": "current provisional judgments, not independently approved gold", "direct_grade": 2, "positive_queries": 46, "per_language": 23, "no_match_queries": 6,
                            "metrics": ["hit@1", "hit@3", "hit@5", "direct recall@3/@5", "direct MRR@5", "graded nDCG@5"],
                            "ungraded_cases": "V01/V02/V03/V04/V06 excluded; V05 historical control excluded", "abstention_threshold": None},
                "limits": ["Single project, authored queries and provisional judgments", "Related scenarios and translated queries are not independent incidents",
                           "Ranking candidates for a no-match query does not confirm an incident", "No threshold tuning or calibrated classification", "CPU float32 timings on one M1 Pro 16GB pass; no production capacity claim"]}
    write(HERE / "protocol.json", protocol)
    write(private / "protocol.json", protocol)
    print(json.dumps({"frozen": True, "corpus_hashes": protocol["corpus_hashes"], "models": models}), flush=True)


def check_frozen(private):
    protocol = read(private / "protocol.json")
    for name, expected in protocol["corpus_hashes"].items():
        assert sha(private / "corpus" / name) == expected, name
    for name, expected in protocol["execution_sources"].items():
        assert sha(HERE / name) == expected, name
    assert {name: metadata.version(name) for name in PACKAGES} == protocol["runtime"]["packages"]
    return protocol


def evaluate(index, queries, query_vectors=None):
    output = []
    for query in queries:
        project = query["filters"]["project"]
        methods = {"fts5": index.lexical(query["text"], project, 10)}
        if query_vectors is not None:
            vector = query_vectors.get(query["id"])
            methods["vector"] = index.vector(vector, project, 10) if vector is not None else []
            methods["hybrid"] = index.hybrid(vector, query["text"], project, 10) if vector is not None else []
        for method, ranked in methods.items():
            identities = [row["id"] for row in ranked]
            assert set(identities) <= set(query["candidate_ids"])
            assert len(identities) == len(set(identities))
            output.append({"query_id": query["id"], "case_id": query["case_id"], "language": query["language"], "method": method,
                           "expected_no_match": query["expected_no_match"], "ranked": ranked, "metrics": measure(identities, query["grades"])})
    return output


def worker(private, label):
    import os
    import threading
    import numpy as np
    import psutil
    import torch
    from sentence_transformers import SentenceTransformer

    protocol = check_frozen(private)
    config = protocol["models"][label]
    downloads = read(private / "downloads.json")[label]
    assert downloads["id"] == config["id"] and downloads["revision"] == config["revision"]
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    torch.manual_seed(0)
    process = psutil.Process(os.getpid())
    peak, stop = [process.memory_info().rss], threading.Event()

    def sample():
        while not stop.wait(0.05):
            peak[0] = max(peak[0], process.memory_info().rss)

    monitor = threading.Thread(target=sample, daemon=True)
    monitor.start()
    start = time.perf_counter()
    model = SentenceTransformer(downloads["local_path"], device="cpu", model_kwargs={"dtype": torch.float32}, config_kwargs=config["config_kwargs"],
                                local_files_only=True, trust_remote_code=False)
    load_seconds = time.perf_counter() - start
    model.max_seq_length = config["max_seq_length"]
    assert model.get_embedding_dimension() == config["dimension"]
    prompts = retrieval_prompts(config, model.prompts)
    encode_options = {"normalize_embeddings": True, "convert_to_numpy": True, "show_progress_bar": False}

    def encode(texts, role, batch_size):
        return model.encode(texts, prompt=prompts[role], batch_size=batch_size, **encode_options)

    records = read(private / "corpus/records.json")["records"]
    queries = read(private / "corpus/labels.json")["queries"]
    documents = [row["text"] for row in records]
    encoded_queries = [row for row in queries if row["candidate_ids"]]
    encode(["Local document retrieval warmup."], "document", 1)
    encode(["Find a local document."], "query", 1)
    start = time.perf_counter()
    document_vectors = encode(documents, "document", 4)
    document_seconds = time.perf_counter() - start
    query_vectors, query_ms = {}, {}
    for position, query in enumerate(encoded_queries, 1):
        start = time.perf_counter()
        vector = encode([query["text"]], "query", 1)[0]
        query_ms[query["id"]] = (time.perf_counter() - start) * 1000
        query_vectors[query["id"]] = vector
        if position % 10 == 0:
            print(json.dumps({"event": "encoded-queries", "model": label, "done": position, "total": len(encoded_queries)}), flush=True)
    query_array = np.array(list(query_vectors.values()), dtype=np.float32)
    for values in (document_vectors, query_array):
        assert np.isfinite(values).all()
        assert np.allclose(np.linalg.norm(values, axis=1), 1, atol=1e-5)
    np.savez(private / (label + "-vectors.npz"), documents=document_vectors, queries=query_array, query_ids=np.array(list(query_vectors)))
    index = RetrievalIndex(private / (label + ".sqlite"), config["dimension"])
    index.load([dict(row, project="mstack") for row in records], document_vectors.tolist())
    results = evaluate(index, queries, {key: value.tolist() for key, value in query_vectors.items()})
    index.close()
    token_counts = {}
    for role, texts in (("document", documents), ("query", [row["text"] for row in encoded_queries])):
        counts = [len(model.tokenizer.encode(prompts[role] + text, truncation=False)) for text in texts]
        token_counts[role] = {"max": max(counts), "over_native_limit": sum(value > model.max_seq_length for value in counts)}
    stop.set()
    monitor.join()
    peak[0] = max(peak[0], process.memory_info().rss)
    outcome = {"status": "complete", "model": config, "actual": {"device": str(model.device), "dtype": str(next(model.parameters()).dtype), "dimension": model.get_embedding_dimension(),
               "max_seq_length": model.max_seq_length, "prompts": prompts, "token_counts": token_counts, "loaded_parameters": sum(value.numel() for value in model.parameters())},
               "resources": {"load_seconds_cached": load_seconds, "document_encoding_seconds": document_seconds, "encoded_documents": len(documents), "encoded_queries": len(query_vectors),
                             "scope_skipped_queries": len(queries) - len(query_vectors), "warmup_calls": 2, "query_ms": query_ms, "query_p50_ms": float(np.percentile(list(query_ms.values()), 50)),
                             "query_p95_ms": float(np.percentile(list(query_ms.values()), 95)), "peak_rss_bytes": peak[0]}, "results": results}
    write(private / (label + "-result.json"), outcome)
    print(json.dumps({"event": "model-complete", "model": label, "resources": {key: value for key, value in outcome["resources"].items() if key != "query_ms"}}), flush=True)


def execute(private):
    protocol = check_frozen(private)
    records = read(private / "corpus/records.json")["records"]
    queries = read(private / "corpus/labels.json")["queries"]
    baseline = RetrievalIndex(private / "fts5.sqlite")
    baseline.load([dict(row, project="mstack") for row in records])
    write(private / "fts5-results.json", evaluate(baseline, queries))
    baseline.close()
    outcomes = {}
    for label in protocol["model_order"]:
        command = [sys.executable, str(HERE / "run.py"), "worker", "--private", str(private), "--model", label]
        start = time.perf_counter()
        with (private / (label + "-execution.log")).open("w") as log:
            print(json.dumps({"event": "model-start", "model": label}), flush=True)
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=1800)
        outcomes[label] = {"exit_code": result.returncode, "seconds": time.perf_counter() - start}
        write(private / "execution.json", outcomes)
        print(json.dumps({"event": "model-exit", "model": label, **outcomes[label]}), flush=True)
    assert all(row["exit_code"] == 0 for row in outcomes.values()), "Retained failed model attempts; inspect logs before comparison"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("freeze", "execute", "worker"))
    parser.add_argument("--private", type=Path, required=True)
    parser.add_argument("--corpus", type=Path)
    parser.add_argument("--model", choices=MODEL_PROFILES)
    parser.add_argument("--models", nargs="+", choices=MODEL_PROFILES, default=("minilm", "gemma", "qwen"))
    parser.add_argument("--pending-models", nargs="*", choices=MODEL_PROFILES, default=())
    args = parser.parse_args()
    if args.operation == "freeze":
        freeze(args.private, args.corpus, args.models, args.pending_models)
    elif args.operation == "execute":
        execute(args.private)
    else:
        worker(args.private, args.model)


if __name__ == "__main__":
    main()
