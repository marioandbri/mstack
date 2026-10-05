"""Small Pier adapter: install a frozen AGENTS.md and optionally user skills.

The native Codex runner, installation, authentication and verifier remain Pier's.
Only use this adapter in disposable benchmark containers.
"""
from __future__ import annotations

import hashlib
import json
import shlex
import os
import tempfile
from datetime import datetime, timedelta, timezone
from auth_state import digest, persist_refresh, validate_auth
from pier.models.agent.network import NetworkAllowlist
from pathlib import Path

from pier.agents.installed.codex import Codex

NODE_VERSION = "24.12.0"

BENCHMARK_CONTRACT = """

## Authorization for this isolated benchmark run
Work inside the disposable task repository. You are explicitly authorized to
create local Git commits containing your solution, as required by this benchmark.
Do not push. Do not access hidden tests, reference solutions or verifier outputs.
Use the supplied task and available instructions. Do not download additional
skills/plugins, add MCP integrations, or delegate to Pi or other external agents.
This authorization is identical for both experimental conditions.

## Submission contract
The verifier extracts committed changes only. Keep a local checkpoint commit
once the first focused checks pass, then commit subsequent corrections as you go.
Do not defer every commit until long type checks, builds or full test suites end.
A checkpoint is explicitly authorized while broader verification is pending;
it records work in progress and does not claim the solution is complete or tested.
Continue the required verification, and report failed or unfinished checks honestly.
Never commit credentials, runtime logs, caches or unrelated generated files.
"""


def delivery_contract(budget_seconds: int, started_at: datetime) -> str:
    if type(budget_seconds) is not int or budget_seconds <= 0:
        raise ValueError('Benchmark budget must be a positive integer')
    deadline = started_at + timedelta(seconds=budget_seconds)
    return BENCHMARK_CONTRACT + (
        f'\nAgent budget: {budget_seconds} seconds. '
        f'Started at {started_at.isoformat()}; deadline {deadline.isoformat()} UTC.\n'
        'Check the clock when running long commands and preserve a committed '
        'submission before the deadline. A timeout remains a benchmark failure.\n'
    )


class MstackCodex(Codex):
    def __init__(self, *args, agents_md: str, skills_snapshot: str | None = None, benchmark_auth: str, budget_seconds: int = 1800, **kwargs):
        super().__init__(*args, **kwargs)
        delivery_contract(budget_seconds, datetime.now(timezone.utc))
        self._budget_seconds = budget_seconds
        self._agents_path = Path(agents_md).resolve(strict=True)
        self._skills_path = (
            Path(skills_snapshot).resolve(strict=True) if skills_snapshot else None
        )
        if not self._agents_path.is_file() or not self._agents_path.read_bytes():
            raise ValueError("AGENTS.md must be a non-empty file")
        if self.skills_dir or self.mcp_servers:
            raise ValueError("This minimal pilot excludes task-provided skills/MCP")
        self._skill_names: list[str] = []
        self._benchmark_auth = Path(benchmark_auth).absolute()
        validate_auth(self._benchmark_auth)
        self._auth_digest = digest(self._benchmark_auth)
        self._skill_hashes = {}
        self._auth_saved = False
        self._auth_error = False

    def install_spec(self):
        spec = super().install_spec()
        for step in spec.steps:
            if 'nvm install 22 && nvm alias default 22' in step.run:
                step.run = step.run.replace('nvm install 22 && nvm alias default 22',
                                           f'nvm install {NODE_VERSION} && nvm alias default {NODE_VERSION}')
        return spec

    def _resolve_auth_json_path(self):
        return self._benchmark_auth

    def network_allowlist(self):
        domains = set(super().network_allowlist().domains)
        domains.update(('chatgpt.com', 'auth.openai.com'))
        return NetworkAllowlist(domains=sorted(domains))

    async def exec_as_agent(self, environment, command, **kwargs):
        cleanup = f'rm -rf {shlex.quote(self._REMOTE_CODEX_SECRETS_DIR.as_posix())} "$CODEX_HOME"'
        if command == cleanup:
            fd, name = tempfile.mkstemp(prefix='.oauth-refresh-', dir=self._benchmark_auth.parent)
            os.close(fd)
            temporary = Path(name)
            try:
                await environment.download_file(
                    (self._REMOTE_CODEX_SECRETS_DIR / 'auth.json').as_posix(), temporary)
                temporary.chmod(0o600)
                persist_refresh(temporary, self._benchmark_auth, self._auth_digest)
                self._auth_saved = True
            except Exception:
                self._auth_error = True
            finally:
                temporary.unlink(missing_ok=True)
        return await super().exec_as_agent(environment, command=command, **kwargs)

    async def setup(self, environment):
        await super().setup(environment)
        home = self._REMOTE_CODEX_HOME.as_posix()
        target = f"{home}/AGENTS.md"
        await self.exec_as_agent(
            environment,
            command=f"mkdir -p {shlex.quote(home)}; "
                    f"test ! -e {shlex.quote(home + '/AGENTS.override.md')}",
        )
        await environment.upload_file(self._agents_path, target)
        await self.exec_as_root(environment, command=f"chmod 0644 {shlex.quote(target)}")
        expected_hash = hashlib.sha256(self._agents_path.read_bytes()).hexdigest()
        await self.exec_as_agent(
            environment,
            command=f"printf '%s\\n' {shlex.quote(expected_hash + '  ' + target)} | sha256sum -c -",
        )
        if self._skills_path:
            self._skill_names = sorted(p.parent.name for p in self._skills_path.glob('*/SKILL.md'))
            remote = "/tmp/mstack-benchmark-skills"
            await self.exec_as_agent(environment, command=f"mkdir -p {remote}")
            await environment.upload_dir(source_dir=self._skills_path, target_dir=remote)
            await self.exec_as_root(environment, command=f"chmod -R a+rX {remote}")
            self._skill_hashes = {
                p.relative_to(self._skills_path).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(self._skills_path.rglob('*')) if p.is_file()
            }
            checksums = ''.join(f'{value}  {name}\n' for name, value in self._skill_hashes.items())
            fd, name = tempfile.mkstemp(prefix='mstack-skill-hashes-')
            os.close(fd)
            checksum_file = Path(name)
            try:
                checksum_file.write_text(checksums)
                await environment.upload_file(checksum_file, '/tmp/mstack-skills.sha256')
                await self.exec_as_root(environment, command='chmod 0644 /tmp/mstack-skills.sha256')
            finally:
                checksum_file.unlink(missing_ok=True)
            self.skills_dir = remote
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        (self.logs_dir / 'mstack-injection.json').write_text(json.dumps({
            'agents_md_sha256': expected_hash,
            'agents_md_container_path': target,
            'added_user_skills': self._skill_names,
            'skill_hashes': self._skill_hashes,
            'note': 'File injection audit, not proof of skill invocation.',
        }, indent=2) + '\n')

    def _build_register_skills_command(self):
        command = super()._build_register_skills_command()
        if not command:
            return None
        # Pier's default copy tolerates failures; make missing manifests fatal here.
        checks = [
            'test -r "$HOME/.agents/skills/"' + shlex.quote(name + '/SKILL.md')
            for name in self._skill_names
        ]
        return command + '\n' + ' && '.join(checks) + '\ncd "$HOME/.agents/skills" && sha256sum -c /tmp/mstack-skills.sha256'

    async def run(self, instruction, environment, context):
        started_at = datetime.now(timezone.utc)
        contract = delivery_contract(self._budget_seconds, started_at)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        (self.logs_dir / 'mstack-delivery.json').write_text(json.dumps({
            'version': 2, 'budget_seconds': self._budget_seconds,
            'started_at': started_at.isoformat(),
            'deadline': (started_at + timedelta(seconds=self._budget_seconds)).isoformat(),
            'contract_sha256': hashlib.sha256(contract.encode()).hexdigest(),
        }, indent=2) + '\n')
        try:
            await super().run(instruction + contract, environment, context)
        finally:
            if not self._auth_saved or self._auth_error:
                raise RuntimeError('Benchmark OAuth persistence failed; stop and log in again')
