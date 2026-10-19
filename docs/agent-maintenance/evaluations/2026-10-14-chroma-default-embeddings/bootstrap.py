"""Exercise the documented default with an empty, task-owned model cache."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--recover", action="store_true", help="Preserve the failed recorder attempt and reopen its confirmed record")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2 import ONNXMiniLM_L6_V2

    cache = args.output / "model-cache" / "all-MiniLM-L6-v2"
    assert cache.exists() if args.recover else not cache.exists(), "Use a new run directory, or explicitly recover the archived attempt"
    ONNXMiniLM_L6_V2.DOWNLOAD_PATH = cache
    client = chromadb.PersistentClient(path=str(args.output / "bootstrap-db"), settings=Settings(anonymized_telemetry=False))
    try:
        cold_seconds = None
        if args.recover:
            collection = client.get_collection(name="observations")
            assert (args.output / "attempt-01" / "attempt.json").exists()
        else:
            collection = client.create_collection(name="observations")
            assert not cache.exists(), "Collection creation should not yet download the model"
            started = time.monotonic()
            collection.add(ids=["origin-001"], documents=["Approval was requested again after it had been granted."],
                           metadatas=[{"project": "mstack", "harness": "synthetic-python", "source_session": "source-a", "capture_session": "capture-a"}])
            cold_seconds = time.monotonic() - started
        data = collection.get(include=["embeddings", "documents", "metadatas"])
        vector = data["embeddings"][0]
        assert len(vector) == 384
        archive = cache / ONNXMiniLM_L6_V2.ARCHIVE_FILENAME
        assert sha(archive) == ONNXMiniLM_L6_V2._MODEL_SHA256
        query = collection.query(query_texts=["The agent asked for permission twice."], n_results=1)
        assert query["ids"][0] == ["origin-001"]
        result = {
            "status": "pass", "create_collection_omitted_embedding_function": True,
            "supplied_embeddings": False, "cache_absent_before_first_add": True,
            "automatic_download_observed": True, "model": ONNXMiniLM_L6_V2.MODEL_NAME,
            "download_url": ONNXMiniLM_L6_V2.MODEL_DOWNLOAD_URL,
            "archive_sha256": sha(archive), "archive_bytes": archive.stat().st_size,
            "embedding_dimensions": len(vector), "embedding_norm": float((vector @ vector) ** 0.5),
            "collection_configuration": collection.configuration_json,
            "query_texts_ids": query["ids"][0], "cold_add_including_download_seconds": None if cold_seconds is None else round(cold_seconds, 3),
            "artifact_recovered": args.recover,
            "model_files": {str(p.relative_to(cache)): {"bytes": p.stat().st_size, "sha256": sha(p)} for p in sorted(cache.rglob("*")) if p.is_file()},
            "runtime": {"python": platform.python_version(), "chromadb": chromadb.__version__,
                        "onnxruntime": importlib.metadata.version("onnxruntime"), "tokenizers": importlib.metadata.version("tokenizers"),
                        "platform": platform.platform(), "python_executable_sha256": sha(Path(sys.executable).resolve())},
            "source_sha256": sha(Path(__file__)), "protocol_sha256": sha(Path(__file__).with_name("protocol.json")),
            "hosted_model_calls": 0,
        }
        (args.output / "bootstrap.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps({k: result[k] for k in ("status", "automatic_download_observed", "archive_bytes", "embedding_dimensions", "query_texts_ids")}))
    finally:
        client.close()


if __name__ == "__main__":
    main()
