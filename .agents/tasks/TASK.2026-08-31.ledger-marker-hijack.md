# TASK: Fail-closed ledger extract on a second Next-step marker

**Date:** 2026-08-31
**Branch:** `fix/tts-ledger-marker-hijack`
**Worktree:** `../tts-ledger-marker-hijack`
**Classification:** Confidential

## Objective

A second `Next step:` marker in the spoken summary must not hijack
`AGENTS-TTS-COMMS.txt`. `_extract_suggestion` previously used `rfind` (last
marker wins), so an extra marker after the real suggestion replaced the
recorded line; a marker in the summary plus a trailing real marker was
ambiguous. Fail closed: exactly one marker, or write nothing.

## Decisions

1. Count case-insensitive `next step:` occurrences. Zero or two-or-more →
   `None` (no ledger append). Speech still generates.
2. Route `_log_to_agents_tts_comms` through `_comms_file()` so tests can
   monkeypatch the path (no writes to the real ledger).
3. No secrets in this file.

## Verification

`uv run --extra dev pytest testing/test_extract_suggestion.py testing/test_last_suggestion.py -q --no-cov`
