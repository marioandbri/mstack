"""Private state and atomic filesystem operations."""
from __future__ import annotations
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
import uuid

class InstallError(Exception):
    pass


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    try:
        return json.loads(path.read_bytes())
    except (ValueError, OSError):
        raise InstallError(f'Cannot read JSON: {path}') from None


def relative(value):
    if not isinstance(value, str) or not value or '\\' in value or '\n' in value:
        raise InstallError('Invalid managed path')
    path = PurePosixPath(value)
    if path.is_absolute() or any(p in ('', '.', '..') for p in value.split('/')):
        raise InstallError('Managed paths must stay inside their declared root')
    return value


def signature(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return {'kind': 'absent'}
    if stat.S_ISLNK(info.st_mode):
        return {'kind': 'link', 'target': os.readlink(path)}
    if stat.S_ISREG(info.st_mode):
        return {'kind': 'file', 'sha256': digest(path.read_bytes()), 'mode': stat.S_IMODE(info.st_mode)}
    if stat.S_ISDIR(info.st_mode):
        children = {p.name: signature(p) for p in sorted(path.iterdir())}
        return {'kind': 'directory', 'sha256': digest(encoded(children)), 'mode': stat.S_IMODE(info.st_mode)}
    raise InstallError(f'Unsupported managed target: {path}')


def resolved_signature(path):
    try:
        return signature(path.resolve(strict=True))
    except (FileNotFoundError, RuntimeError):
        return {'kind': 'absent'}


def atomic_file(path, data, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.mstack-', dir=path.parent)
    temporary = Path(name)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, 'wb') as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_link(path, target):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / ('.mstack-link-' + uuid.uuid4().hex)
    try:
        temporary.symlink_to(target)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def private_directory(path):
    if path.is_symlink():
        raise InstallError(f'Private state cannot be a symlink: {path}')
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.chmod(0o700)


@contextlib.contextmanager
def lock(state):
    private_directory(state)
    path = state / '.lock'
    if path.is_symlink():
        raise InstallError('Installation lock cannot be a symlink')
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        os.fchmod(fd, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise InstallError('Another mstack operation is running') from None
        yield
    finally:
        os.close(fd)


def copy_backup(path, backup):
    backup.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.is_symlink():
        backup.symlink_to(os.readlink(path))
    elif path.is_dir():
        shutil.copytree(path, backup, symlinks=True)
    elif path.is_file():
        shutil.copy2(path, backup)
        backup.chmod(0o600)
