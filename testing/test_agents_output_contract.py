"""AGENTS.md OUTPUT and llms.txt match the shipped speak contract."""

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_AGENTS = (_ROOT / "AGENTS.md").read_text(encoding="utf-8")
_LLMS = (_ROOT / "llms.txt").read_text(encoding="utf-8")


def test_agents_output_names_eleven_masters_and_marketing():
    assert "What would this marketing / sales master suggest?" in _AGENTS
    assert "craft / next-agent" not in _AGENTS
    assert _AGENTS.count("What would this ") >= 11


def test_agents_output_names_shipped_cli_behavior():
    assert "kitten-tts-nano" in _AGENTS
    assert "1.8" in _AGENTS
    assert "Player rate is **1.0**" in _AGENTS
    assert "Agents omit `--voice` and `--speed`" in _AGENTS
    assert "Do not pass `--wait`" in _AGENTS
    assert "One ONNX session per call" in _AGENTS
    assert "350-character chunk" in _AGENTS
    assert "AGENTS-TTS-COMMS.txt" in _AGENTS
    assert "CLI-only" in _AGENTS
    assert "Do not add IndexTTS" in _AGENTS
    assert "period-space" in _AGENTS
    assert "Do not prompt agents to wrap" in _AGENTS


def test_agents_output_claims_serialized_play():
    assert "Sequential plays" in _AGENTS
    assert "not serialized yet" not in _AGENTS
    assert "Do not build the Rust mixer GUI" in _AGENTS


def test_llms_is_kitten_prd_not_indextts():
    assert "This project is not yet indexed" not in _LLMS
    assert "kitten-tts-nano" in _LLMS
    assert "marketing / sales" in _LLMS
    assert "repo_docs/PRD.md" in _LLMS
    assert "Ignore it" in _LLMS
    assert "Sequential speaker lock (shipped)" in _LLMS
    assert "One KittenTTS ONNX session per call" in _LLMS
    assert "1.8" in _LLMS
    assert "period-space" in _LLMS
    assert "Do not add wrap instructions to the skill" in _LLMS
