"""Validation tests for the AGENTS-TTS-COMMS.txt last-suggestion reader."""
from pathlib import Path

import pytest

from tts_cli.cli import read_last_suggestion


def _write(tmp_path: Path, body: str) -> Path:
    f = tmp_path / "AGENTS-TTS-COMMS.txt"
    f.write_text(body, encoding="utf-8")
    return f


def test_returns_last_suggestion(monkeypatch, tmp_path):
    body = (
        "# header\n#\n# more header\n\n"
        "## 2026-08-31T22:00:00Z\nfirst suggestion.\n\n"
        "## 2026-08-31T22:30:00Z\nsecond suggestion.\n"
    )
    f = _write(tmp_path, body)
    monkeypatch.setattr("tts_cli.cli._comms_file", lambda: f)
    assert read_last_suggestion() == "second suggestion."


def test_ignores_header_comments(monkeypatch, tmp_path):
    body = "# only header\n# no entries\n"
    f = _write(tmp_path, body)
    monkeypatch.setattr("tts_cli.cli._comms_file", lambda: f)
    assert read_last_suggestion() is None


def test_missing_file_returns_none(monkeypatch, tmp_path):
    monkeypatch.setattr("tts_cli.cli._comms_file", lambda: tmp_path / "does-not-exist.txt")
    assert read_last_suggestion() is None


def test_multiline_suggestion(monkeypatch, tmp_path):
    body = (
        "## 2026-08-31T22:00:00Z\nshort.\n\n"
        "## 2026-08-31T23:00:00Z\nline one\nline two\n"
    )
    f = _write(tmp_path, body)
    monkeypatch.setattr("tts_cli.cli._comms_file", lambda: f)
    assert read_last_suggestion() == "line one\nline two"


def test_empty_block_yields_none(monkeypatch, tmp_path):
    body = "## 2026-08-31T22:00:00Z\n\n## 2026-08-31T23:00:00Z\n"
    f = _write(tmp_path, body)
    monkeypatch.setattr("tts_cli.cli._comms_file", lambda: f)
    assert read_last_suggestion() is None
