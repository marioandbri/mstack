"""Build and validate readonly managed content from a Git commit."""
from __future__ import annotations
import importlib.metadata
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from mstack_config import OWNED_KEYS
from mstack_fs import InstallError, digest, encoded, private_directory, read_json, relative

ROOT_IDS = ('agents', 'claude', 'codex', 'pi')

def git(repo, *args):
    try:
        return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        raise InstallError('Cannot read the requested Git source') from None


def source(repo, ref):
    commit = git(repo, 'rev-parse', '--verify', '--end-of-options', ref + '^{commit}').decode().strip()
    if not re.fullmatch(r'[0-9a-f]{40,64}', commit):
        raise InstallError('Invalid source commit')

    def blob(path):
        return git(repo, 'show', commit + ':' + relative(path))

    try:
        manifest = json.loads(blob('mstack.json'))
        inventory_path = relative(manifest['skillsManifest'])
        inventory = json.loads(blob(inventory_path))
        if manifest['schemaVersion'] != 1 or set(inventory['targets']) != set(ROOT_IDS):
            raise ValueError()
        names = [item['name'] for item in inventory['skills']]
        if not names or len(set(names)) != len(names) or any(not re.fullmatch(r'[a-z0-9-]+', n) for n in names):
            raise ValueError()
        entries = manifest['managed']
        targets = [relative(e['target']) for e in entries]
        if len(set(targets)) != len(targets):
            raise ValueError()
        for entry in entries:
            root, _, tail = entry['target'].partition('/')
            if root not in ROOT_IDS or not tail:
                raise ValueError()
            method = entry['method']
            if method == 'link':
                if relative(entry['sourceTarget']) not in targets:
                    raise ValueError()
            elif method in ('copy', 'template', 'toml-keys', 'json-keys'):
                relative(entry['source'])
                if method.endswith('-keys') and tuple(entry['keys']) != OWNED_KEYS.get(entry['target']):
                    raise ValueError()
            else:
                raise ValueError()
    except (KeyError, TypeError, ValueError):
        raise InstallError('Invalid mstack installation manifest') from None
    if (sys.version.split()[0] != manifest['runtime']['python'] or
            importlib.metadata.version('tomlkit') != manifest['runtime']['tomlkit']):
        raise InstallError('Installer runtime differs from the pinned manifest')
    paths = ['mstack.json', inventory_path]
    paths.extend(e['source'] for e in entries if 'source' in e)
    paths.extend('skills/' + n for n in names)
    files = {}
    for record in git(repo, 'ls-tree', '-r', '-z', commit, '--', *paths).split(b'\0'):
        if not record:
            continue
        header, path_bytes = record.split(b'\t', 1)
        mode, kind, object_id = header.decode().split()
        path = relative(path_bytes.decode())
        if kind != 'blob' or mode not in ('100644', '100755'):
            raise InstallError(f'Managed source must contain regular files: {path}')
        files[path] = {'data': git(repo, 'cat-file', 'blob', object_id), 'executable': mode == '100755'}
    required = ['mstack.json', inventory_path] + [e['source'] for e in entries if 'source' in e]
    required += ['skills/' + n + '/SKILL.md' for n in names]
    if any(p not in files for p in required):
        raise InstallError('The commit is missing required managed content')
    metadata = {'commit': commit, 'manifest': manifest, 'inventory': inventory,
                'files': {p: {'sha256': digest(f['data']), 'executable': f['executable']} for p, f in files.items()}}
    return metadata, files


def bundle_check(version, expected=None):
    if version.is_symlink() or not version.is_dir():
        raise InstallError('Snapshot must be a regular directory')
    if any(stat.S_IMODE(p.stat().st_mode) != 0o555 for p in [version, *(p for p in version.rglob('*') if p.is_dir())]):
        raise InstallError('Snapshot directory permissions drift detected')
    metadata_path = version / '.mstack-bundle.json'
    if metadata_path.is_symlink() or stat.S_IMODE(metadata_path.stat().st_mode) != 0o444:
        raise InstallError('Snapshot metadata permissions drift detected')
    metadata = read_json(metadata_path)
    if expected and digest(metadata_path.read_bytes()) != expected:
        raise InstallError('Snapshot metadata drift detected')
    actual_paths = {p.relative_to(version).as_posix() for p in version.rglob('*') if p.is_file() or p.is_symlink()}
    if actual_paths != set(metadata['files']) | {'.mstack-bundle.json'}:
        raise InstallError('Snapshot file inventory drift detected')
    for relative_path, item in metadata['files'].items():
        path = version / relative(relative_path)
        expected_mode = 0o555 if item['executable'] else 0o444
        if (path.is_symlink() or not path.is_file() or digest(path.read_bytes()) != item['sha256']
                or stat.S_IMODE(path.stat().st_mode) != expected_mode):
            raise InstallError(f'Snapshot content drift: {relative_path}')
    return metadata


def install_bundle(state, metadata, files):
    versions = state / 'versions'
    private_directory(versions)
    destination = versions / metadata['commit']
    expected = digest(encoded(metadata))
    if destination.exists():
        bundle_check(destination, expected)
        return expected
    temporary = Path(tempfile.mkdtemp(prefix='.snapshot-', dir=versions))
    try:
        for name, item in files.items():
            path = temporary / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(item['data'])
            path.chmod(0o555 if item['executable'] else 0o444)
        (temporary / '.mstack-bundle.json').write_bytes(encoded(metadata))
        (temporary / '.mstack-bundle.json').chmod(0o444)
        for directory in sorted((p for p in temporary.rglob('*') if p.is_dir()), reverse=True):
            directory.chmod(0o555)
        temporary.chmod(0o555)
        os.replace(temporary, destination)
        return expected
    finally:
        if temporary.exists():
            for p in temporary.rglob('*'):
                if p.is_dir():
                    p.chmod(0o700)
            temporary.chmod(0o700)
            shutil.rmtree(temporary)
