"""Validation tests for the MossTTSModel adapter."""

import json
import subprocess
from unittest.mock import MagicMock
from pathlib import Path
import pytest

from tts_cli.models.moss_tts_model import (
    MossTTSModel,
    DEFAULT_VOICE,
    BUILT_IN_VOICES,
    MAX_TEXT_LENGTH,
    _resolve_bundled_voice_path,
)


@pytest.fixture
def moss_model(monkeypatch):
    m = MossTTSModel("moss-tts-nano")
    m.python_executable = "/fake/venv/bin/python"
    m._availability_cache = True
    return m


def test_moss_tts_supported_voices(moss_model):
    voices = moss_model.get_supported_voices()
    assert "en_calm_female" in voices
    assert "en_conversational_female" in voices


def test_moss_tts_rejects_empty_text(moss_model):
    assert moss_model.generate_speech("") is False
    assert moss_model.generate_speech("   \n") is False


def test_moss_tts_rejects_overlong_text(moss_model):
    long_text = "a" * (MAX_TEXT_LENGTH + 1)
    assert moss_model.generate_speech(long_text) is False


def test_resolve_bundled_voice_path():
    path = _resolve_bundled_voice_path("en_calm_female")
    assert path.name.endswith(".wav")
