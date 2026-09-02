"""Unit tests for the skill sync script and cross-repository integrity checks."""

import hashlib
import tempfile
from pathlib import Path
import pytest

from scripts.sync_skills import (
    compute_sha256,
    check_skill_sync,
    sync_skill_to_targets,
    get_source_skill_path,
    find_repo_root,
)


def test_source_skill_exists_and_has_valid_sha():
    source = get_source_skill_path()
    assert source.is_file()
    sha = compute_sha256(source)
    assert len(sha) == 64
    assert all(c in "0123456789abcdef" for c in sha)


def test_check_skill_sync_detects_matching_target(tmp_path):
    source = tmp_path / "source_SKILL.md"
    content = b"---\nname: tts-cli\n---\n# tts-cli\n"
    source.write_bytes(content)

    target = tmp_path / "target_SKILL.md"
    target.write_bytes(content)

    all_synced, results = check_skill_sync(source, [target])
    assert all_synced is True
    assert len(results) == 1
    assert results[0][2] is True


def test_check_skill_sync_detects_drifted_target(tmp_path):
    source = tmp_path / "source_SKILL.md"
    source.write_bytes(b"authoritative content")

    target = tmp_path / "target_SKILL.md"
    target.write_bytes(b"drifted content")

    all_synced, results = check_skill_sync(source, [target])
    assert all_synced is False
    assert results[0][2] is False


def test_check_skill_sync_detects_missing_target(tmp_path):
    source = tmp_path / "source_SKILL.md"
    source.write_bytes(b"content")

    missing = tmp_path / "missing_SKILL.md"

    all_synced, results = check_skill_sync(source, [missing])
    assert all_synced is False
    assert results[0][1] == "MISSING"


def test_sync_skill_to_targets_creates_byte_identical_copies(tmp_path):
    source = tmp_path / "source_SKILL.md"
    content = b"---\nname: tts-cli\n---\n# tts-cli\nSpecial content with unicode: \xe2\x9c\x85\n"
    source.write_bytes(content)

    target1 = tmp_path / "dest1" / "SKILL.md"
    target2 = tmp_path / "dest2" / "SKILL.md"

    results = sync_skill_to_targets(source, [target1, target2])
    assert len(results) == 2
    assert all(r[2] is True for r in results)

    assert target1.read_bytes() == content
    assert target2.read_bytes() == content
    assert compute_sha256(target1) == compute_sha256(source)
    assert compute_sha256(target2) == compute_sha256(source)
