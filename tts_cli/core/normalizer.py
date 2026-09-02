"""
Text Normalization for Speech Synthesis.

Performs robust text cleaning, Markdown stripping, acronym pronunciation
formatting, punctuation normalization, and pause pacing for on-device TTS.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Sequence

# Common technical acronyms that should be pronounced letter-by-letter if needed
TECH_ACRONYMS = {
    "PQC": "P Q C",
    "CLI": "C L I",
    "TUI": "T U I",
    "GUI": "G U I",
    "RTF": "R T F",
    "TTFT": "T T F T",
    "PRD": "P R D",
    "KEM": "K E M",
    "DSA": "D S A",
    "FIPS": "FIPS",
    "ONNX": "ONNX",
    "TTS": "T T S",
}


def normalize_text_for_speech(text: str) -> str:
    """Normalize and clean raw prompt text for high-fidelity speech synthesis.
    
    1. Strips Markdown formatting (bold, italic, code spans, links, headers).
    2. Cleans up bullet characters, list markers, and structural symbols.
    3. Normalizes technical acronyms and file extensions for natural cadence.
    4. Paces punctuation and sentence boundaries cleanly.
    """
    if not text:
        return ""

    # Normalize unicode
    cleaned = unicodedata.normalize("NFKC", text)

    # Convert markdown links: [link text](http://...) -> link text
    cleaned = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", cleaned)

    # Strip code spans: `code` -> code
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)

    # Strip markdown headers: # Header -> Header
    cleaned = re.sub(r"^\s*#+\s*", "", cleaned, flags=re.MULTILINE)

    # Strip bold / italic: **bold**, *italic*, __bold__, _italic_
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"\*([^*]+)\*", r"\1", cleaned)
    cleaned = re.sub(r"__([^_]+)__", r"\1", cleaned)

    # Strip list item markers: - item, * item, 1. item
    cleaned = re.sub(r"^\s*[-*•]\s+", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^\s*\d+\.\s+", "", cleaned, flags=re.MULTILINE)

    # Replace brackets with comma/pause
    cleaned = re.sub(r"[\[\]{}【】〖〗『』「」]", " ", cleaned)

    # Normalize em-dashes and hyphens between clauses
    cleaned = re.sub(r"\s*[—–-]{2,}\s*", ", ", cleaned)

    # Clean multiple exclamation / question marks
    cleaned = re.sub(r"[!！]{2,}", "!", cleaned)
    cleaned = re.sub(r"[\?？]{2,}", "?", cleaned)
    cleaned = re.sub(r"\.{3,}|…", ".", cleaned)

    # Acronym spacing for crisp pronunciation
    for acr, expansion in TECH_ACRONYMS.items():
        pattern = r"\b" + re.escape(acr) + r"\b"
        cleaned = re.sub(pattern, expansion, cleaned)

    # Normalize whitespace and newlines
    cleaned = re.sub(r"\n+", ". ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)

    # Clean up double periods / commas
    cleaned = re.sub(r"\s*\.\s*\.", ".", cleaned)
    cleaned = re.sub(r"\s*,\s*,", ",", cleaned)
    cleaned = re.sub(r"\s*,\s*\.", ".", cleaned)

    return cleaned.strip()
