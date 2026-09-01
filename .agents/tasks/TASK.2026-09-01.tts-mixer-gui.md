# TASK 2026-09-01 — Rust tts-cli mixer GUI (long-term)

**Status:** vision only — do not implement in the speed/voice/detach feat
**Classification:** Confidential — no secrets
**Native language when built:** Rust (do not rewrite the Python CLI into Rust)

## Goal

A **Rust GUI** that pops up for tts-cli playback and is the **one mixer** for
every agent on the machine.

1. **Volume** — operator-controlled output level for tts-cli only, applied to
   every agent speak (not the rest of the desktop).
2. **Process watch** — identify tts-cli (and its generate/play children) by
   PID and related process controls so overlapping chats cannot each grab
   the speaker.
3. **Sequential queue** — when many agents (or one agent in one chat) call
   `cli-tts`, plays are a **track list**: enqueue, play one after another,
   never overlap.
4. **Transport** — skip forward / backward like a playlist (previous, next,
   maybe scrub). Volume for all tracks is the GUI slider.
5. **Permanent heard speed** — the GUI sets the **durable generate speed**
   of the **final WAV** for every tts-cli call (same knob as today's CLI
   `--speed` / 1.8 default), not a second stacked player rate.

## Why later

The CLI now serializes playback on `~/.tts-cli/play.lock` (see
`tts_cli/core/play_queue.py`). The mixer is still how the operator gets one
volume, skippable tracks, PID watch, and a durable generate-speed knob.
Do not re-implement the speaker mutex in the GUI — take the same lock file
or become the sole player that holds it.

## Constraints (when an implement chat opens)

- Rust GUI, Python CLI stays the generator. Do not rewrite the engine.
- No secrets in the GUI, task, or logs. PIDs and WAV paths only.
- Fail closed if a process is not tts-cli. Do not attach to arbitrary PIDs
  as a generic volume hijack.
- Queue is FIFO across agents; skip is operator-only.
- Heard speed writes the WAV (or a single post-process of the WAV). Player
  rate stays 1.0 so rates do not stack.
- One GUI instance per machine (or per user session), not one window per
  agent.

## Binding copies to update when it ships

`llms.txt` User Preferences, `README.md` Roadmap, `AGENTS.md` only if agent
speak changes, `.agents/skills/tts-cli/SKILL.md` (playback still one
`--prompt`; the CLI plays automatically.
