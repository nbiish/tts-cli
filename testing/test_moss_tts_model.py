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
    MOSS_OUTPUT_SPEED,
    MAX_REFERENCE_DURATION_SECS,
    _resolve_bundled_voice_path,
    _check_reference_duration,
)


@pytest.fixture
def moss_model(monkeypatch):
    m = MossTTSModel("moss-tts-nano")
    m.python_executable = "/fake/venv/bin/python"
    m._availability_cache = True
    return m


def test_moss_tts_default_voice_is_narrator():
    assert DEFAULT_VOICE == "en_narrator"


def test_moss_tts_supported_voices(moss_model):
    voices = moss_model.get_supported_voices()
    assert "en_narrator" in voices
    assert "en_conversational_female" in voices


def test_moss_tts_output_speed_is_1_8():
    assert MOSS_OUTPUT_SPEED == 1.8


def test_moss_tts_rejects_empty_text(moss_model):
    assert moss_model.generate_speech("") is False
    assert moss_model.generate_speech("   \n") is False


def test_moss_tts_rejects_overlong_text(moss_model):
    long_text = "a" * (MAX_TEXT_LENGTH + 1)
    assert moss_model.generate_speech(long_text) is False


def test_resolve_bundled_voice_path():
    path = _resolve_bundled_voice_path("en_narrator")
    assert path.name.endswith(".wav")


def test_reference_duration_bound():
    """MAX_REFERENCE_DURATION_SECS prevents oversized reference clips."""
    assert MAX_REFERENCE_DURATION_SECS == 30.0


def test_model_info_includes_speed(moss_model):
    info = moss_model.get_model_info()
    assert info["output_speed"] == 1.8
    assert info["default_voice"] == "en_narrator"
