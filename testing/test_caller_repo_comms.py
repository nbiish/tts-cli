"""Tests for caller repository root discovery and AGENTS-TTS-COMMS.txt routing."""

import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from tts_cli.cli import (
    AGENTS_TTS_COMMS_HEADER,
    _comms_file,
    _find_repo_root,
    _log_to_agents_tts_comms,
    _spawn_detached_child,
    read_last_suggestion,
)


def test_find_repo_root_at_git_root(tmp_path):
    repo_dir = tmp_path / "my_project"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    found = _find_repo_root(repo_dir)
    assert found == repo_dir.resolve()


def test_find_repo_root_from_nested_subdir(tmp_path):
    repo_dir = tmp_path / "my_project"
    sub_dir = repo_dir / "src" / "pkg" / "nested"
    sub_dir.mkdir(parents=True)
    (repo_dir / ".git").mkdir()

    found = _find_repo_root(sub_dir)
    assert found == repo_dir.resolve()


def test_find_repo_root_in_worktree_file(tmp_path):
    worktree_dir = tmp_path / "worktree_branch"
    worktree_dir.mkdir()
    git_file = worktree_dir / ".git"
    git_file.write_text("gitdir: /path/to/main/.git/worktrees/worktree_branch\n")

    found = _find_repo_root(worktree_dir)
    assert found == worktree_dir.resolve()


def test_find_repo_root_non_git_fallback(tmp_path):
    non_git_dir = tmp_path / "plain_folder"
    non_git_dir.mkdir()

    found = _find_repo_root(non_git_dir)
    assert found == non_git_dir.resolve()


def test_find_repo_root_env_var_override(tmp_path, monkeypatch):
    custom_dir = tmp_path / "custom_repo"
    custom_dir.mkdir()
    (custom_dir / ".git").mkdir()

    monkeypatch.setenv("TTS_CLI_CALLER_DIR", str(custom_dir))
    found = _find_repo_root()
    assert found == custom_dir.resolve()


def test_comms_file_returns_repo_root_comms(tmp_path):
    repo_dir = tmp_path / "target_repo"
    sub_dir = repo_dir / "sub"
    sub_dir.mkdir(parents=True)
    (repo_dir / ".git").mkdir()

    comms = _comms_file(sub_dir)
    assert comms == repo_dir.resolve() / "AGENTS-TTS-COMMS.txt"


def test_log_creates_header_in_fresh_repo(tmp_path, monkeypatch):
    repo_dir = tmp_path / "fresh_repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()
    monkeypatch.setenv("TTS_CLI_CALLER_DIR", str(repo_dir))

    ledger = repo_dir / "AGENTS-TTS-COMMS.txt"
    assert not ledger.exists()

    _log_to_agents_tts_comms(
        "Finished setup. Next step: add automated regression tests for repo routing.",
        "kitten-tts-nano",
        None,
        "/tmp/out.wav",
    )

    assert ledger.exists()
    content = ledger.read_text(encoding="utf-8")
    assert "# AGENTS-TTS-COMMS.txt" in content
    assert "add automated regression tests for repo routing." in content
    assert content.count("## ") == 1


def test_log_appends_without_repeating_header(tmp_path, monkeypatch):
    repo_dir = tmp_path / "fresh_repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()
    monkeypatch.setenv("TTS_CLI_CALLER_DIR", str(repo_dir))

    _log_to_agents_tts_comms(
        "Step 1. Next step: do first task.",
        "kitten-tts-nano",
        None,
        "/tmp/out.wav",
    )
    _log_to_agents_tts_comms(
        "Step 2. Next step: do second task.",
        "kitten-tts-nano",
        None,
        "/tmp/out.wav",
    )

    ledger = repo_dir / "AGENTS-TTS-COMMS.txt"
    content = ledger.read_text(encoding="utf-8")
    assert content.count("# AGENTS-TTS-COMMS.txt") == 1
    assert content.count("## ") == 2
    assert "do first task." in content
    assert "do second task." in content


def test_read_last_suggestion_from_caller_repo(tmp_path, monkeypatch):
    repo_dir = tmp_path / "active_repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()
    monkeypatch.setenv("TTS_CLI_CALLER_DIR", str(repo_dir))

    _log_to_agents_tts_comms(
        "Work done. Next step: ship the feature branch.",
        "kitten-tts-nano",
        None,
        "/tmp/out.wav",
    )

    last = read_last_suggestion()
    assert last == "ship the feature branch."


def test_spawn_detached_child_passes_caller_dir(monkeypatch, tmp_path):
    repo_dir = tmp_path / "spawn_caller_repo"
    repo_dir.mkdir()

    captured_kwargs = {}

    def mock_popen(argv, **kwargs):
        captured_kwargs.update(kwargs)
        return None

    monkeypatch.setattr(subprocess, "Popen", mock_popen)

    _spawn_detached_child(["python", "-m", "tts_cli.cli"], caller_dir=str(repo_dir))

    assert captured_kwargs.get("cwd") == str(repo_dir)
    assert captured_kwargs.get("env", {}).get("TTS_CLI_CALLER_DIR") == str(repo_dir)


def test_caller_dir_param_takes_priority_over_env(tmp_path, monkeypatch):
    """--caller-dir (explicit param) beats TTS_CLI_CALLER_DIR env var."""
    env_repo = tmp_path / "env_repo"
    env_repo.mkdir()
    (env_repo / ".git").mkdir()

    explicit_repo = tmp_path / "explicit_repo"
    explicit_repo.mkdir()
    (explicit_repo / ".git").mkdir()

    monkeypatch.setenv("TTS_CLI_CALLER_DIR", str(env_repo))

    _log_to_agents_tts_comms(
        "Test. Next step: verify priority.",
        "kitten-tts-nano",
        None,
        "/tmp/out.wav",
        caller_dir=str(explicit_repo),
    )

    # Ledger should land in explicit_repo, NOT env_repo
    assert (explicit_repo / "AGENTS-TTS-COMMS.txt").exists()
    assert not (env_repo / "AGENTS-TTS-COMMS.txt").exists()


def test_detached_child_argv_includes_caller_dir():
    """_detached_child_argv propagates --caller-dir to the child argv."""
    from tts_cli.cli import _detached_child_argv

    argv = _detached_child_argv(
        "hello",
        model="kitten-tts-nano",
        voice=None,
        speed=1.8,
        lang=None,
        output_path="/tmp/out.wav",
        caller_dir="/some/caller/dir",
    )
    assert "--caller-dir" in argv
    idx = argv.index("--caller-dir")
    assert argv[idx + 1] == "/some/caller/dir"


def test_detached_child_argv_omits_caller_dir_when_none():
    """_detached_child_argv omits --caller-dir when not provided."""
    from tts_cli.cli import _detached_child_argv

    argv = _detached_child_argv(
        "hello",
        model="kitten-tts-nano",
        voice=None,
        speed=1.8,
        lang=None,
        output_path="/tmp/out.wav",
    )
    assert "--caller-dir" not in argv


def test_read_last_suggestion_respects_caller_dir(tmp_path):
    """read_last_suggestion uses caller_dir to find the right ledger."""
    repo_a = tmp_path / "repo_a"
    repo_a.mkdir()
    (repo_a / ".git").mkdir()

    repo_b = tmp_path / "repo_b"
    repo_b.mkdir()
    (repo_b / ".git").mkdir()

    _log_to_agents_tts_comms(
        "From A. Next step: do A stuff.",
        "kitten-tts-nano",
        None,
        "/tmp/out.wav",
        caller_dir=str(repo_a),
    )
    _log_to_agents_tts_comms(
        "From B. Next step: do B stuff.",
        "kitten-tts-nano",
        None,
        "/tmp/out.wav",
        caller_dir=str(repo_b),
    )

    assert read_last_suggestion(caller_dir=str(repo_a)) == "do A stuff."
    assert read_last_suggestion(caller_dir=str(repo_b)) == "do B stuff."


def test_log_with_caller_dir_creates_header(tmp_path):
    """caller_dir creates the ledger with header in the right repo."""
    repo_dir = tmp_path / "fresh"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    ledger = repo_dir / "AGENTS-TTS-COMMS.txt"
    assert not ledger.exists()

    _log_to_agents_tts_comms(
        "Init. Next step: bootstrap.",
        "kitten-tts-nano",
        None,
        "/tmp/out.wav",
        caller_dir=str(repo_dir),
    )

    assert ledger.exists()
    content = ledger.read_text(encoding="utf-8")
    assert "# AGENTS-TTS-COMMS.txt" in content
    assert "bootstrap." in content

