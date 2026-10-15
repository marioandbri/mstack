"""Isolated Codex RPC execution with the existing private benchmark OAuth helper."""
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import tempfile
import time
import uuid

from codex_rpc import RPC
from collector import _write_json
from evaluation import EvaluationError, private_directory
from records import digest


def docker_environment(root, endpoint, plugins=()):
    if not isinstance(endpoint, str) or not endpoint.startswith("unix://") or not Path(endpoint.removeprefix("unix://")).is_socket():
        raise EvaluationError("nonlocal-or-unavailable-docker")
    config = private_directory(Path(root) / "docker-config")
    config_file = config / "config.json"
    expected = {"cliPluginsExtraDirs": list(plugins)}
    if config_file.exists():
        if json.loads(config_file.read_text()) != expected:
            raise EvaluationError("docker-config-drift")
    else:
        _write_json(config_file, expected)
    return ["docker", "--config", str(config), "--host", endpoint], {"PATH": os.environ["PATH"], "DOCKER_CONFIG": str(config), "DOCKER_HOST": endpoint}


class CodexDocker:
    def __init__(self, control_root, auth_path):
        self.root = private_directory(control_root)
        self.auth_path = Path(auth_path).absolute()

    def _auth(self, profile):
        source = profile["source_files"].get("helpers/auth_state.py")
        if source is None:
            raise EvaluationError("benchmark-auth-helper-unavailable")
        path = self.root / ("auth-helper-" + digest(source.encode()) + ".py")
        if not path.exists():
            with path.open("x") as stream:
                path.chmod(0o600); stream.write(source)
        if digest(path.read_bytes()) != digest(source.encode()):
            raise EvaluationError("benchmark-auth-helper-changed")
        spec = importlib.util.spec_from_file_location("mstack_benchmark_auth", path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        module.validate_auth(self.auth_path)
        return module

    @staticmethod
    def _stop_container(docker, child_env, cid_path, token):
        if not cid_path.exists():
            return
        cid = cid_path.read_text().strip()
        inspected = subprocess.run([*docker, "inspect", cid, "--format", '{{index .Config.Labels "mstack.maintenance.owner"}}'], env=child_env, capture_output=True, text=True)
        if inspected.returncode == 0:
            if inspected.stdout.strip() != token:
                raise EvaluationError("container-ownership-changed")
            subprocess.run([*docker, "stop", "-t", "2", cid], env=child_env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=10)
        else:
            present = subprocess.run([*docker, "ps", "-a", "--no-trunc", "--filter", "id=" + cid, "--format", "{{.ID}}"], env=child_env, capture_output=True, text=True)
            if present.returncode != 0 or present.stdout.strip():
                raise EvaluationError("container-stop-unverified")

    def check(self, workspace, protocol, check):
        environment = protocol["profile"]["environment"]
        docker, child_env = docker_environment(self.root, environment["docker_endpoint"], environment.get("docker_plugin_directories", []))
        token = uuid.uuid4().hex
        cid = self.root / (token + ".cid")
        logs = private_directory(workspace.parent / "checks")
        path = logs / (check["id"] + ".log")
        command = [*docker, "run", "--rm", "--cidfile", str(cid), "--label", "mstack.maintenance.owner=" + token,
                   "--network=none", "--read-only", "--tmpfs", "/tmp:rw,nosuid,nodev", "--cap-drop=ALL", "--security-opt=no-new-privileges", "--memory=2g", "--cpus=2",
                   "--mount", f"type=bind,src={workspace},dst=/workspace,readonly", "--workdir", "/workspace" + ("/" + check["cwd"] if check["cwd"] != '.' else ''),
                   environment["image_digest"], *check["argv"]]
        try:
            with path.open("xb") as output:
                path.chmod(0o600)
                result = subprocess.run(command, env=child_env, stdout=output, stderr=subprocess.STDOUT, timeout=30)
        finally:
            self._stop_container(docker, child_env, cid, token)
        with path.open("rb") as source:
            sha = hashlib.file_digest(source, "sha256").hexdigest()
            source.seek(0); excerpt = source.read(4000).decode(errors="replace")
        return {"passed": result.returncode == 0, "exit_code": result.returncode, "output_sha256": sha, "output_excerpt": excerpt, "executor": "isolated-container-check"}

    def run(self, workspace, protocol, seconds):
        return self._run(workspace, protocol, seconds, preflight=False)

    def preflight(self, workspace, protocol, seconds=30):
        return self._run(workspace, protocol, seconds, preflight=True)

    def _run(self, workspace, protocol, seconds, preflight):
        profile = protocol["profile"]
        if profile["kind"] != "agent" or profile["harness"]["name"] != "codex-app-server":
            raise EvaluationError("unsupported-agent-transport")
        environment = profile["environment"]
        docker, child_env = docker_environment(self.root, environment["docker_endpoint"], environment.get("docker_plugin_directories", []))
        image = environment["image_digest"]
        actual = subprocess.check_output([*docker, "image", "inspect", image, "--format", "{{.Id}}"], env=child_env, stderr=subprocess.PIPE, text=True).strip()
        if actual != image:
            raise EvaluationError("evaluation-image-mismatch")
        helper = self._auth(profile)
        with helper.auth_lock(self.auth_path):
            original_hash = helper.digest(self.auth_path)
            home = Path(tempfile.mkdtemp(prefix=".maintenance-auth-", dir=self.auth_path.parent)); home.chmod(0o700)
            shutil.copyfile(self.auth_path, home / "auth.json"); (home / "auth.json").chmod(0o600)
            config = 'cli_auth_credentials_store = "file"\n[features]\napps = false\n[projects."/workspace"]\ntrust_level = "trusted"\n'
            (home / "config.toml").write_text(config); (home / "config.toml").chmod(0o600)
            global_text = profile["instructions"].get("global/AGENTS.md")
            if global_text is not None:
                (home / "AGENTS.md").write_text(global_text); (home / "AGENTS.md").chmod(0o600)
            preserved = False
            lifecycle = {"consumers_stopped": True}
            try:
                result = self._execute(workspace, protocol, seconds, home, docker, child_env, preflight, lifecycle)
                if global_text is not None:
                    result["global_instructions_preserved"] = (home / "AGENTS.md").read_bytes() == global_text.encode()
                return result
            finally:
                try:
                    if not lifecycle["consumers_stopped"]:
                        raise EvaluationError("benchmark-auth-consumer-not-stopped")
                    helper.persist_refresh(home / "auth.json", self.auth_path, original_hash)
                    preserved = True
                finally:
                    if preserved:
                        shutil.rmtree(home)
                    else:
                        # Keep refreshed credentials private, outside collected artifacts.
                        _write_json(self.root / ("auth-recovery-" + uuid.uuid4().hex + ".json"), {"state": "refresh-not-persisted", "private_home": str(home)})

    def _execute(self, workspace, protocol, seconds, home, docker, child_env, preflight, lifecycle):
        profile = protocol["profile"]
        token = uuid.uuid4().hex
        cid_path = self.root / (token + ".cid")
        name = "mstack-maintenance-" + token
        for path in (workspace, home):
            if "," in str(path):
                raise EvaluationError("unsupported-mount-path")
        command = [*docker, "run", "--rm", "-i", "--init", "--name", name, "--cidfile", str(cid_path), "--label", "mstack.maintenance.owner=" + token,
                   "--cap-drop=ALL", "--security-opt=no-new-privileges", "--memory=4g", "--cpus=2",
                   "--mount", f"type=bind,src={workspace},dst=/workspace", "--mount", f"type=bind,src={home},dst=/root/.codex",
                   "--mount", f"type=bind,src={workspace / '.agents/skills'},dst=/workspace/.agents/skills,readonly",
                   profile["environment"]["image_digest"]]
        setup = protocol["case"].get("setup_commands", [])
        if setup:
            bootstrap = "import json,os,subprocess,sys\nwith open('/workspace/setup.log','x') as log:\n os.chmod('/workspace/setup.log',0o600)\n for argv in json.loads(sys.argv[1]): subprocess.run(argv,cwd='/workspace',stdout=log,stderr=log,check=True)\nos.chdir('/workspace')\nos.execvp('codex',['codex','app-server','--listen','stdio://'])\n"
            command += ["python3", "-c", bootstrap, json.dumps(setup)]
        else:
            command += ["codex", "app-server", "--listen", "stdio://"]
        (workspace / ".agents/skills").mkdir(mode=0o700, parents=True, exist_ok=True)

        def stop():
            self._stop_container(docker, child_env, cid_path, token)

        rpc, thread_id, turn_id = None, None, None
        deadline = time.monotonic() + seconds
        calls = 0
        context = {"state": "unverified", "image_digest": profile["environment"]["image_digest"], "harness": profile["harness"]}
        try:
            lifecycle["consumers_stopped"] = False
            rpc = RPC(command, workspace, environment=child_env, stop=stop)
            def call(method, params):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError()
                return rpc.call(method, params, timeout=min(15, remaining))
            initialized = call("initialize", {"clientInfo": {"name": "mstack_maintenance_eval", "title": "mstack maintenance evaluation", "version": "1.0.0"}, "capabilities": {"experimentalApi": True}})
            rpc.send("initialized", request=False)
            catalog = call("skills/list", {"cwds": ["/workspace"], "forceReload": True})
            _write_json(workspace / "catalog.json", catalog)
            actual_skills = {skill["name"]: skill for entry in catalog.get("data", []) for skill in entry.get("skills", []) if skill.get("enabled", True)}
            missing = sorted({skill["name"] for skill in profile["catalog"]} - actual_skills.keys())
            thread = call("thread/start", {"model": profile["model"], "allowProviderModelFallback": False, "cwd": "/workspace", "approvalPolicy": "never", "sandbox": "danger-full-access", "ephemeral": True, "experimentalRawEvents": True, "config": {"model_reasoning_effort": profile["reasoning"]}})
            _write_json(workspace / "thread.json", thread)
            thread_id = thread["thread"]["id"]
            sources = thread.get("instructionSources", thread["thread"].get("instructionSources", []))
            expected = {"/root/.codex/AGENTS.md"} if "global/AGENTS.md" in profile["instructions"] else set()
            if "AGENTS.md" in protocol["case"]["fixture"] or "AGENTS.md" in profile["instructions"]:
                expected.add("/workspace/AGENTS.md")
            context.update({"catalog_missing": missing, "catalog_external": sorted(actual_skills.keys() - {s["name"] for s in profile["catalog"]}), "instruction_sources": sources, "instruction_sources_expected": sorted(expected), "session_id": thread["thread"].get("sessionId"), "thread_id": thread_id, "initialize": initialized})
            if not missing and expected.issubset(set(sources)):
                context["state"] = "verified"
            _write_json(workspace / "context.json", context)
            if preflight:
                return {"execution_status": "not-executed", "context": context, "model_calls": 0}
            inputs = [{"type": "text", "text": protocol["case"]["request"], "text_elements": []}]
            for name in protocol["case"].get("explicit_skills", []):
                inputs.append({"type": "skill", "name": name, "path": "/workspace/.agents/skills/" + name + "/SKILL.md"})
            turn = call("turn/start", {"threadId": thread_id, "effort": profile["reasoning"], "input": inputs}); calls = 1
            turn_id = turn["turn"]["id"]
            while time.monotonic() < deadline:
                try:
                    message = rpc.next(timeout=min(1, max(.001, deadline - time.monotonic())))
                except queue.Empty:
                    continue
                if message.get("_eof"):
                    raise EvaluationError("app-server-exited-during-turn")
                if message.get("method") == "turn/completed":
                    completion = message["params"]["turn"]
                    _write_json(workspace / "agent-result.json", completion)
                    return {"execution_status": "completed" if completion["status"] == "completed" else "interrupted" if completion["status"] == "interrupted" else "infrastructure-error", "context": context, "model_calls": None, "agent_turns_started": calls, "turn_status": completion["status"]}
                if message.get("method") == "item/tool/requestUserInput":
                    _write_json(workspace / "agent-question.json", message["params"])
                    rpc.send("turn/interrupt", {"threadId": thread_id, "turnId": turn_id})
                    return {"execution_status": "interrupted", "stop_reason": "awaiting-user-input", "context": context, "model_calls": None, "agent_turns_started": calls}
            raise TimeoutError()
        except TimeoutError:
            if rpc and thread_id and turn_id:
                rpc.send("turn/interrupt", {"threadId": thread_id, "turnId": turn_id})
            return {"execution_status": "timeout", "context": context, "model_calls": None, "agent_turns_started": calls}
        finally:
            try:
                if rpc:
                    rpc.close()
            finally:
                stop()
            lifecycle["consumers_stopped"] = True
