"""tts-cli skill is CLI tooling only — no MCP content."""

from pathlib import Path

from tts_cli.cli import MASTER_QUESTIONS

_SKILL = (
    Path(__file__).resolve().parents[1] / ".agents" / "skills" / "tts-cli" / "SKILL.md"
)


def test_skill_file_exists():
    assert _SKILL.is_file()


def test_skill_has_no_mcp_mention():
    text = _SKILL.read_text(encoding="utf-8")
    assert "mcp" not in text.lower()


def test_skill_names_cli_and_every_master_question():
    text = _SKILL.read_text(encoding="utf-8")
    assert "cli-tts --prompt" in text
    assert "cli-tts --next-step-prompt" in text
    for question in MASTER_QUESTIONS:
        assert question in text
    assert len(MASTER_QUESTIONS) == 11
