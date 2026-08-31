"""Sentence-aware text splitting for TTS engines with a hard length limit."""

from __future__ import annotations

import re


def split_text(text: str, max_length: int = 350) -> list[str]:
    """Split ``text`` into chunks of at most ``max_length`` characters.

    Prefers sentence boundaries (``.``, ``!``, ``?``), then words. A single
    token longer than ``max_length`` is hard-split so no returned chunk
    exceeds the limit. Empty / whitespace-only input yields an empty list.

    Raises:
        ValueError: if ``max_length`` is less than 1.
    """
    if max_length < 1:
        raise ValueError("max_length must be >= 1")
    if not text or not text.strip():
        return []

    text = " ".join(text.split())
    if len(text) <= max_length:
        return [text]

    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current = ""

    def push_current() -> None:
        nonlocal current
        if current:
            chunks.append(current)
            current = ""

    def append_piece(piece: str) -> None:
        nonlocal current
        if not piece:
            return
        extra = len(piece) if not current else len(piece) + 1
        if len(current) + extra <= max_length:
            current = piece if not current else f"{current} {piece}"
            return
        push_current()
        if len(piece) <= max_length:
            current = piece
            return
        for i in range(0, len(piece), max_length):
            slice_ = piece[i:i + max_length]
            if len(slice_) == max_length:
                chunks.append(slice_)
            else:
                current = slice_

    for sentence in sentences:
        if len(sentence) <= max_length:
            append_piece(sentence)
            continue
        for word in sentence.split(" "):
            append_piece(word)

    push_current()
    return chunks
