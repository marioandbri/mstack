"""Download only pinned, non-executable model artifacts into task-private storage."""
import argparse
import hashlib
import json
from pathlib import Path
import time

from huggingface_hub import get_token, snapshot_download


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--private", type=Path, required=True)
    parser.add_argument("--models", nargs="+", choices=("minilm", "gemma", "qwen", "gemma300", "e5small"), default=("gemma", "qwen", "minilm"))
    parser.add_argument("--use-local-auth", action="store_true", help="Use an existing authorized HF login; never records the token")
    args = parser.parse_args()
    destination = args.private / "downloads.json"
    results = json.loads(destination.read_text()) if destination.exists() else {}
    token = get_token() if args.use_local_auth else False
    if args.use_local_auth and not token:
        raise RuntimeError("No local Hugging Face login; authenticate before downloading a gated checkpoint")
    for label in args.models:
        info = json.loads((args.private / (label + "-model-info.json")).read_text())
        start = time.perf_counter()
        print(json.dumps({"event": "download-start", "model": info["id"], "revision": info["sha"]}), flush=True)
        path = Path(snapshot_download(info["id"], revision=info["sha"], cache_dir=args.private / "hf-cache",
                                     allow_patterns=["*.json", "*.safetensors", "*.model", "*.txt", "*.jinja", "README.md", "LICENSE*"],
                                     ignore_patterns=["onnx/*", "openvino/*", "tensorrt/*"], token=token, max_workers=4))
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
        temporary = destination.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(results, indent=2) + "\n")
        temporary.replace(destination)
        print(json.dumps({"event": "download-complete", "model": info["id"], "seconds": duration, "bytes": results[label]["artifact_bytes"]}), flush=True)


if __name__ == "__main__":
    main()
