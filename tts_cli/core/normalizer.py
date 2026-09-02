"""
Text Normalization for Speech Synthesis.

Performs robust text cleaning, Markdown stripping, acronym pronunciation
formatting, punctuation normalization, pause pacing, and acoustic artifact
prevention for on-device MOSS-TTS and KittenTTS models.
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
    "API": "A P I",
    "CPU": "C P U",
    "GPU": "G P U",
    "LLM": "L L M",
    "WSL": "W S L",
    "URL": "U R L",
    "CI": "C I",
    "CD": "C D",
    "SHA": "S H A",
    "OS": "O S",
    "DB": "D B",
    "RAM": "RAM",
    "RSS": "R S S",
    "EBU": "E B U",
    "WSOLA": "W S O L A",
    "RVQ": "R V Q",
    "WAV": "WAV",
    "HF": "H F",
}

# Specific term pronunciations for natural speech cadence
TERM_EXPANSIONS = {
    r"\b1\.8[xX×]\b": "one point eight times",
    r"\b1\.8\b": "one point eight",
    r"\b48\s*k[hH][zZ]\b": "forty-eight kilohertz",
    r"\b24\s*k[hH][zZ]\b": "twenty-four kilohertz",
    r"\b44\.1\s*k[hH][zZ]\b": "forty-four point one kilohertz",
    r"\b100[mM]\b": "one hundred million",
    r"\b20[mM]\b": "twenty million",
    r"\b15[mM]\b": "fifteen million",
}


def normalize_text_for_speech(text: str) -> str:
    """Normalize and clean raw prompt text for high-fidelity speech synthesis.
    
    1. Strips Markdown formatting (bold, italic, code spans, links, headers).
    2. Cleans up bullet characters, list markers, and structural symbols.
    3. Normalizes technical acronyms and file extensions for natural cadence.
    4. Converts slashes, hyphens, and placeholders to smooth spoken equivalents.
    5. Paces punctuation and sentence boundaries cleanly to prevent acoustic artifacts.
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

    # Clean fill-in placeholder blanks (e.g. ___ / ___ master suggest)
    cleaned = re.sub(r"_{2,}\s*/\s*_{2,}", "specialist", cleaned)
    cleaned = re.sub(r"_{2,}", "", cleaned)

    # Strip bold / italic: **bold**, *italic*, __bold__, _italic_
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"\*([^*]+)\*", r"\1", cleaned)
    cleaned = re.sub(r"__([^_]+)__", r"\1", cleaned)

    # Strip list item markers: - item, * item, 1. item
    cleaned = re.sub(r"^\s*[-*•]\s+", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^\s*\d+\.\s+", "", cleaned, flags=re.MULTILINE)

    # Convert slashes between words to 'and' or space
    cleaned = re.sub(r"\s+/\s+", " and ", cleaned)
    cleaned = re.sub(r"(?<=\w)/(?=\w)", " and ", cleaned)

    # Hyphenated compound terms: convert hyphen to space for smooth articulation
    cleaned = re.sub(r"([a-zA-Z]+)-([a-zA-Z]+)", r"\1 \2", cleaned)

    # Replace brackets and quotes with comma/space
    cleaned = re.sub(r"[\[\]{}【】〖〗『』「」\"'“”‘’]", " ", cleaned)

    # Normalize em-dashes and hyphens between clauses to commas
    cleaned = re.sub(r"\s*[—–-]{2,}\s*", ", ", cleaned)

    # Clean multiple exclamation / question marks
    cleaned = re.sub(r"[!！]{2,}", "!", cleaned)
    cleaned = re.sub(r"[\?？]{2,}", "?", cleaned)
    cleaned = re.sub(r"\.{3,}|…", ".", cleaned)

    # Expand known speech terms (e.g. 1.8x, 48kHz)
    for pattern, expansion in TERM_EXPANSIONS.items():
        cleaned = re.sub(pattern, expansion, cleaned)

    # Acronym spacing for crisp pronunciation
    for acr, expansion in TECH_ACRONYMS.items():
        pattern = r"\b" + re.escape(acr) + r"\b"
        cleaned = re.sub(pattern, expansion, cleaned)

    # Strip leftover special punctuation symbols that can glitch audio decoders
    cleaned = re.sub(r"[@#$%^&*~|\\<>]", " ", cleaned)

    # Normalize whitespace and newlines to sentence pauses
    cleaned = re.sub(r"\n+", ". ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)

    # Clean up double periods / commas
    cleaned = re.sub(r"\s*\.\s*\.", ".", cleaned)
    cleaned = re.sub(r"\s*,\s*,", ",", cleaned)
    cleaned = re.sub(r"\s*,\s*\.", ".", cleaned)
    cleaned = re.sub(r"\s*\?\s*\.", "?", cleaned)

    return cleaned.strip()
