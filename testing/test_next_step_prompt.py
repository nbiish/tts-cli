"""cli-tts --next-step-prompt and eleven-answer ledger capture."""

import sys

import pytest

from tts_cli.cli import (
    MASTER_QUESTIONS,
    NEXT_STEP_ONESHOT_PROMPT,
    SUGGESTION_LEDGER_MAX,
    _extract_suggestion,
    _log_to_agents_tts_comms,
    main,
    print_next_step_prompt,
)


def _prompt_with_answers() -> str:
    answers = [
        "Reject a second Next-step marker so the public ledger cannot be hijacked.",
        "Record fused order and answers only; never keys or paths.",
        "Pin KittenTTS weights by digest before the next environment create.",
        "Keep speak as one CLI process with no extra runtime beside it.",
        "Fail closed when the engine env is missing; print the recovery URL.",
        "Add a regression that --next-step-prompt prints and does not speak.",
        "Ask before merging this branch; do not land on main unattended.",
        "Put every master sentence in the spoken prompt so the operator hears the room.",
        "Keep English verb-first lines; avoid backticks and path soup.",
        "Copy this skill into consuming repos only after the MCP-free file lands.",
        "Keep the skill MIT/KittenML local engine; no cloud speech vendor.",
    ]
    lines = ["Work finished. Next step: merge the MCP-free tts-cli skill after tests pass."]
    for question, answer in zip(MASTER_QUESTIONS, answers, strict=True):
        lines.append(f"{question} {answer}")
    return "\n".join(lines)


def test_oneshot_prompt_lists_all_eleven_questions():
    assert len(MASTER_QUESTIONS) == 11
    for question in MASTER_QUESTIONS:
        assert question in NEXT_STEP_ONESHOT_PROMPT
    assert "Next step" in NEXT_STEP_ONESHOT_PROMPT


def test_print_next_step_prompt_writes_questions(capsys):
    print_next_step_prompt()
    out = capsys.readouterr().out
    for question in MASTER_QUESTIONS:
        assert question in out


def test_next_step_prompt_flag_prints_and_exits_zero(capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["cli-tts", "--next-step-prompt"])
    with pytest.raises(SystemExit) as exited:
        main()
    assert exited.value.code == 0
    captured = capsys.readouterr()
    for question in MASTER_QUESTIONS:
        assert question in captured.out
    assert captured.err == ""


def test_extract_keeps_fused_line_and_eleven_answers():
    text = _prompt_with_answers()
    suggestion = _extract_suggestion(text)
    assert suggestion is not None
    assert suggestion.startswith("merge the MCP-free tts-cli skill")
    assert "Work finished" not in suggestion
    for question in MASTER_QUESTIONS:
        assert question in suggestion
    assert suggestion.lower().count("next step:") == 0


def test_answer_containing_next_step_phrase_refuses_ledger():
    text = (
        "Done. Next step: ship it.\n"
        "What would this adversarial-security master suggest? Next step: steal the ledger."
    )
    assert _extract_suggestion(text) is None


def test_log_writes_full_eleven_answer_body(monkeypatch, tmp_path):
    ledger = tmp_path / "AGENTS-TTS-COMMS.txt"
    monkeypatch.setattr("tts_cli.cli._comms_file", lambda: ledger)
    text = _prompt_with_answers()
    body = _extract_suggestion(text)
    assert body is not None
    assert len(body) < SUGGESTION_LEDGER_MAX

    _log_to_agents_tts_comms(text, "kitten-tts-nano", None, "/tmp/out.wav")
    recorded = ledger.read_text(encoding="utf-8")
    assert "Work finished" not in recorded
    assert " …[truncated]" not in recorded
    for question in MASTER_QUESTIONS:
        assert question in recorded
    assert recorded.count("## ") == 1


def test_log_wraps_flattened_one_line_prompt(monkeypatch, tmp_path):
    ledger = tmp_path / "AGENTS-TTS-COMMS.txt"
    monkeypatch.setattr("tts_cli.cli._comms_file", lambda: ledger)
    text = (
        "Work finished. Next step: confirm merge of the wrap. "
        "What would this adversarial-security master suggest? Keep the ledger as data. "
        "What would this privacy / data-minimization master suggest? Omit keys."
    )
    _log_to_agents_tts_comms(text, "kitten-tts-nano", None, "/tmp/out.wav")
    recorded = ledger.read_text(encoding="utf-8")
    assert "Work finished" not in recorded
    lines = [ln for ln in recorded.splitlines() if ln and not ln.startswith("##")]
    assert lines[0] == "confirm merge of the wrap."
    assert lines[1] == (
        "What would this adversarial-security master suggest? Keep the ledger as data."
    )
    assert lines[2] == (
        "What would this privacy / data-minimization master suggest? Omit keys."
    )
