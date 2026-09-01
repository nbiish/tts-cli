"""Per-user speaker lock so concurrent cli-tts plays never overlay.

Every process that reaches `play_audio` (detached agent child, operator CLI,
`--output` in-process, future GUI) takes the same exclusive lock for the
duration of the OS player. Generation is not serialized — only the speaker.

Cross-process: advisory flock on `~/.tts-cli/play.lock` (override with
`TTS_CLI_PLAY_LOCK`). Same-process: a threading lock, because flock is
per-process and would not serialize two threads.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger("tts_cli.play_queue")

PLAY_LOCK_ENV = "TTS_CLI_PLAY_LOCK"
_PROCESS_SPEAKER = threading.Lock()


def play_lock_path() -> Path:
    override = os.environ.get(PLAY_LOCK_ENV)
    if override:
        return Path(override)
    return Path.home() / ".tts-cli" / "play.lock"


def _ensure_lock_byte(fd: int) -> None:
    """msvcrt.locking requires at least one byte; flock does not care."""
    if os.fstat(fd).st_size == 0:
        os.write(fd, b"\0")
        os.lseek(fd, 0, os.SEEK_SET)


def _lock_exclusive(fd: int) -> None:
    if os.name == "nt":
        import msvcrt

        _ensure_lock_byte(fd)
        while True:
            try:
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                return
            except OSError:
                time.sleep(0.05)
        return

    import fcntl

    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        logger.debug("speaker busy; waiting for play.lock")
        fcntl.flock(fd, fcntl.LOCK_EX)


def _unlock(fd: int) -> None:
    if os.name == "nt":
        import msvcrt

        os.lseek(fd, 0, os.SEEK_SET)
        try:
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        return

    import fcntl

    fcntl.flock(fd, fcntl.LOCK_UN)


@contextmanager
def exclusive_speaker() -> Iterator[None]:
    """Hold the speaker until the with-block exits (player finished or failed)."""
    path = play_lock_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with _PROCESS_SPEAKER:
        fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            _lock_exclusive(fd)
            try:
                yield
            finally:
                _unlock(fd)
        finally:
            os.close(fd)
