from pathlib import Path
import sys
import tempfile
import unittest

from codex_evaluation import CodexDocker
from codex_rpc import RPC
from evaluation import EvaluationError


class CleanupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_close_releases_stdin_when_the_real_child_has_already_exited(self):
        rpc = RPC([sys.executable, "-c", "print('{}',flush=True)"], self.root)
        rpc.process.wait(timeout=5)
        rpc.close()
        self.assertTrue(rpc.process.stdin.closed)
        self.assertFalse(rpc.reader.is_alive())

    def test_container_disappearing_between_inspect_and_stop_is_confirmed_absent(self):
        tool = self.root / "docker.py"
        tool.write_text("import sys\nif sys.argv[1]=='inspect': print('owned-token')\nelif sys.argv[1]=='stop': sys.exit(1)\nelif sys.argv[1]=='ps': pass\nelse: sys.exit(2)\n")
        cid = self.root / "owned.cid"; cid.write_text("synthetic-container-id")
        CodexDocker._stop_container([sys.executable, str(tool)], {}, cid, "owned-token")
        with self.assertRaisesRegex(EvaluationError, "container-ownership-changed"):
            CodexDocker._stop_container([sys.executable, str(tool)], {}, cid, "someone-else")
        tool.write_text(tool.read_text().replace("elif sys.argv[1]=='ps': pass", "elif sys.argv[1]=='ps': sys.exit(1)"))
        with self.assertRaisesRegex(EvaluationError, "container-stop-unverified"):
            CodexDocker._stop_container([sys.executable, str(tool)], {}, cid, "owned-token")


if __name__ == "__main__":
    unittest.main()
