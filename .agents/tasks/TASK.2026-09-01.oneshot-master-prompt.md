# TASK 2026-09-01 — one-shot master-suggest prompt

**Branch:** `feat/tts-oneshot-master-prompt`
**Worktree:** `../tts-oneshot-master-prompt`
**Classification:** Confidential — no secrets

## Goal

The tts-cli skill and MCP tool blurb present **one** prompt: each master
answers in one sentence, then one fused `Next step:`. Agents make **one**
speak call. No per-expert tool loops.

## Done when

- Skill contains the copy-paste one-shot prompt.
- YAML `description` and `MCP_AUDIO_GUIDE.md` tell harnesses: one tool,
  one call.
- `AGENTS.md` `<OUTPUT>` points at that prompt.

## Non-goals

- No new MCP server.
- No panel in `AGENTS-TTS-COMMS.txt`.
