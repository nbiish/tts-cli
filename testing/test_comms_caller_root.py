"""Tests for project root discovery and AGENTS-TTS-COMMS.txt caller location."""

import os
from pathlib import Path
import pytest

from tts_cli.cli import _find_repo_root, _comms_file


def test_find_repo_root_from_cwd(tmp_path, monkeypatch):
    project_root = tmp_path / "my_project"
    project_root.mkdir()
    (project_root / "AGENTS.md").write_text("# Agents file\n", encoding="utf-8")

    sub_dir = project_root / "packages" / "subpackage"
    sub_dir.mkdir(parents=True)

    # Calling from sub_dir without TTS_CLI_CALLER_DIR
    monkeypatch.delenv("TTS_CLI_CALLER_DIR", raising=False)
    monkeypatch.chdir(sub_dir)

    found_root = _find_repo_root()
    assert found_root == project_root
    assert _comms_file() == project_root / "AGENTS-TTS-COMMS.txt"


def test_find_repo_root_respects_caller_env(tmp_path, monkeypatch):
    project_root = tmp_path / "caller_project"
    project_root.mkdir()
    (project_root / "llms.txt").write_text("# Contract\n", encoding="utf-8")

    sub_dir = project_root / "deep" / "nested" / "folder"
    sub_dir.mkdir(parents=True)

    monkeypatch.setenv("TTS_CLI_CALLER_DIR", str(sub_dir))

    found_root = _find_repo_root()
    assert found_root == project_root
    assert _comms_file() == project_root / "AGENTS-TTS-COMMS.txt"


def test_find_repo_root_detects_dot_agents_dir(tmp_path, monkeypatch):
    project_root = tmp_path / "custom_agent_workspace"
    project_root.mkdir()
    (project_root / ".agents").mkdir()

    sub_dir = project_root / "workspace"
    sub_dir.mkdir()

    monkeypatch.delenv("TTS_CLI_CALLER_DIR", raising=False)
    monkeypatch.chdir(sub_dir)

    found_root = _find_repo_root()
    assert found_root == project_root
