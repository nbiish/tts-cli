"""Player rate stays 1.0 so KittenTTS generate 1.8 is not stacked."""

import inspect
import subprocess
from unittest.mock import MagicMock

from tts_cli.cli import PLAY_AUDIO_RATE, play_audio


def test_play_audio_default_rate_is_unity():
    sig = inspect.signature(play_audio)
    assert sig.parameters["speed"].default == 1.0
    assert PLAY_AUDIO_RATE == 1.0


def test_play_audio_darwin_passes_unity_rate(monkeypatch):
    monkeypatch.setattr("tts_cli.cli.platform.system", lambda: "Darwin")
    run = MagicMock()
    monkeypatch.setattr(subprocess, "run", run)
    play_audio("/tmp/out.wav")
    assert run.call_count == 1
    argv = run.call_args[0][0]
    assert argv[:3] == ["afplay", "--rate", "1.0"]
    assert argv[3] == "/tmp/out.wav"
    assert run.call_args.kwargs.get("check") is True
