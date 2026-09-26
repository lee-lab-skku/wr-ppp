"""Shared editor conflict detection, independent of either adapter."""
from contextlib import contextmanager
import hashlib
import os
import socket
from pathlib import Path
import threading


class ConflictError(ValueError):
    """A stale writer must reload rather than overwrite newer work."""


def fingerprint(path):
    path = Path(path)
    if path.is_symlink():
        raise ConflictError('An editor destination was replaced with a symbolic link')
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


_locks = {}
_locks_guard = threading.Lock()


@contextmanager
def file_lock(path):
    """Serialize GUI/browser writes and reserve the destination across processes.

    The short-lived directory lock is never stolen. Interrupted writes require
    inspection of the lock before reopening, rather than risking stale updates.
    """
    path = Path(path).absolute()
    key = str(path.parent.resolve() / path.name)
    with _locks_guard:
        lock = _locks.setdefault(key, threading.RLock())
    with lock:
        directory = path.parent / ('.' + path.name + '.editor-lock')
        try:
            directory.mkdir()
        except FileExistsError as error:
            raise ConflictError('Another editor owns the destination lock: ' + str(directory)) from error
        owner = directory / 'owner'
        try:
            owner.write_text(f'{socket.gethostname()}\t{os.getpid()}\n', encoding='utf-8')
            yield
        finally:
            owner.unlink(missing_ok=True)
            directory.rmdir()
