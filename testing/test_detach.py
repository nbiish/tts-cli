"""Speak without --output returns immediately; --output stays in-process."""

import subprocess
import sys
from unittest.mock import MagicMock

import pytest

from tts_cli.cli import main


def test_prompt_returns_immediately(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["cli-tts", "--prompt", "hello from parent"])
    monkeypatch.setattr(
        "tts_cli.cli.get_cached_output_path", lambda: "/tmp/cached.wav"
    )
    spawned = {}

    def fake_popen(argv, **kwargs):
        spawned["argv"] = argv
        spawned["kwargs"] = kwargs
        return MagicMock()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    def _must_not_generate(*_a, **_k):
        raise AssertionError("parent must not generate when --output is omitted")

    monkeypatch.setattr("tts_cli.cli.generate_speech", _must_not_generate)

    with pytest.raises(SystemExit) as exited:
        main()
    assert exited.value.code == 0
    argv = spawned["argv"]
    assert "--wait" not in argv
    assert argv[1:3] == ["-m", "tts_cli.cli"]
    assert "--text" in argv
    assert "hello from parent" in argv
    assert "--output" in argv
    assert "/tmp/cached.wav" in argv
    kwargs = spawned["kwargs"]
    assert kwargs.get("start_new_session") is True
    assert kwargs.get("stdin") is subprocess.DEVNULL
    assert kwargs.get("stdout") is subprocess.DEVNULL
    assert kwargs.get("stderr") is subprocess.DEVNULL


def test_output_stays_in_process(monkeypatch):
    monkeypatch.setattr(
        sys, "argv", ["cli-tts", "--text", "hello file", "--output", "/tmp/out.wav"]
    )
    gen = MagicMock(return_value=True)
    monkeypatch.setattr("tts_cli.cli.generate_speech", gen)
    monkeypatch.setattr("tts_cli.cli.play_audio", lambda *_a, **_k: None)
    monkeypatch.setattr(
        "tts_cli.cli._spawn_detached_child",
        lambda *_a, **_k: (_ for _ in ()).throw(
            AssertionError("must not spawn when --output is set")
        ),
    )
    main()
    assert gen.call_count == 1
    assert gen.call_args.kwargs["text"] == "hello file"
    assert gen.call_args.kwargs["speed"] == 1.8


def test_unknown_name_fails_in_parent(monkeypatch, capsys):
    monkeypatch.setattr(
        sys, "argv", ["cli-tts", "--voice", "not-a-voice", "--text", "hello"]
    )
    monkeypatch.setattr(
        "tts_cli.cli._spawn_detached_child",
        lambda *_a, **_k: (_ for _ in ()).throw(
            AssertionError("must not spawn on a bad name")
        ),
    )
    with pytest.raises(SystemExit) as exited:
        main()
    assert exited.value.code == 1
    assert "Unknown voice" in capsys.readouterr().out
