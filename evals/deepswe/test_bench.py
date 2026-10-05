import asyncio
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import bench
from auth_state import auth_lock, digest, persist_refresh, validate_auth
from mstack_codex import MstackCodex
from pier.agents.installed.codex import Codex
from pier.models.job.config import JobConfig


def credential(path, token='original'):
    path.write_text(json.dumps({'auth_mode': 'chatgpt', 'tokens': {
        'access_token': token, 'refresh_token': 'refresh'}}))
    path.chmod(0o600)
    return path


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.auth = credential(self.root / 'auth.json')

    def test_oauth_only(self):
        self.auth.write_text('{"OPENAI_API_KEY":"fixture"}')
        with self.assertRaises(ValueError):
            validate_auth(self.auth)

    def test_permissions_are_enforced(self):
        self.auth.chmod(0o644)
        with self.assertRaises(ValueError):
            validate_auth(self.auth)

    def test_symlinks_rejected(self):
        link = self.root / 'linked.json'
        link.symlink_to(self.auth)
        with self.assertRaises(ValueError):
            validate_auth(link)

    def test_atomic_renewal(self):
        refreshed = credential(self.root / 'renewed.json', 'renewed')
        persist_refresh(refreshed, self.auth, digest(self.auth))
        self.assertEqual(json.loads(self.auth.read_text())['tokens']['access_token'], 'renewed')
        self.assertEqual(self.auth.stat().st_mode & 0o777, 0o600)
        self.assertFalse(refreshed.exists())

    def test_competing_write_is_preserved(self):
        expected = digest(self.auth)
        refreshed = credential(self.root / 'renewed.json', 'renewed')
        credential(self.auth, 'competing')
        with self.assertRaises(ValueError):
            persist_refresh(refreshed, self.auth, expected)
        self.assertEqual(json.loads(self.auth.read_text())['tokens']['access_token'], 'competing')

    def test_only_one_run_can_hold_login(self):
        with auth_lock(self.auth):
            with self.assertRaises(ValueError):
                with auth_lock(self.auth):
                    self.fail('second lock acquired')


class ProfileTests(unittest.TestCase):
    def test_a_b_only_differ_in_skills(self):
        manifest = dict(codex_version='0.159.0', reasoning='high', auth_json='/private/benchmark/auth.json',
                        model='gpt-6.1-sol', agent_timeout_sec=1800, tasks=['fixture'])
        a = bench.make_config(manifest, 'A')
        b = bench.make_config(manifest, 'B')
        JobConfig.model_validate(a)
        JobConfig.model_validate(b)
        self.assertNotIn('skills_snapshot', a['agents'][0]['kwargs'])
        self.assertIn('skills_snapshot', b['agents'][0]['kwargs'])
        b['agents'][0]['kwargs'].pop('skills_snapshot')
        b['job_name'] = 'A'
        self.assertEqual(a, b)
        self.assertEqual(a['n_concurrent_trials'], 1)

    def test_pin_covers_verifier_without_changing_instructions(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / 'tests').mkdir()
            (root / 'task.toml').write_text('docker_image = "registry/task:v1"\n')
            (root / 'tests/Dockerfile').write_text('FROM registry/task:v1\nRUN true\n')
            (root / 'instruction.md').write_text('unchanged prompt')
            bench.pin_task_image(root, 'registry/task:v1', 'registry/task@sha256:abc')
            self.assertIn('registry/task@sha256:abc', (root / 'task.toml').read_text())
            self.assertEqual((root / 'tests/Dockerfile').read_text(), 'FROM registry/task@sha256:abc\nRUN true\n')
            self.assertEqual((root / 'instruction.md').read_text(), 'unchanged prompt')

    def test_pin_rejects_an_unrecognized_task_format(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / 'task.toml').write_text('unexpected = "fixture"')
            with self.assertRaises(ValueError):
                bench.pin_task_image(root, 'registry/task:v1', 'registry/task@sha256:abc')

    @unittest.skipUnless(os.environ.get('MSTACK_DOCKER_E2E') == '1', 'opt-in real Docker CLI integration')
    def test_compose_is_visible_with_isolated_docker_config(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / 'config.json').write_text(json.dumps(bench.docker_config()))
            env = os.environ.copy()
            env['DOCKER_CONFIG'] = str(root)
            import subprocess
            output = subprocess.check_output(['docker','compose','version'], env=env, text=True)
            self.assertIn('Docker Compose version', output)

    def test_hashes_detect_content_changes(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / 'AGENTS.md').write_text('first')
            before = bench.tree_hashes(root)
            (root / 'AGENTS.md').write_text('second')
            self.assertNotEqual(before, bench.tree_hashes(root))

    def test_report_separates_failure_error_and_missing(self):
        with tempfile.TemporaryDirectory() as name, patch.object(bench, 'STATE', Path(name)):
            state = Path(name)
            (state / 'manifest.json').write_text(json.dumps({'tasks': ['pass', 'error', 'missing']}))
            for task, result in [('pass', {'verifier_result': {'rewards': {'reward': 1}}}),
                                 ('error', {'exception_info': {'exception_type': 'BuildError'}})]:
                folder = state / 'jobs/A' / task
                folder.mkdir(parents=True)
                (folder / 'result.json').write_text(json.dumps({'task_name': task, **result}))
            bench.report(None)
            import csv
            with (state / 'comparison.csv').open() as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual([r['status'] for r in rows[:3]], ['pass', 'error', 'missing'])
            self.assertTrue(all(r['input_tokens'] == '' for r in rows))


    def test_report_matches_the_pier_task_name_from_frozen_metadata(self):
        with tempfile.TemporaryDirectory() as name, patch.object(bench, 'STATE', Path(name)):
            state = Path(name)
            task = 'dynamodb-toolbox-lazy-recursive-schemas'
            (state / 'manifest.json').write_text(json.dumps({'tasks': [task]}))
            task_dir = state / 'deep-swe/tasks' / task
            task_dir.mkdir(parents=True)
            (task_dir / 'task.toml').write_text('[task]\nname = "datacurve/' + task + '"\n')
            trial = state / 'jobs/A/trial'
            trial.mkdir(parents=True)
            (trial / 'result.json').write_text(json.dumps({
                'task_name': 'datacurve/' + task,
                'exception_info': {'exception_type': 'AgentTimeoutError'},
                'verifier_result': {'rewards': {'reward': 0}},
                'agent_result': {'n_input_tokens': 8950680, 'n_cache_tokens': 8529920,
                                 'n_output_tokens': 42970},
            }))
            bench.report(None)
            import csv
            with (state / 'comparison.csv').open() as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]['status'], 'timeout')
            self.assertEqual(rows[0]['output_tokens'], '42970')
            self.assertEqual(rows[1]['status'], 'missing')


class AdapterTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.auth = credential(self.root / 'auth.json')
        agents = self.root / 'AGENTS.md'
        agents.write_text('fixture instructions')
        self.agent = MstackCodex(logs_dir=self.root / 'logs', model_name='gpt-6.1-sol',
                                 agents_md=str(agents), benchmark_auth=str(self.auth), version='0.159.0')

    def test_node_runtime_is_pinned(self):
        commands = '\n'.join(step.run for step in self.agent.install_spec().steps)
        self.assertIn('nvm install 24.12.0', commands)
        self.assertNotIn('nvm install 22 &&', commands)

    def test_chatgpt_network_and_private_auth_path(self):
        self.assertIn('chatgpt.com', self.agent.network_allowlist().domains)
        self.assertIn('auth.openai.com', self.agent.network_allowlist().domains)
        self.assertEqual(self.agent._resolve_auth_json_path(), self.auth)

    async def test_upstream_cleanup_preserves_refreshed_oauth(self):
        async def download(source, destination):
            self.assertEqual(source, '/tmp/codex-secrets/auth.json')
            credential(destination, 'renewed')
        environment = SimpleNamespace(download_file=download)
        async def upstream_run(agent, instruction, environment, context):
            await agent.exec_as_agent(environment, command='rm -rf /tmp/codex-secrets "$CODEX_HOME"')
        async def upstream_exec(*args, **kwargs):
            return None
        with patch.object(Codex, 'run', upstream_run), patch.object(Codex, 'exec_as_agent', upstream_exec):
            await self.agent.run('fixture task', environment, None)
        self.assertEqual(json.loads(self.auth.read_text())['tokens']['access_token'], 'renewed')
        self.assertEqual(list(self.root.glob('.oauth-refresh-*')), [])

    async def test_lost_refresh_causes_failure(self):
        async def download(*args):
            raise OSError('fixture transfer failed')
        environment = SimpleNamespace(download_file=download)
        async def upstream_run(agent, instruction, environment, context):
            await agent.exec_as_agent(environment, command='rm -rf /tmp/codex-secrets "$CODEX_HOME"')
        async def upstream_exec(*args, **kwargs):
            return None
        with patch.object(Codex, 'run', upstream_run), patch.object(Codex, 'exec_as_agent', upstream_exec):
            with self.assertRaisesRegex(RuntimeError, 'OAuth persistence failed'):
                await self.agent.run('fixture task', environment, None)
        self.assertEqual(json.loads(self.auth.read_text())['tokens']['access_token'], 'original')


if __name__ == '__main__':
    unittest.main()
