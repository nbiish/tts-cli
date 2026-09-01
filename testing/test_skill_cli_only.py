"""tts-cli skill is CLI tooling only — no MCP content."""

from pathlib import Path

from tts_cli.cli import DETERMINISTIC_MASTERS, MASTER_QUESTIONS, SLASH_MASTERS

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
    assert len(MASTER_QUESTIONS) == 9
    assert len(DETERMINISTIC_MASTERS) == 6
    assert len(SLASH_MASTERS) == 3
    assert "adversarial / security" in text
    assert "privacy / data-protection regulatory" in text
    assert "supply-chain / third-party-risk" in text
    assert "systems-architecture / devops / infrastructure" in text
    assert "reliability / verification" in text
    assert "governance / sovereignty" in text
    assert "___ / ___" in text
    assert "craft / next-agent" not in text
    assert "data-minimization" not in text
    assert "--voice" not in text
    assert "--wait" not in text
    assert "expr-voice" not in text
    assert "list-voices" not in text
    lowered = text.lower()
    assert "do not wait" not in lowered
    assert "detach" not in lowered
    assert "setup-global" not in text
    assert "--clipboard" not in text
    assert "create-environment" not in text
