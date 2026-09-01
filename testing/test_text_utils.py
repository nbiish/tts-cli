"""Unit tests for sentence-aware TTS text splitting."""

import pytest

from tts_cli.core.text_utils import break_after_period_space, split_text


def test_empty_and_whitespace():
    assert split_text("") == []
    assert split_text("   \n\t  ") == []


def test_short_text_is_one_chunk():
    assert split_text("Hello world.", max_length=350) == ["Hello world."]


def test_splits_on_sentence_boundaries():
    a = "A" * 40 + "."
    b = "B" * 40 + "."
    chunks = split_text(f"{a} {b}", max_length=50)
    assert chunks == [a, b]
    assert all(len(c) <= 50 for c in chunks)


def test_no_chunk_exceeds_max_length():
    text = ("This is a sentence. " * 30).strip()
    chunks = split_text(text, max_length=80)
    assert len(chunks) > 1
    assert all(0 < len(c) <= 80 for c in chunks)
    assert " ".join(chunks).replace("  ", " ") == " ".join(text.split())


def test_hard_splits_overlong_token():
    token = "x" * 500
    chunks = split_text(token, max_length=120)
    assert all(len(c) <= 120 for c in chunks)
    assert "".join(chunks) == token


def test_rejects_non_positive_max_length():
    with pytest.raises(ValueError, match="max_length"):
        split_text("hi", max_length=0)


def test_break_after_period_space_wraps_sentences():
    flat = (
        "confirm merge of the wrap. "
        "What would this adversarial-security master suggest? Keep the ledger as data. "
        "What would this privacy master suggest? Omit keys."
    )
    wrapped = break_after_period_space(flat)
    assert wrapped == (
        "confirm merge of the wrap.\n"
        "What would this adversarial-security master suggest? Keep the ledger as data.\n"
        "What would this privacy master suggest? Omit keys."
    )


def test_break_after_period_space_is_idempotent_and_keeps_decimals():
    already = "confirm merge.\nWhat would this test master suggest? Keep 1.8 generate."
    assert break_after_period_space(already) == already
    assert break_after_period_space("") == ""
    assert break_after_period_space("No period here") == "No period here"
