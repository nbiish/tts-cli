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
    assert "C P U" in cleaned


def test_slash_and_hyphen_expansion():
    text = "What would this adversarial / security master suggest? Apply zero-trust and third-party checks."
    cleaned = normalize_text_for_speech(text)
    assert " / " not in cleaned
    assert "adversarial and security" in cleaned
    assert "zero trust" in cleaned
    assert "third party" in cleaned


def test_term_expansions():
    text = "Generating audio at 1.8x speedup and 48kHz stereo on 100M model."
    cleaned = normalize_text_for_speech(text)
    assert "one point eight times" in cleaned
    assert "forty-eight kilohertz" in cleaned
    assert "one hundred million" in cleaned


def test_blank_placeholder_cleaning():
    text = "What would this ___ / ___ master suggest? <advice>"
    cleaned = normalize_text_for_speech(text)
    assert "___" not in cleaned
    assert "specialist" in cleaned


def test_empty_input():
    assert normalize_text_for_speech("") == ""
    assert normalize_text_for_speech(None) == ""
