"""Prepare snapshots, run two Pier profiles, and export a paired CSV.

Usage: uv run bench.py --help
Requires git, Docker with Compose, and a separate ChatGPT benchmark login.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
import platform
import random
import re
import shutil
import subprocess
import sys
import tomllib
from auth_state import DEFAULT_HOME, auth_lock, validate_auth
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = ROOT / 'state'
PIER_VERSION = '0.3.1'
DATASET_URL = 'https://github.com/datacurve-ai/deep-swe.git'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_hashes(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): sha(p)
            for p in sorted(root.rglob('*')) if p.is_file() and '.git' not in p.parts}


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def capture(*args: str, env=None) -> str:
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT, env=env).strip()


def make_config(manifest: dict, profile: str) -> dict:
    kwargs = {
        'version': manifest['codex_version'],
        'reasoning_effort': manifest['reasoning'],
        'agents_md': str(STATE / 'snapshot/AGENTS.md'),
        'benchmark_auth': manifest['auth_json'],
        'config_toml': 'cli_auth_credentials_store = "file"\n[features]\nresponses_websockets = false\nresponses_websockets_v2 = false\n',
    }
    if profile == 'B':
        kwargs['skills_snapshot'] = str(STATE / 'snapshot/skills')
    return {
        'job_name': profile,
        'jobs_dir': str(STATE / 'jobs'),
        'n_attempts': 1,
        'n_concurrent_trials': 1,
        'retry': {'max_retries': 0},
        'environment': {'type': 'docker', 'delete': True},
        'agents': [{
            'import_path': 'mstack_codex:MstackCodex',
            'model_name': manifest['model'],
            'override_timeout_sec': manifest['agent_timeout_sec'],
            'kwargs': kwargs,
        }],
        'tasks': [{'path': str(STATE / 'deep-swe/tasks' / name)}
                  for name in manifest['tasks']],
    }


def docker_config() -> dict:
    source = Path(os.environ.get('DOCKER_CONFIG', str(Path.home() / '.docker')))
    config_file = source / 'config.json'
    configured = json.loads(config_file.read_text()) if config_file.is_file() else {}
    directories = [source / 'cli-plugins', Path.home() / '.docker/cli-plugins']
    directories.extend(Path(p) for p in configured.get('cliPluginsExtraDirs', []))
    return {'auths': {}, 'cliPluginsExtraDirs': sorted({str(p) for p in directories if p.is_dir()})}


def pin_task_image(task_dir: Path, image: str, frozen: str) -> None:
    task_path = task_dir / 'task.toml'
    original = task_path.read_text()
    changed = original.replace('docker_image = ' + json.dumps(image),
                               'docker_image = ' + json.dumps(frozen))
    if changed == original:
        raise ValueError('Cannot pin the task image in this task format')
    task_path.write_text(changed)
    for dockerfile in task_dir.rglob('Dockerfile'):
        text = dockerfile.read_text()
        dockerfile.write_text(re.sub(r'(?m)^(FROM\s+)' + re.escape(image) + r'(?=\s|$)',
                                    lambda match: match.group(1) + frozen, text))


def prepare(args) -> None:
    if STATE.exists():
        raise ValueError('state/ already exists; do not overwrite your baseline. '
                         'Choose a new --state-dir for another experiment.')
    agents = Path(args.agents).expanduser().resolve(strict=True)
    skills = Path(args.skills).expanduser().resolve(strict=True)
    auth = Path(args.auth_json).expanduser().absolute()
    if auth.exists():
        validate_auth(auth)
    if not agents.is_file() or not agents.read_bytes():
        raise ValueError('--agents must point to a non-empty AGENTS.md')
    if not skills.is_dir() or not list(skills.glob('*/SKILL.md')):
        raise ValueError('--skills must contain skill-name/SKILL.md directories')
    if auth.resolve().is_relative_to(STATE):
        raise ValueError('OAuth credentials must live outside evaluation state')
    version = args.codex_version
    if not version:
        match = re.search(r'\b\d+\.\d+\.\d+(?:-[\w.-]+)?\b', capture('codex', '--version'))
        if not match:
            raise ValueError('Cannot determine Codex version; pass --codex-version explicitly')
        version = match.group(0)
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[\w.-]+)?', version):
        raise ValueError('Use an exact Codex package version, not latest')
    if args.tasks < 1 or args.timeout < 1:
        raise ValueError('--tasks and --timeout must be positive')
    STATE.mkdir()
    try:
        if args.dataset:
            dataset = Path(args.dataset).expanduser().resolve(strict=True)
            shutil.copytree(dataset, STATE / 'deep-swe')
        else:
            subprocess.run(['git', 'clone', '--depth', '1', DATASET_URL,
                            str(STATE / 'deep-swe')], check=True)
        tasks_root = STATE / 'deep-swe/tasks'
        eligible = []
        details = {}
        for path in sorted(tasks_root.iterdir()):
            task_file = path / 'task.toml'
            if not task_file.is_file():
                continue
            task = tomllib.loads(task_file.read_text())
            environment = task.get('environment', {})
            if args.language and task.get('metadata', {}).get('language') != args.language:
                continue
            if (environment.get('mcp_servers') or environment.get('skills_dir')
                    or str(environment.get('os', 'linux')).lower() != 'linux'):
                continue
            eligible.append(path.name)
            details[path.name] = {k: environment[k] for k in
                                 ('cpus', 'memory_mb', 'storage_mb', 'docker_image')
                                 if k in environment}
        if len(eligible) < args.tasks:
            raise ValueError(f'Only {len(eligible)} compatible tasks found')
        selected = random.Random(args.seed).sample(eligible, args.tasks)
        original_task_hashes = {name: tree_hashes(tasks_root / name) for name in selected}
        images = {}
        for name in selected:
            task_path = tasks_root / name / 'task.toml'
            image = details[name].get('docker_image')
            if not image:
                raise ValueError('Pilot requires prebuilt task images')
            inspection = json.loads(capture('docker', 'image', 'inspect', image))[0]
            digests = inspection.get('RepoDigests') or []
            repository = image.rsplit(':', 1)[0]
            frozen = next((d for d in digests if d.split('@')[0] == repository), None)
            if not frozen:
                raise ValueError(f'Pull the task image before preparing: {image}')
            if inspection['Os'] + '/' + inspection['Architecture'] != args.platform:
                raise ValueError('Task image platform does not match --platform')
            images[name] = {'source': image, 'digest': frozen, 'id': inspection['Id']}
            pin_task_image(task_path.parent, image, frozen)
        snapshot = STATE / 'snapshot'
        snapshot.mkdir()
        shutil.copyfile(agents, snapshot / 'AGENTS.md')
        # Dereference symlinks. Copy only actual skill directories, not a home/config tree.
        (snapshot / 'skills').mkdir()
        for skill in sorted(skills.iterdir()):
            if skill.is_dir() and (skill / 'SKILL.md').is_file():
                shutil.copytree(skill, snapshot / 'skills' / skill.name, symlinks=False,
                                ignore=shutil.ignore_patterns('.git', '__pycache__', '.DS_Store'))
        manifest = {
            'created_at': datetime.now(timezone.utc).isoformat(),
            'auth_mode': 'chatgpt',
            'images': images,
            'original_task_hashes': original_task_hashes,
            'auth_json': str(auth),
            'platform': args.platform,
            'language_filter': args.language,
            'source_commit': capture('git', '-C', str(ROOT.parents[1]), 'rev-parse', 'HEAD'),
            'host_docker': json.loads(capture('docker', 'info', '--format', '{{json .}}'))['MemTotal'],
            'pier_version': PIER_VERSION,
            'python_version': platform.python_version(),
            'node_version': '24.12.0',
            'dataset_commit': capture('git', '-C', str(STATE / 'deep-swe'), 'rev-parse', 'HEAD'),
            'codex_version': version,
            'model': args.model,
            'reasoning': args.reasoning,
            'agent_timeout_sec': args.timeout,
            'tasks': selected,
            'selection_seed': args.seed,
            'task_resources': {name: details[name] for name in selected},
            'snapshot_hashes': tree_hashes(snapshot),
            'task_hashes': {name: tree_hashes(tasks_root / name) for name in selected},
            'adapter_sha256': sha(ROOT / 'mstack_codex.py'),
            'runner_sha256': sha(Path(__file__)),
            'auth_helper_sha256': sha(ROOT / 'auth_state.py'),
            'uv_lock_sha256': sha(ROOT / 'uv.lock') if (ROOT / 'uv.lock').exists() else None,
        }
        (STATE / 'docker-config').mkdir()
        write_json(STATE / 'docker-config/config.json', docker_config())
        manifest['docker_config_sha256'] = sha(STATE / 'docker-config/config.json')
        # Validate against the installed Pier schema before any paid run.
        from pier.models.job.config import JobConfig
        for profile in ('A', 'B'):
            config = make_config(manifest, profile)
            JobConfig.model_validate(config)
            write_json(STATE / f'{profile}.json', config)
        write_json(STATE / 'manifest.json', manifest)
        (STATE / 'tasks.txt').write_text('\n'.join(selected) + '\n')
    except BaseException:
        # This directory was created by this invocation and contains no previous results.
        shutil.rmtree(STATE)
        raise
    print(f'Prepared {len(selected)} tasks, Codex {version}, {args.model}, reasoning={args.reasoning}.')
    print('A: unchanged AGENTS.md; B: same AGENTS.md + snapshot of user skills.')
    print(f'Agent limit: {args.timeout}s/task. This is not a dollar/token spending cap.')
    print('Check resources/images for your Docker host in state/manifest.json before running.')
    print('Tasks:', ', '.join(selected))


def verify_frozen(manifest: dict) -> None:
    if manifest.get('docker_config_sha256') and sha(STATE / 'docker-config/config.json') != manifest['docker_config_sha256']:
        raise ValueError('Docker runtime configuration changed')
    if manifest.get('python_version') and platform.python_version() != manifest['python_version']:
        raise ValueError('Python runtime changed')
    if importlib.metadata.version('datacurve-pier') != manifest['pier_version']:
        raise ValueError('Pier version changed')
    if tree_hashes(STATE / 'snapshot') != manifest['snapshot_hashes']:
        raise ValueError('Snapshot changed; do not compare against the existing baseline')
    for name in manifest['tasks']:
        if tree_hashes(STATE / 'deep-swe/tasks' / name) != manifest['task_hashes'][name]:
            raise ValueError(f'Task files changed: {name}')
    for name, key in [('mstack_codex.py', 'adapter_sha256'), ('bench.py', 'runner_sha256'), ('auth_state.py', 'auth_helper_sha256')]:
        if sha(ROOT / name) != manifest[key]:
            raise ValueError(f'{name} changed since preparation')
    if manifest['uv_lock_sha256'] and sha(ROOT / 'uv.lock') != manifest['uv_lock_sha256']:
        raise ValueError('uv.lock changed between preparations/runs')


def runtime_env(manifest: dict) -> dict:
    env = os.environ.copy()
    for key in ('OPENAI_API_KEY', 'CODEX_AUTH_JSON_PATH', 'CODEX_FORCE_AUTH_JSON',
                'OPENAI_BASE_URL', 'OPENAI_API_BASE', 'CODEX_HOME'):
        env.pop(key, None)
    env['DOCKER_DEFAULT_PLATFORM'] = manifest['platform']
    env['DOCKER_CONFIG'] = str(STATE / 'docker-config')
    if sys.platform == 'darwin':
        env['DOCKER_HOST'] = 'unix://' + str(Path.home() / '.docker/run/docker.sock')
    env['PYTHONPATH'] = str(ROOT) + os.pathsep + env.get('PYTHONPATH', '')
    return env


def run_profile(args) -> None:
    manifest = json.loads((STATE / 'manifest.json').read_text())
    verify_frozen(manifest)
    auth = Path(manifest['auth_json'])
    validate_auth(auth)
    env = runtime_env(manifest)
    capture('docker', 'info', env=env)
    capture('docker', 'compose', 'version', env=env)
    config_path = STATE / f'{args.profile}.json'
    if json.loads(config_path.read_text()) != make_config(manifest, args.profile):
        raise ValueError('Profile changed after preparation')
    if (STATE / 'jobs' / args.profile).exists():
        raise ValueError(f'Profile {args.profile} already has a job. Existing results are not overwritten.')
    env = runtime_env(manifest)
    with auth_lock(auth):
        subprocess.run([sys.executable, '-m', 'pier.cli.main', 'run', '-c', str(config_path)],
                       cwd=ROOT, env=env, check=True)


def duration(timing: dict) -> float | None:
    if timing.get('started_at') and timing.get('finished_at'):
        start = datetime.fromisoformat(timing['started_at'].replace('Z', '+00:00'))
        end = datetime.fromisoformat(timing['finished_at'].replace('Z', '+00:00'))
        return round((end - start).total_seconds(), 2)
    return None


def report(_args) -> None:
    manifest = json.loads((STATE / 'manifest.json').read_text())
    rows = []
    task_names = {name: name for name in manifest['tasks']}
    for name in manifest['tasks']:
        metadata_path = STATE / 'deep-swe/tasks' / name / 'task.toml'
        if metadata_path.is_file():
            declared = tomllib.loads(metadata_path.read_text()).get('task', {}).get('name')
            if declared:
                if declared in task_names and task_names[declared] != name:
                    raise ValueError(f'Ambiguous task name: {declared}')
                task_names[declared] = name
    for profile in ('A', 'B'):
        results = {}
        for file in sorted((STATE / 'jobs' / profile).glob('*/result.json')):
            result = json.loads(file.read_text())
            name = task_names.get(result.get('task_name'))
            if name is None:
                raise ValueError(f"Unrecognized task result name: {result.get('task_name')}")
            if name in results:
                raise ValueError(f'Multiple trials for {profile}/{name}; inspect manually')
            results[name] = result
        for name in manifest['tasks']:
            result = results.get(name, {})
            reward = (result.get('verifier_result') or {}).get('rewards') or {}
            usage = result.get('agent_result') or {}
            error = (result.get('exception_info') or {}).get('exception_type')
            value = reward.get('reward')
            status = ('missing' if not result else 'timeout' if error == 'AgentTimeoutError'
                      else 'error' if error else 'pass' if value == 1
                      else 'fail' if value == 0 else 'unscored')
            rows.append({
                'profile': profile, 'task': name, 'status': status,
                'reward': value, 'error': error,
                'agent_seconds': duration(result.get('agent_execution') or {}),
                'input_tokens': usage.get('n_input_tokens'),
                'cached_input_tokens': usage.get('n_cache_tokens'),
                'output_tokens': usage.get('n_output_tokens'),
                'estimated_cost_usd': usage.get('cost_usd'),
            })
    summary = {profile: {
        'planned': len(manifest['tasks']),
        'statuses': {status: sum(r['profile'] == profile and r['status'] == status for r in rows)
                     for status in ('pass', 'fail', 'timeout', 'error', 'missing', 'unscored')}
    } for profile in ('A', 'B')}
    write_json(STATE / 'summary.json', summary)
    out = STATE / 'comparison.csv'
    with out.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print('Task\tA\tB')
    for name in manifest['tasks']:
        pair = {r['profile']: r['status'] for r in rows if r['task'] == name}
        print(f"{name}\t{pair['A']}\t{pair['B']}")
    for profile in ('A', 'B'):
        group = [r for r in rows if r['profile'] == profile]
        passed = sum(r['status'] == 'pass' for r in group)
        invalid = sum(r['status'] in {'error', 'missing', 'unscored'} for r in group)
        print(f'{profile}: {passed}/{len(group)} planned tasks passed; {invalid} errors/missing/unscored.')
    print(f'CSV: {out}')
    print('Missing metrics stay blank, not zero. Cost is an estimate from Pier, not an invoice.')
    print('Inspect errors before comparing. Agent timeouts remain visible as failures.')
    print('This subset is a pilot, not a reliability estimate or official benchmark score.')


def login(args) -> None:
    home = Path(args.login_home).expanduser().absolute()
    home.mkdir(parents=True, exist_ok=True, mode=0o700)
    home.chmod(0o700)
    auth = home / 'auth.json'
    if home.resolve() == (Path.home() / '.codex').resolve():
        raise ValueError('Use the dedicated benchmark home')
    with auth_lock(auth):
        env = os.environ.copy()
        env['CODEX_HOME'] = str(home)
        subprocess.run(['codex', '-c', 'cli_auth_credentials_store="file"',
                        'login', '--device-auth'], env=env, check=True)
        auth.chmod(0o600)
        validate_auth(auth)


def doctor(_args) -> None:
    manifest = json.loads((STATE / 'manifest.json').read_text())
    verify_frozen(manifest)
    validate_auth(Path(manifest['auth_json']))
    env = runtime_env(manifest)
    capture('docker', 'info', env=env)
    capture('docker', 'compose', 'version', env=env)
    for image in manifest['images'].values():
        inspection = json.loads(capture('docker', 'image', 'inspect', image['digest'], env=env))[0]
        if inspection['Id'] != image['id']:
            raise ValueError('Task image content changed')
    print('Frozen inputs, private ChatGPT login, Docker, Compose and task images verified.')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-dir', default='state-chatgpt', help='Separate immutable state per experiment')
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('login', help='Authenticate only the private benchmark home')
    p.add_argument('--login-home', default=str(DEFAULT_HOME))
    p.set_defaults(func=login)
    commands.add_parser('doctor', help='Verify frozen inputs and private login').set_defaults(func=doctor)
    p = commands.add_parser('prepare', help='Freeze instructions, skills, model, CLI and task selection')
    p.add_argument('--agents', required=True)
    p.add_argument('--skills', required=True)
    p.add_argument('--model', default='gpt-6.1-sol', help='Exact model ID available through the benchmark login')
    p.add_argument('--auth-json', default=str(DEFAULT_HOME / 'auth.json'))
    p.add_argument('--dataset', help='Existing clean DeepSWE checkout to copy')
    p.add_argument('--language', default='typescript')
    p.add_argument('--platform', default='linux/amd64')
    p.add_argument('--reasoning', default='high')
    p.add_argument('--codex-version', help='Defaults to the version from local codex --version')
    p.add_argument('--tasks', type=int, default=1)
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--timeout', type=int, default=1800, help='Agent seconds per task; both profiles')
    p.set_defaults(func=prepare)
    p = commands.add_parser('run', help='Run one profile; does not overwrite or resume jobs')
    p.add_argument('profile', choices=['A', 'B'])
    p.set_defaults(func=run_profile)
    commands.add_parser('report', help='Export paired CSV from Pier results').set_defaults(func=report)
    args = parser.parse_args()
    global STATE
    STATE = Path(args.state_dir).expanduser().absolute()
    if not STATE.parent.is_dir():
        raise ValueError('State parent directory must exist')
    try:
        args.func(args)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'Error: {exc}\n')


if __name__ == '__main__':
    main()
