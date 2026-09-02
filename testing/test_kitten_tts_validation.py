"""Validation tests for the KittenTTS adapter.

Proves the fail-closed safety properties of ``KittenTTSModel.generate_speech``:
  - overlong text is rejected before any subprocess is spawned.
  - empty text is rejected before any subprocess is spawned.
  - an unrecognized built-in voice name is rejected (fail-closed, no silent
    fallback) before any subprocess is spawned.
  - a valid voice + valid text reaches the runner subprocess.
  - text over CHUNK_TEXT_LENGTH is split and sent as ``chunks`` in one spawn
    (model loads once; the runner concatenates WAVs).

These tests never invoke the real KittenTTS engine or its isolated env — they
stub ``subprocess.Popen`` and assert whether it was reached, so they are fast
and hermetic.
"""

import json
import subprocess
from unittest.mock import MagicMock

import pytest

from tts_cli.models.kitten_tts_model import (
    KittenTTSModel,
    MAX_TEXT_LENGTH,
    CHUNK_TEXT_LENGTH,
    BUILT_IN_VOICES,
    DEFAULT_GENERATE_SPEED,
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


def test_no_voice_defaults_to_expr_voice_5_f(model_with_env, monkeypatch):
    """Omitted voice defaults to expr-voice-5-f (the last woman voice); generate speed defaults to 1.8."""
    popen = _stub_popen(monkeypatch)
    ok = model_with_env.generate_speech("hello world", output_path="/tmp/out.wav")
    assert ok is True
    assert popen.call_count == 1
    payload = _payload_from_popen(popen)
    assert payload["voice"] == "expr-voice-5-f"
    assert payload["speed"] == DEFAULT_GENERATE_SPEED
    assert payload["speed"] == 1.8


def test_missing_env_unavailable():
    """Without an isolated env, the model reports unavailable."""
    m = KittenTTSModel("kitten-tts-nano")
    m.python_executable = None
    m._availability_cache = None
    assert m.check_availability() is False
    ok = m.generate_speech("hello", output_path="/tmp/out.wav")
    assert ok is False


def _payload_from_popen(popen) -> dict:
    """Decode the JSON stdin payload sent to the runner."""
    fake_proc = popen.return_value
    args, kwargs = fake_proc.communicate.call_args
    raw = kwargs.get("input") if kwargs else None
    if raw is None and args:
        raw = args[0]
    return json.loads(raw)


def test_empty_text_rejected(model_with_env, monkeypatch):
    """Empty / whitespace-only text is rejected before spawning the runner."""
    popen = _stub_popen(monkeypatch)
    ok = model_with_env.generate_speech("   \n", output_path="/tmp/out.wav")
    assert ok is False
    assert popen.call_count == 0


def test_short_text_sends_one_chunk(model_with_env, monkeypatch):
    """Text under CHUNK_TEXT_LENGTH is a single chunk in one runner spawn."""
    popen = _stub_popen(monkeypatch)
    ok = model_with_env.generate_speech("hello world",
                                         output_path="/tmp/out.wav")
    assert ok is True
    assert popen.call_count == 1
    payload = _payload_from_popen(popen)
    assert payload["chunks"] == ["hello world"]


def test_long_text_is_chunked_in_one_spawn(model_with_env, monkeypatch):
    """Text over CHUNK_TEXT_LENGTH is split; the runner still loads once."""
    popen = _stub_popen(monkeypatch)
    sentence = "This is a complete test sentence used for chunking. "
    text = sentence * 12  # well over 350 chars, under 5000
    assert CHUNK_TEXT_LENGTH < len(text) < MAX_TEXT_LENGTH
    ok = model_with_env.generate_speech(text, output_path="/tmp/out.wav")
    assert ok is True
    assert popen.call_count == 1, "chunking must not spawn one runner per chunk"
    payload = _payload_from_popen(popen)
    chunks = payload["chunks"]
    assert len(chunks) >= 2
    assert all(len(c) <= CHUNK_TEXT_LENGTH for c in chunks)
    assert " ".join(chunks) == " ".join(text.split())


def test_runner_keeps_one_onnx_session_for_all_chunks():
    """Runner loads KittenTTS once, loops generate_to_file, then drops the session."""
    script = KittenTTSModel._runner_script()
    assert script.count("tts = KittenTTS(") == 1
    assert "loading KittenTTS once" in script
    load_at = script.index("tts = KittenTTS(")
    loop_at = script.index("for i, chunk in enumerate(chunks):")
    gen_at = script.index("tts.generate_to_file(")
    unload_at = script.index("del tts")
    concat_at = script.index("_concat_wavs(part_paths, output_path)")
    assert load_at < loop_at < gen_at < unload_at < concat_at
    assert script.count("tts = KittenTTS(") == 1
    assert script.count("tts.generate_to_file(") == 1


def test_validate_voice():
    """validate_voice accepts only the documented built-in voices."""
    m = KittenTTSModel("kitten-tts-nano")
    for v in BUILT_IN_VOICES:
        assert m.validate_voice(v) is True
    assert m.validate_voice("nonsense") is False
    assert "expr-voice-5-m" in BUILT_IN_VOICES
    assert DEFAULT_GENERATE_SPEED == 1.8
