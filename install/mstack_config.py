"""Merge only owned defaults while preserving shared application settings."""
from __future__ import annotations
import json
from pathlib import Path
import tomlkit
from mstack_fs import InstallError, atomic_file, signature

OWNED_KEYS = {
    'codex/config.toml': ('model', 'model_reasoning_effort'),
    'pi/settings.json': ('defaultProvider', 'defaultModel', 'defaultThinkingLevel'),
}

def config_document(path, method):
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise InstallError(f'Configuration must be a regular file: {path}')
    try:
        content = path.read_text() if path.exists() else ''
        doc = tomlkit.parse(content) if method == 'toml-keys' else json.loads(content or '{}')
        if not isinstance(doc, dict):
            raise ValueError()
        return doc, content
    except (ValueError, tomlkit.exceptions.TOMLKitError):
        # Parser messages can contain private configuration values.
        raise InstallError(f'Invalid configuration: {path}') from None


def config_signature(path, action):
    doc, _ = config_document(path, action['method'])
    if any(key in doc and not isinstance(doc[key], str) for key in action['keys']):
        raise InstallError(f'Owned preferences must be strings: {path}')
    return {'kind': 'configuration', 'values': {
        key: {'present': key in doc, **({'value': doc[key]} if key in doc else {})}
        for key in action['keys']}}


def merge_config(action, values, remove_empty=False):
    path = Path(action['target'])
    original = signature(path)
    doc, _ = config_document(path, action['method'])
    for key, item in values.items():
        if item['present']:
            doc[key] = item['value']
        elif key in doc:
            del doc[key]
    text = tomlkit.dumps(doc) if action['method'] == 'toml-keys' else json.dumps(doc, indent=2) + '\n'
    if signature(path) != original:
        raise InstallError(f'Configuration changed during the operation: {path}')
    if remove_empty and not doc and (action['method'] == 'json-keys' or not text.strip()):
        path.unlink(missing_ok=True)
    else:
        mode = original.get('mode', 0o600)
        atomic_file(path, text.encode(), mode)



def owned_defaults(data, keys, method):
    try:
        content = data.decode()
        doc = tomlkit.parse(content) if method == 'toml-keys' else json.loads(content)
        if set(doc) != set(keys) or any(not isinstance(doc[k], str) for k in keys):
            raise ValueError()
        return {k: {'present': True, 'value': str(doc[k])} for k in keys}
    except (ValueError, tomlkit.exceptions.TOMLKitError):
        raise InstallError('Owned defaults must contain only the declared string keys') from None
