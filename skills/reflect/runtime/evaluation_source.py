"""Freeze managed source using the existing installer, not the working tree."""
import json
from pathlib import Path
import subprocess
import sys

from evaluation import EvaluationError
from records import digest


def git_profile(repository, commit, environment, *, identity, model, reasoning, seconds, tool_repository=None):
    repository = Path(repository).resolve(strict=True)
    tools = Path(tool_repository).resolve(strict=True) if tool_repository else repository
    head = subprocess.check_output(["git", "-C", str(tools), "rev-parse", "HEAD"], stderr=subprocess.PIPE).decode().strip()
    tooling = {}
    for relative in ("install/mstack_source.py", "install/mstack_config.py", "install/mstack_fs.py"):
        committed = subprocess.check_output(["git", "-C", str(tools), "show", head + ":" + relative], stderr=subprocess.PIPE)
        if (tools / relative).read_bytes() != committed:
            raise EvaluationError("uncommitted-source-freeze-tool")
        tooling[relative] = digest(committed)
    sys.path.insert(0, str(tools / "install"))
    try:
        import yaml
        from mstack_source import source
        metadata, source_files = source(repository, commit)
    except (ImportError, OSError, ValueError):
        raise EvaluationError("source-freeze-unavailable") from None
    finally:
        sys.path.pop(0)
    files = {key: value["data"].decode() for key, value in source_files.items() if key.startswith("skills/")}
    # This helper remains owned by DeepSWE; freeze its existing Git blob for reuse.
    helper = subprocess.check_output(["git", "-C", str(repository), "show", metadata["commit"] + ":evals/deepswe/auth_state.py"], stderr=subprocess.PIPE).decode()
    files["helpers/auth_state.py"] = helper
    catalog = []
    for entry in metadata["inventory"]["skills"]:
        path = "skills/" + entry["name"] + "/SKILL.md"
        text = files[path]
        try:
            front = yaml.safe_load(text.split("---\n", 2)[1])
            policy_file = "skills/" + entry["name"] + "/agents/openai.yaml"
            policy = yaml.safe_load(files[policy_file]) if policy_file in files else {}
            implicit = front.get("disable-model-invocation") is not True and (policy or {}).get("policy", {}).get("allow_implicit_invocation") is not False
            if front["name"] != entry["name"] or not isinstance(front["description"], str):
                raise ValueError()
        except (ValueError, KeyError, IndexError, TypeError):
            raise EvaluationError("invalid-source-catalog") from None
        catalog.append({"name": front["name"], "description": front["description"], "path": path, "sha256": digest(text.encode()), "invocation": "automatic" if implicit else "explicit-only"})
    return {"schema_version": 1, "id": identity, "kind": "agent", "source_commit": metadata["commit"], "model": model, "reasoning": reasoning,
            "harness": {"name": "codex-app-server", "version": environment["codex"]}, "environment": {**environment, "freeze_tool": {"commit": head, "files": tooling}},
            "budget_seconds": seconds, "max_turns": 1, "instructions": {"global/AGENTS.md": source_files["instructions/global/AGENTS.md"]["data"].decode()},
            "catalog": catalog, "source_files": files}
