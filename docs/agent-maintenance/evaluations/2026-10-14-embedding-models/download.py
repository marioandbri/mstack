"""Download only pinned, non-executable model artifacts into task-private storage."""
import argparse
import hashlib
import json
from pathlib import Path
import time

from huggingface_hub import snapshot_download


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--private", type=Path, required=True)
    args = parser.parse_args()
    results = {}
    for label in ("gemma", "qwen", "minilm"):
        info = json.loads((args.private / (label + "-model-info.json")).read_text())
        start = time.perf_counter()
        print(json.dumps({"event": "download-start", "model": info["id"], "revision": info["sha"]}), flush=True)
        path = Path(snapshot_download(info["id"], revision=info["sha"], cache_dir=args.private / "hf-cache",
                                     allow_patterns=["*.json", "*.safetensors", "*.model", "*.txt", "*.jinja", "README.md", "LICENSE*"],
                                     token=False, max_workers=4))
        duration = time.perf_counter() - start
        artifacts = []
        upstream = {item["rfilename"]: item for item in info["siblings"]}
        for item in sorted(path.rglob("*")):
            if not item.is_file():
                continue
            name = item.relative_to(path).as_posix()
            with item.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            expected = upstream[name].get("lfs", {}).get("sha256")
            assert expected is None or digest == expected, name
            artifacts.append({"path": name, "bytes": item.stat().st_size, "sha256": digest, "upstream_lfs_sha256": expected})
        results[label] = {"id": info["id"], "revision": info["sha"], "local_path": str(path), "license": info["cardData"]["license"],
                          "download_seconds": duration, "artifact_bytes": sum(item["bytes"] for item in artifacts), "artifacts": artifacts}
        (args.private / "downloads.json").write_text(json.dumps(results, indent=2) + "\n")
        print(json.dumps({"event": "download-complete", "model": info["id"], "seconds": duration, "bytes": results[label]["artifact_bytes"]}), flush=True)


if __name__ == "__main__":
    main()
