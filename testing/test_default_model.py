"""Lock-in tests for the default-model selection.

`auto` must resolve to ``kitten-tts-nano`` — the fastest engine (cold ~7.9s,
RTF ~0.47) — unless the operator overrides via ``TTS_CLI_DEFAULT_MODEL`` or
``~/.tts-cli/default_model``. MOSS-TTS stays selectable as the secondary
zero-shot cloning engine.

Hermetic: no engine, no subprocess, no network. ``HOME`` is redirected so the
user config file is never touched.
"""

import pytest

from tts_cli.cli import (
    DEFAULT_MODEL_FALLBACK,
    SELECTABLE_MODELS,
    get_default_model,
    set_default_model,
    setup_models,
)
from tts_cli.core.model_registry import model_registry
from tts_cli.models.kitten_tts_model import KittenTTSModel


@pytest.fixture(autouse=True)
def isolated_default_model_env(monkeypatch, tmp_path):
    """No env override, no real ~/.tts-cli config for the whole module."""
    monkeypatch.delenv("TTS_CLI_DEFAULT_MODEL", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    return tmp_path


def test_builtin_fallback_is_kitten():
    """The built-in default (what `auto` resolves to) is kitten-tts-nano."""
    assert DEFAULT_MODEL_FALLBACK == "kitten-tts-nano"
    assert get_default_model() == "kitten-tts-nano"


def test_selectable_models_lead_with_default():
    assert SELECTABLE_MODELS[0] == DEFAULT_MODEL_FALLBACK
    assert "moss-tts-nano" in SELECTABLE_MODELS


def test_env_overrides_default(monkeypatch):
    """MOSS stays reachable as the secondary engine via env override."""
    monkeypatch.setenv("TTS_CLI_DEFAULT_MODEL", "moss-tts-nano")
    assert get_default_model() == "moss-tts-nano"


def test_config_file_overrides_fallback(isolated_default_model_env, tmp_path):
    cfg = tmp_path / ".tts-cli" / "default_model"
    cfg.parent.mkdir(parents=True)
    cfg.write_text("moss-tts-nano", encoding="utf-8")
    assert get_default_model() == "moss-tts-nano"


def test_invalid_config_falls_back_to_kitten(isolated_default_model_env, tmp_path):
    cfg = tmp_path / ".tts-cli" / "default_model"
    cfg.parent.mkdir(parents=True)
    cfg.write_text("pocket-tts", encoding="utf-8")
    assert get_default_model() == "kitten-tts-nano"


def test_set_default_rejects_unknown(capsys):
    assert set_default_model("pocket-tts") is False
    assert "Unknown model" in capsys.readouterr().out


def test_auto_alias_registers_kitten_default():
    """The registry `auto` alias reflects the kitten default for --list."""
    setup_models()
    model = model_registry.get_model("auto")
    assert isinstance(model, KittenTTSModel)
    assert model_registry.get_model("moss-tts-nano") is not None
