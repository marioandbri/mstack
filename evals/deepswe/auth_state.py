"""Private OAuth storage and single-run locking, outside evaluation artifacts."""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import stat
from contextlib import contextmanager
from pathlib import Path

DEFAULT_HOME = Path.home() / '.local/share/mstack-evals/codex'


def validate_auth(path: Path) -> None:
    if path.is_symlink() or not path.is_file():
        raise ValueError('Benchmark auth must be a regular, private file')
    if path.resolve() == (Path.home() / '.codex/auth.json').resolve():
        raise ValueError('Use a separate benchmark login, not the active Codex login')
    if stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise ValueError('Benchmark auth file must have permissions 0600')
    data = json.loads(path.read_text())
    tokens = data.get('tokens') or {}
    if data.get('auth_mode') != 'chatgpt' or not tokens.get('access_token') or not tokens.get('refresh_token'):
        raise ValueError('A ChatGPT OAuth login with refresh token is required')


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def persist_refresh(source: Path, destination: Path, expected_hash: str) -> None:
    validate_auth(source)
    if digest(destination) != expected_hash:
        raise ValueError('Benchmark login changed during the trial; refusing to overwrite it')
    # source is a sibling private temporary file, so replacement is atomic.
    os.chmod(source, 0o600)
    with source.open('rb') as handle:
        os.fsync(handle.fileno())
    os.replace(source, destination)


@contextmanager
def auth_lock(path: Path):
    lock_path = path.parent / '.benchmark.lock'
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Another benchmark or login uses these credentials') from None
        yield
    finally:
        os.close(fd)
