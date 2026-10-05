"""Install commit snapshots, merge owned settings, and undo installations safely."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import re
import shutil
import uuid
from mstack_config import config_signature, merge_config, owned_defaults
from mstack_fs import InstallError, atomic_file, atomic_link, copy_backup, digest, encoded, lock, private_directory, read_json, relative, resolved_signature, signature
from mstack_source import ROOT_IDS, bundle_check, install_bundle, source

ROOT = Path(__file__).resolve().parent.parent

def observe(action):
    path = Path(action['target'])
    if action['method'] in ('toml-keys', 'json-keys'):
        return config_signature(path, action)
    return signature(path)


def target_path(roots, spec):
    root, _, tail = relative(spec).partition('/')
    if root not in roots or not tail:
        raise InstallError('Invalid target root')
    result = Path(roots[root]) / tail
    parent = result.parent
    while parent != Path(roots[root]):
        if parent.is_symlink():
            raise InstallError(f'Managed parent cannot be a symlink: {parent}')
        parent = parent.parent
    return result


def actions_for(metadata, files, roots, state):
    actions = []
    for entry in metadata['manifest']['managed']:
        item = dict(entry, target=str(target_path(roots, entry['target'])))
        method = item['method']
        if method == 'link':
            item['link'] = str(target_path(roots, item['sourceTarget']))
            item['after'] = {'kind': 'link', 'target': item['link']}
        elif method in ('copy', 'template'):
            data = files[item['source']]['data']
            if method == 'template':
                data = data.replace(b'{{globalAgentsPath}}', str(target_path(roots, 'agents/AGENTS.md')).encode())
                if b'{{' in data:
                    raise InstallError('Unresolved instruction template variable')
            item['data'] = data
            before = signature(Path(item['target']))
            mode = before.get('mode', 0o644) if before.get('sha256') == digest(data) else 0o644
            item['after'] = {'kind': 'file', 'sha256': digest(data), 'mode': mode}
        else:
            item['after'] = {'kind': 'configuration', 'values': owned_defaults(files[item['source']]['data'], item['keys'], method)}
        actions.append(item)
    for skill in metadata['inventory']['skills']:
        for root_id in metadata['inventory']['targets']:
            target = str(target_path(roots, root_id + '/skills/' + skill['name']))
            link = str(state / 'active/skills' / skill['name'])
            actions.append({'target': target, 'method': 'skill-link', 'link': link,
                            'after': {'kind': 'link', 'target': link}})
    for item in actions:
        item['before'] = observe(item)
        item['changed'] = item['before'] != item['after']
        path = Path(item['target'])
        item['file_existed_before'] = path.is_file()
        if item['method'] == 'skill-link' and path.is_symlink() and not os.readlink(path).startswith(str(state / 'active/')):
            item['legacy_source_signature'] = resolved_signature(path)
    if len({a['target'] for a in actions}) != len(actions):
        raise InstallError('Configured directories cause overlapping managed targets')
    return actions


def checked_record(state, path):
    record = read_json(path)
    generation = record.get('generation', '')
    if not re.fullmatch(r'[0-9a-f]{32}', generation):
        raise InstallError('Invalid installation generation')
    archive = state / 'receipts' / (generation + '.json')
    if not archive.is_file() or path.read_bytes() != archive.read_bytes():
        raise InstallError('Installation record drift detected')
    return record


def current_receipt(state):
    path = state / 'current.json'
    return checked_record(state, path) if path.exists() else None


def verify_receipt(state, receipt):
    if signature(state / 'active') != receipt['active']:
        raise InstallError('Active snapshot pointer drift detected')
    bundle_check(state / 'versions' / receipt['commit'], receipt['bundle_sha256'])
    for action in receipt['actions']:
        if observe(action) != action['after']:
            raise InstallError(f'Local managed-content drift: {action["target"]}')
    # Keep the upstream ownership guard without changing external skill packages.
    lock_path = Path(receipt['roots']['agents']) / '.skill-lock.json'
    if lock_path.is_file():
        upstream = read_json(lock_path).get('skills', {})
        owned = receipt['skill_names']
        if any(name in upstream for name in owned):
            raise InstallError('A managed skill still has upstream installer ownership')
    duplicate_guard(receipt)
    return receipt


def duplicate_guard(receipt):
    owned = set(receipt['skill_names'])
    for root in receipt['roots'].values():
        base = Path(root) / 'skills'
        seen = set()
        def visit(directory):
            try:
                real = directory.resolve(strict=True)
            except (FileNotFoundError, RuntimeError):
                return
            if not real.is_dir():
                return
            if (directory / 'SKILL.md').is_file() and directory.name in owned:
                if directory != base / directory.name:
                    raise InstallError(f'Duplicate managed skill: {directory}')
            if real in seen:
                return
            seen.add(real)
            for child in directory.iterdir():
                if child.is_dir():
                    visit(child)
        if base.is_dir():
            visit(base)


def replace_target(action):
    path = Path(action['target'])
    if observe(action) != action['before']:
        raise InstallError(f'Target changed during installation: {path}')
    if action['method'].endswith('-keys'):
        merge_config(action, action['after']['values'])
        return
    displaced = None
    if path.is_dir() and not path.is_symlink():
        displaced = path.parent / ('.mstack-displaced-' + uuid.uuid4().hex)
        os.replace(path, displaced)
    try:
        if action['after']['kind'] == 'link':
            atomic_link(path, action['link'])
        else:
            atomic_file(path, action['data'], action['after']['mode'])
    except BaseException:
        if displaced is not None:
            os.replace(displaced, path)
        raise
    else:
        if displaced is not None:
            shutil.rmtree(displaced)


def restore_action(action):
    if not action['changed']:
        return
    path = Path(action['target'])
    before = action['before']
    if action['method'].endswith('-keys'):
        merge_config(action, before['values'], not action['file_existed_before'])
        return
    if before['kind'] == 'absent':
        path.unlink(missing_ok=True)
    elif before['kind'] == 'link':
        atomic_link(path, before['target'])
    elif before['kind'] == 'file':
        atomic_file(path, Path(action['backup']).read_bytes(), before['mode'])
    elif before['kind'] == 'directory':
        if path.is_symlink() or path.is_file():
            path.unlink()
        shutil.copytree(action['backup'], path, symlinks=True)


def undo(state, journal, allow_partial=False, dry_run=False):
    # Validate everything before the first rollback mutation.
    for action in journal['actions']:
        actual = observe(action)
        allowed = [action['after'], action['before']] if allow_partial else [action['after']]
        if actual not in allowed:
            raise InstallError(f'Rollback would overwrite local changes: {action["target"]}')
        if action.get('backup') and signature(Path(action['backup'])) != action['backup_signature']:
            raise InstallError('An installation backup changed or is missing')
        if action.get('legacy_source_signature'):
            target = Path(action['target']).parent / action['before']['target']
            if resolved_signature(target) != action['legacy_source_signature']:
                raise InstallError('The original mutable skill source changed; rollback stopped')
    if signature(state / 'active') not in [journal['active_before'], journal['active']]:
        raise InstallError('Active snapshot pointer changed; rollback stopped')
    previous_ref = journal.get('previous')
    previous = None
    if previous_ref:
        previous_path = state / 'receipts' / (previous_ref['generation'] + '.json')
        if digest(previous_path.read_bytes()) != previous_ref['sha256']:
            raise InstallError('Previous installation record drift detected')
        previous = read_json(previous_path)
    if previous:
        bundle_check(state / 'versions' / previous['commit'], previous['bundle_sha256'])
    if dry_run:
        return
    pointer = journal['active_before']
    if pointer['kind'] == 'absent':
        (state / 'active').unlink(missing_ok=True)
    else:
        atomic_link(state / 'active', pointer['target'])
    for action in reversed(journal['actions']):
        if allow_partial and observe(action) == action['before']:
            continue
        restore_action(action)
    if previous:
        atomic_file(state / 'current.json', encoded(previous))
        verify_receipt(state, previous)
    else:
        (state / 'current.json').unlink(missing_ok=True)
    (state / 'journal.json').unlink(missing_ok=True)


def setup(repo, ref, roots, state, apply=False):
    if (state / 'journal.json').exists():
        raise InstallError('An unfinished operation exists; use recover --apply')
    metadata, files = source(repo, ref)
    for label in ('agents', 'codex', 'pi'):
        if (Path(roots[label]) / 'AGENTS.override.md').exists():
            raise InstallError(f'Instruction override shadows the managed file: {label}')
    previous = current_receipt(state)
    if previous:
        if previous['roots'] != roots:
            raise InstallError('Configured directories differ from the active installation')
        verify_receipt(state, previous)
    actions = actions_for(metadata, files, roots, state)
    changes = sum(a['changed'] for a in actions)
    pointer = {'kind': 'link', 'target': str(state / 'versions' / metadata['commit'])}
    pointer_changed = signature(state / 'active') != pointer
    print(f'MODE {"apply" if apply else "dry-run"}; commit={metadata["commit"]}; skills={len(metadata["inventory"]["skills"])}; changes={changes}')
    if not apply:
        for item in actions:
            if item['changed']:
                print(f'PLAN {item["method"]}: {item["target"]}')
        print('RESULT dry-run; no files changed')
        return None
    with lock(state):
        # Recheck after acquiring the lock, before allocating or modifying targets.
        if current_receipt(state) != previous or (state / 'journal.json').exists():
            raise InstallError('Installation state changed; run setup again')
        if previous:
            verify_receipt(state, previous)
        if previous and not changes and not pointer_changed:
            print('RESULT unchanged; installation is already verified')
            return previous
        bundle_sha = install_bundle(state, metadata, files)
        private_directory(state / 'backups')
        generation = uuid.uuid4().hex
        backup_root = state / 'backups' / generation
        private_directory(backup_root)
        serializable = []
        for index, action in enumerate(actions):
            item = {k: v for k, v in action.items() if k != 'data'}
            if action['changed'] and signature(Path(action['target']))['kind'] != 'absent':
                backup = backup_root / str(index)
                copy_backup(Path(action['target']), backup)
                item['backup'] = str(backup)
                item['backup_signature'] = signature(backup)
            serializable.append(item)
        receipt = {'generation': generation, 'commit': metadata['commit'], 'bundle_sha256': bundle_sha,
                   'roots': roots, 'skill_names': [s['name'] for s in metadata['inventory']['skills']],
                   'active': pointer, 'actions': serializable,
                   'previous': {'generation': previous['generation'], 'sha256': digest(encoded(previous))} if previous else None,
                   'active_before': signature(state / 'active')}
        private_directory(state / 'receipts')
        atomic_file(state / 'receipts' / (generation + '.json'), encoded(receipt))
        atomic_file(state / 'journal.json', encoded(receipt))
        try:
            if receipt['active_before']['kind'] == 'absent':
                atomic_link(state / 'active', pointer['target'])
            for action in actions:
                if action['changed']:
                    replace_target(action)
            atomic_link(state / 'active', pointer['target'])
            verify_receipt(state, receipt)
            private_directory(state / 'receipts')
            atomic_file(state / 'receipts' / (generation + '.json'), encoded(receipt))
            atomic_file(state / 'current.json', encoded(receipt))
            (state / 'journal.json').unlink()
        except BaseException:
            try:
                undo(state, receipt, allow_partial=True)
            except Exception:
                raise InstallError('Installation stopped; recover --apply must inspect the retained journal') from None
            raise
        print(f'RESULT installed; skills={len(receipt["skill_names"])}; targets={len(actions)}; backups={backup_root}')
        return receipt


def resolve_locations(args):
    explicit_home = args.home is not None
    home = Path(args.home or Path.home()).expanduser().resolve(strict=True)
    local = {}
    local_path = Path(args.local_config) if args.local_config else ROOT / 'mstack.local.json'
    if args.local_config or (not explicit_home and local_path.exists()):
        local = read_json(local_path)
        if set(local) - {'directories', 'stateDir'} or set(local.get('directories', {})) - set(ROOT_IDS):
            raise InstallError('Local configuration supports only directory overrides and stateDir')
    defaults = {'agents': home / '.agents', 'claude': home / '.claude', 'codex': home / '.codex', 'pi': home / '.pi/agent'}
    env_names = {'codex': 'CODEX_HOME', 'claude': 'CLAUDE_CONFIG_DIR', 'pi': 'PI_CODING_AGENT_DIR'}
    roots = {}
    for label in ROOT_IDS:
        explicit = getattr(args, label + '_dir')
        env_value = os.environ.get(env_names.get(label, '')) if not explicit_home else None
        value = explicit or local.get('directories', {}).get(label) or env_value or defaults[label]
        roots[label] = str(Path(value).expanduser().resolve())
    data_home = os.environ.get('XDG_DATA_HOME') if not explicit_home else None
    state = Path(args.state_dir or local.get('stateDir') or (Path(data_home) if data_home else home / '.local/share') / 'mstack').expanduser().absolute()
    if state.is_symlink():
        raise InstallError('Installation state cannot be a symlink')
    return roots, state.resolve()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for command in ('setup', 'snapshot', 'verify', 'status', 'rollback', 'recover'):
        p = commands.add_parser(command)
        p.add_argument('--home')
        p.add_argument('--repo', default=str(ROOT))
        p.add_argument('--ref', default='HEAD')
        p.add_argument('--state-dir')
        p.add_argument('--local-config')
        for label in ROOT_IDS:
            p.add_argument('--' + label + '-dir')
        p.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    try:
        roots, state = resolve_locations(args)
        if args.command == 'setup':
            setup(Path(args.repo).resolve(strict=True), args.ref, roots, state, args.apply)
        elif args.command == 'snapshot':
            if (state / 'journal.json').exists():
                raise InstallError('An unfinished operation exists; use recover --apply')
            metadata, files = source(Path(args.repo).resolve(strict=True), args.ref)
            destination = state / 'versions' / metadata['commit']
            if args.apply:
                with lock(state):
                    install_bundle(state, metadata, files)
                print(f'SNAPSHOT {destination}; active installation unchanged')
            else:
                print(f'PLAN snapshot: {destination}; dry-run, no files changed')
        elif args.command in ('verify', 'status'):
            receipt = current_receipt(state)
            if not receipt:
                raise InstallError('No managed installation exists; setup defaults to dry-run')
            if receipt['roots'] != roots:
                raise InstallError('Configured directories differ from the active installation')
            if (state / 'journal.json').exists():
                raise InstallError('An unfinished operation exists; use recover --apply')
            verify_receipt(state, receipt)
            print(f'PASS commit={receipt["commit"]}; skills={len(receipt["skill_names"])}; targets={len(receipt["actions"])}; owned content and configuration verified')
        else:
            journal = checked_record(state, state / 'journal.json') if args.command == 'recover' else current_receipt(state)
            if not journal:
                raise InstallError('There is no operation to undo')
            if journal['roots'] != roots:
                raise InstallError('Configured directories differ from the operation being restored')
            if not args.apply:
                if args.command == 'rollback':
                    verify_receipt(state, journal)
                undo(state, journal, allow_partial=args.command == 'recover', dry_run=True)
                print(f'PLAN {args.command}: generation={journal["generation"]}; targets={len(journal["actions"])}')
                print('RESULT dry-run; no files changed')
            else:
                with lock(state):
                    if args.command == 'rollback':
                        verify_receipt(state, journal)
                    undo(state, journal, allow_partial=args.command == 'recover')
                print('RESULT previous owned state restored; unowned configuration preserved')
    except (InstallError, OSError) as exc:
        parser.exit(1, f'ERROR {exc}\n')


if __name__ == '__main__':
    main()
