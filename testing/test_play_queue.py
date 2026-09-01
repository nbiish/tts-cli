"""Concurrent plays wait on one speaker lock; they never overlay."""

from __future__ import annotations

import os
import subprocess
import threading
import time
from multiprocessing import Process
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tts_cli.cli import play_audio
from tts_cli.core.play_queue import exclusive_speaker


@pytest.fixture(autouse=True)
def _isolate_play_lock(tmp_path, monkeypatch):
    monkeypatch.setenv("TTS_CLI_PLAY_LOCK", str(tmp_path / "play.lock"))


def _mp_hold_lock(lock_path: str, ready_path: str, hold: float) -> None:
    os.environ["TTS_CLI_PLAY_LOCK"] = lock_path
    from tts_cli.core.play_queue import exclusive_speaker as hold_speaker

    with hold_speaker():
        Path(ready_path).write_text("1", encoding="utf-8")
        time.sleep(hold)


def test_two_threaded_plays_run_sequentially(monkeypatch):
    monkeypatch.setattr("tts_cli.cli.platform.system", lambda: "Darwin")
    order: list[str] = []

    def fake_run(*_a, **_k):
        order.append("start")
        time.sleep(0.12)
        order.append("end")
        return MagicMock()

    monkeypatch.setattr(subprocess, "run", fake_run)
    barrier = threading.Barrier(2)

    def worker(name: str) -> None:
        barrier.wait()
        play_audio(f"/tmp/{name}.wav")

    threads = [
        threading.Thread(target=worker, args=("a",)),
        threading.Thread(target=worker, args=("b",)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert order == ["start", "end", "start", "end"]


def test_second_process_waits_for_speaker(tmp_path):
    lock_path = str(tmp_path / "play.lock")
    ready_path = str(tmp_path / "ready")
    os.environ["TTS_CLI_PLAY_LOCK"] = lock_path
    holder = Process(target=_mp_hold_lock, args=(lock_path, ready_path, 0.25))
    holder.start()
    deadline = time.time() + 3
    while not os.path.exists(ready_path):
        if time.time() > deadline:
            holder.terminate()
            pytest.fail("lock holder never became ready")
        time.sleep(0.01)

    t0 = time.perf_counter()
    with exclusive_speaker():
        waited = time.perf_counter() - t0
    holder.join(timeout=3)
    assert waited >= 0.15
    assert holder.exitcode == 0
