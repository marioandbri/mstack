"""One synthetic SDK owner. Never starts a Chroma server or embedding model."""
import traceback


def decode(data):
    rows = []
    for index, identity in enumerate(data["ids"]):
        row = dict(data["metadatas"][index])
        row["id"] = identity
        row["text"] = data["documents"][index]
        vector = data["embeddings"][index]
        row["vector"] = None if vector is None else vector.tolist()
        rows.append(row)
    return rows


def add(collection, originals):
    kwargs = {
        "ids": [r["id"] for r in originals],
        "documents": [r["text"] for r in originals],
        "metadatas": [{k: v for k, v in r.items() if k not in ("vector", "text")} for r in originals],
    }
    if all(r["vector"] is not None for r in originals):
        kwargs["embeddings"] = [r["vector"] for r in originals]
    collection.add(**kwargs)


def actor(path, operation, payload, barrier, pipe, guarded=False):
    client = None
    try:
        import chromadb
        from chromadb.config import Settings

        client = chromadb.PersistentClient(path=str(path), settings=Settings(anonymized_telemetry=False))
        if operation == "create":
            collection = client.create_collection("observations", embedding_function=None, configuration={"hnsw": {"space": "l2"}})
            pipe.send({"created": True, "max_batch_size": client.get_max_batch_size()})
            return
        collection = client.get_collection("observations", embedding_function=None)
        before = collection.count()
        snapshots = []
        if operation == "decide":
            snapshots = [decode(collection.get(ids=[r["identity"]], include=["metadatas", "documents", "embeddings"]))[0] for r in payload]
        if barrier is not None:
            barrier.wait(timeout=30)
        outcomes = []
        if operation == "read":
            pipe.send({"rows": decode(collection.get(include=["metadatas", "documents", "embeddings"]))})
            return
        if operation in ("capture", "missing_embedding"):
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
                try:
                    add(collection, [original])
                    outcomes.append({"status": "returned", "id": original["id"]})
                except ValueError as error:
                    if operation != "missing_embedding":
                        raise
                    outcomes.append({"status": "rejected", "error": str(error), "exception": type(error).__name__})
        elif operation == "decide":
            for item, snapshot in zip(payload, snapshots):
                if snapshot["revision"] != item["expected_revision"]:
                    outcomes.append({"status": "conflict", "observed_revision": snapshot["revision"]})
                    continue
                collection.update(ids=[item["identity"]], metadatas=[{"revision": item["expected_revision"] + 1, "decision": item["decision"]}])
                outcomes.append({"status": "accepted", "base_revision": snapshot["revision"]})
        elif operation == "retrieval":
            vector = collection.query(query_embeddings=[[1.0, 0.0, 0.0]], n_results=1, where={"project": "mstack"})
            text = collection.get(where={"project": "mstack"}, where_document={"$contains": "approval"})
            combined = collection.query(query_embeddings=[[1.0, 0.0, 0.0]], n_results=3, where={"project": "mstack"}, where_document={"$contains": "approval"})
            pipe.send({"vector_ids": vector["ids"][0], "substring_ids": text["ids"], "combined_filter_ids": combined["ids"][0]})
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
        elif operation == "interrupted":
            import time
            for original in payload["prefix"]:
                add(collection, [original])
                pipe.send({"event": "acknowledged", "id": original["id"]})
            batch = payload["batch"]
            maximum = client.get_max_batch_size()
            if len(batch) > maximum:
                pipe.send({"error": f"Requested batch {len(batch)} exceeds SDK maximum {maximum}"})
                return
            pipe.send({"event": "batch_started", "batch_rows": len(batch), "maximum": maximum})
            add(collection, batch)
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
