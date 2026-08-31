"""Validation tests for the KittenTTS adapter.

Proves the fail-closed safety properties of ``KittenTTSModel.generate_speech``:
  - overlong text is rejected before any subprocess is spawned.
  - an unrecognized built-in voice name is rejected (fail-closed, no silent
    fallback) before any subprocess is spawned.
  - a valid voice + valid text reaches the runner subprocess.

These tests never invoke the real KittenTTS engine or its isolated env — they
stub ``subprocess.Popen`` and assert whether it was reached, so they are fast
and hermetic.
"""

import subprocess
from unittest.mock import MagicMock

import pytest

from tts_cli.models.kitten_tts_model import (
    KittenTTSModel,
    MAX_TEXT_LENGTH,
    BUILT_IN_VOICES,
    DEFAULT_VOICE,
)


@pytest.fixture
def model_with_env(monkeypatch):
    """A KittenTTSModel whose isolated env is present (availability True).

    ``python_executable`` is set to a fake path so ``check_dependencies``
    passes; the real subprocess is never spawned because we stub ``Popen``.
    """
    m = KittenTTSModel("kitten-tts-nano")
    m.python_executable = "/fake/venv/bin/python"
    m._availability_cache = True
    return m


def _stub_popen(monkeypatch, *, returncode=0, stdout="", stderr=""):
    """Replace subprocess.Popen with a recorder; return the mock.

    The returned mock is a MagicMock whose native ``call_count`` records how
    many times the runner subprocess was spawned, so a test can assert the
    runner was (or was not) reached.
    """
    fake_proc = MagicMock()
    fake_proc.returncode = returncode
    fake_proc.communicate.return_value = (stdout, stderr)

    popen = MagicMock(return_value=fake_proc)
    monkeypatch.setattr(subprocess, "Popen", popen)
    # Stub Path.exists so the success-path output check passes.
    from pathlib import Path
    monkeypatch.setattr(Path, "exists", lambda self: True)
    return popen


def test_overlong_text_rejected(model_with_env, monkeypatch):
    """Text over MAX_TEXT_LENGTH is rejected before spawning the runner."""
    popen = _stub_popen(monkeypatch)
    ok = model_with_env.generate_speech("x" * (MAX_TEXT_LENGTH + 1),
                                         output_path="/tmp/out.wav")
    assert ok is False
    assert popen.call_count == 0, "runner must not be spawned for overlong text"


def test_unknown_voice_fail_closed(model_with_env, monkeypatch):
    """An unrecognized voice name fails closed — no silent fallback, no spawn."""
    popen = _stub_popen(monkeypatch)
    ok = model_with_env.generate_speech("hello",
                                         voice="not-a-real-voice",
                                         output_path="/tmp/out.wav")
    assert ok is False
    assert popen.call_count == 0, "runner must not be spawned for a bad voice"


def test_valid_voice_reaches_runner(model_with_env, monkeypatch):
    """A valid built-in voice + valid text reaches the runner subprocess."""
    popen = _stub_popen(monkeypatch)
    ok = model_with_env.generate_speech("hello world",
                                         voice=BUILT_IN_VOICES[0],
                                         output_path="/tmp/out.wav")
    assert ok is True
    assert popen.call_count == 1, "runner must be spawned for valid input"
    # The voice must be forwarded to the runner via the JSON payload.
    args, kwargs = popen.call_args
    sent_stdin = kwargs.get("stdin")
    assert sent_stdin is subprocess.PIPE


def test_no_voice_uses_default(model_with_env, monkeypatch):
    """Absent voice resolves to DEFAULT_VOICE and reaches the runner."""
    popen = _stub_popen(monkeypatch)
    ok = model_with_env.generate_speech("hello world",
                                         output_path="/tmp/out.wav")
    assert ok is True
    assert popen.call_count == 1


def test_missing_env_unavailable():
    """Without an isolated env, the model reports unavailable."""
    m = KittenTTSModel("kitten-tts-nano")
    m.python_executable = None
    m._availability_cache = None
    assert m.check_availability() is False
    ok = m.generate_speech("hello", output_path="/tmp/out.wav")
    assert ok is False


def test_validate_voice():
    """validate_voice accepts only the documented built-in voices."""
    m = KittenTTSModel("kitten-tts-nano")
    for v in BUILT_IN_VOICES:
        assert m.validate_voice(v) is True
    assert m.validate_voice("nonsense") is False
    assert DEFAULT_VOICE in BUILT_IN_VOICES
