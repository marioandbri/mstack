"""Local mechanical fixture transport, explicitly distinct from a model harness."""
import json
import os
import signal
import subprocess
import sys

from evaluation import EvaluationError


class FixtureProcess:
    def run(self, workspace, protocol, seconds):
        if protocol["profile"]["kind"] != "fixture" or protocol["case"]["kind"] != "synthetic-fixture":
            raise EvaluationError("fixture-transport-requires-synthetic-case")
        path = workspace / ".evaluation/fixture.py"
        if ".evaluation/fixture.py" not in protocol["case"]["fixture"] or path.is_symlink():
            raise EvaluationError("missing-fixture-program")
        with (workspace / "fixture.log").open("x") as output:
            (workspace / "fixture.log").chmod(0o600)
            process = subprocess.Popen([sys.executable, "-I", str(path)], cwd=workspace, stdout=output, stderr=output, start_new_session=True)
            try:
                process.wait(timeout=seconds)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL); process.wait()
                raise
        with (workspace / "events.jsonl").open("x") as events:
            (workspace / "events.jsonl").chmod(0o600)
            events.write(json.dumps({"type": "mechanical-fixture-completed", "returncode": process.returncode}) + "\n")
        return {"execution_status": "completed" if process.returncode == 0 else "infrastructure-error", "context": {"state": "verified-fixture", "instructions": sorted(protocol["profile"]["instructions"])}, "model_calls": 0}
