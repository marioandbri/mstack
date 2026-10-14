"""Synthetic SDK owner using Chroma's documented default embedding function."""
from pathlib import Path
import traceback


def decode(data):
    return [dict(data["metadatas"][i], id=identity, text=data["documents"][i],
                 vector=data["embeddings"][i].tolist()) for i, identity in enumerate(data["ids"])]


def add(collection, originals):
    assert all(r["vector"] is None for r in originals), "This trial must not supply embeddings"
    collection.add(ids=[r["id"] for r in originals], documents=[r["text"] for r in originals],
                   metadatas=[{k: v for k, v in r.items() if k not in ("vector", "text")} for r in originals])


def actor(path, operation, payload, barrier, pipe, cache, guarded=False):
    client = None
    try:
        import chromadb
        from chromadb.config import Settings
        from chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2 import ONNXMiniLM_L6_V2

        ONNXMiniLM_L6_V2.DOWNLOAD_PATH = Path(cache)
        client = chromadb.PersistentClient(path=str(path), settings=Settings(anonymized_telemetry=False))
        if operation == "create":
            collection = client.create_collection(name="observations")
            pipe.send({"created": True, "max_batch_size": client.get_max_batch_size(),
                       "configuration": collection.configuration_json})
            return
        collection = client.get_collection(name="observations")
        before = collection.count()
        snapshots = []
        if operation == "decide":
            snapshots = [decode(collection.get(ids=[r["identity"]], include=["metadatas", "documents", "embeddings"]))[0] for r in payload]
        if barrier is not None:
            barrier.wait(timeout=60)
        outcomes = []
        if operation == "read":
            pipe.send({"rows": decode(collection.get(include=["metadatas", "documents", "embeddings"]))})
            return
        if operation == "capture":
            for original in payload:
                if guarded:
                    matches = decode(collection.get(where={"operation_id": original["operation_id"]}, include=["metadatas", "documents", "embeddings"]))
                    if matches:
                        immutable = set(original) - {"vector", "revision", "decision"}
                        same = len(matches) == 1 and all(matches[0][key] == original[key] for key in immutable)
                        outcomes.append({"status": "already-captured" if same else "operation-conflict", "id": original["id"]})
                        continue
                    if collection.get(ids=[original["id"]])["ids"]:
                        outcomes.append({"status": "identity-conflict", "id": original["id"]})
                        continue
                add(collection, [original])
                outcomes.append({"status": "returned", "id": original["id"]})
        elif operation == "decide":
            for item, snapshot in zip(payload, snapshots):
                if snapshot["revision"] != item["expected_revision"]:
                    outcomes.append({"status": "conflict", "observed_revision": snapshot["revision"]})
                    continue
                collection.update(ids=[item["identity"]], metadatas=[{"revision": item["expected_revision"] + 1, "decision": item["decision"]}])
                outcomes.append({"status": "accepted", "base_revision": snapshot["revision"]})
        elif operation == "retrieval":
            queries = []
            for item in payload["queries"]:
                found = collection.query(query_texts=[item["text"]], n_results=3, where={"project": "mstack"})
                ids = found["ids"][0]
                hits = set(ids) & set(item["relevant_ids"])
                queries.append(dict(item, ids=ids, distances=found["distances"][0],
                                    hit_at_1=bool(ids and ids[0] in item["relevant_ids"]),
                                    hit_at_3=bool(hits), recall_at_3=len(hits) / len(item["relevant_ids"])))
            pipe.send({"queries": queries, "query_texts_used": True, "supplied_query_vectors": False})
            return
        elif operation == "embedding_failure":
            original = decode(collection.get(ids=[payload[0]["id"]], include=["metadatas", "documents", "embeddings"]))[0]
            error = None
            try:
                collection.update(ids=[payload[0]["id"]], embeddings=[[1.0, 0.0]])
            except Exception as failure:
                error = str(failure)
            current = decode(collection.get(ids=[payload[0]["id"]], include=["metadatas", "documents", "embeddings"]))[0]
            pipe.send({"error_message": error, "unchanged": original == current})
            return
        elif operation == "capture_embedding_unavailable":
            from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

            def unavailable(self, input):
                raise RuntimeError("Injected local embedding stage unavailable")

            # Fault injection only in this disposable process, after collection
            # creation with real defaults. It never alters the installed SDK.
            DefaultEmbeddingFunction.__call__ = unavailable
            try:
                add(collection, payload)
            except RuntimeError as failure:
                pipe.send({"rejected": True, "message": str(failure), "persisted_rows": collection.count()})
                return
            raise AssertionError("Expected deliberate embedding failure")
        elif operation == "interrupted":
            for original in payload["prefix"]:
                add(collection, [original])
                pipe.send({"event": "acknowledged", "id": original["id"]})
            maximum = client.get_max_batch_size()
            assert len(payload["batch"]) <= maximum
            pipe.send({"event": "batch_started", "batch_rows": len(payload["batch"]), "maximum": maximum,
                       "embedding_computation_precedes_sdk_write": True})
            add(collection, payload["batch"])
            pipe.send({"event": "batch_acknowledged"})
        else:
            raise ValueError(operation)
        pipe.send({"before_rows": before, "results": outcomes})
    except BaseException:
        pipe.send({"error": traceback.format_exc()})
    finally:
        if client is not None:
            client.close()
        pipe.close()
