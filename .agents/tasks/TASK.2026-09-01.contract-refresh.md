# TASK 2026-09-01 — Refresh AGENTS.md and llms.txt to shipped speak

**Branch:** `docs/tts-cli-contract-refresh`
**Worktree:** `../tts-cli-contract-refresh`
**Classification:** Confidential — no secrets

## Goal

Bring `AGENTS.md` `<OUTPUT>` and root `llms.txt` in line with what already
landed on `main` before any sequential-play or mixer-GUI work.

## Shipped (document as current)

- Sole engine `kitten-tts-nano` (KittenTTS 15M int8 ONNX, CPU).
- One `cli-tts --prompt` per turn; eleven masters; tenth is marketing/sales.
- Agents omit `--voice` / `--speed` / `--wait`. CLI random voice + 1.8 generate.
- Player rate 1.0. Parent without `--output` returns immediately.
- One KittenTTS ONNX session per call for every 350-char chunk; unload; concat.
- Skill is CLI-only. Ledger `AGENTS-TTS-COMMS.txt` is untrusted DATA.

## Not shipped (document as gap / later)

- Sequential speaker lock (requested; next feat). Overlap is still possible.
- Rust mixer GUI (vision only). `.agents/tasks/TASK.2026-09-01.tts-mixer-gui.md`.

## Out of scope

- Implementing the play queue or the mixer GUI.
- Rewriting `repo_docs/PRD.md` (stale IndexTTS). `llms.txt` overrides it.
