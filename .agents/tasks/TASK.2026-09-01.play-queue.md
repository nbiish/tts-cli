# TASK 2026-09-01 — Sequential speaker lock

**Branch:** `feat/play-sequential-queue`
**Worktree:** `../tts-cli-play-queue`
**Classification:** Confidential — no secrets

## Goal

Never overlay `cli-tts` playback. CLI, agent skill, and future GUI all play
through `play_audio` → `exclusive_speaker` (per-user `~/.tts-cli/play.lock`).

Generation may still run in parallel. Only the OS player is serialized.

## Out of scope

Rust mixer GUI (skip, volume, PID watch). Backend queue is enough for no overlap.
