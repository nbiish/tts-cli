"""Validation tests for the normalizer module."""

from tts_cli.core.normalizer import normalize_text_for_speech


def test_markdown_stripping():
    text = "## Summary\n- **PQC** security: `verified`\n- Link: [docs](https://example.com)"
    cleaned = normalize_text_for_speech(text)
    assert "##" not in cleaned
    assert "**" not in cleaned
    assert "`" not in cleaned
    assert "https://" not in cleaned
    assert "docs" in cleaned
    assert "P Q C" in cleaned


def test_acronym_pacing():
    text = "The CLI operates using ONNX on CPU."
    cleaned = normalize_text_for_speech(text)
    assert "C L I" in cleaned
    assert "ONNX" in cleaned


def test_empty_input():
    assert normalize_text_for_speech("") == ""
    assert normalize_text_for_speech(None) == ""
