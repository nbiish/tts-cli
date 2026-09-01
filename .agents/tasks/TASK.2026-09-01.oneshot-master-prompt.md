# TASK 2026-09-01 — tts-cli skill is CLI-only

**Branch:** `feat/tts-cli-oneshot-prompt`
**Worktree:** `../tts-cli-oneshot-prompt`
**Classification:** Confidential — no secrets

## Goal

`.agents/skills/tts-cli/SKILL.md` teaches the `cli-tts` CLI only: commands,
expected `--prompt` shape, ledger, voices, setup. **Zero MCP mentions**
(not even a "there is no MCP" disclaimer). End-of-chat output is one
`--prompt` whose Next-step body is the fused order plus one sentence per
master (`AGENTS.md` `<OUTPUT>` is the binding copy).

## Done when

- Skill file has no `MCP` / `mcp` substring.
- YAML description, command table, and HEREDOC are CLI-only.
- `cli-tts --next-step-prompt` prints the eleven questions.
- Tests lock the skill invariant and the eleven-answer ledger capture.
- Ledger cap is 5000 so a valid `--prompt` is not truncated.

## Non-goals

- Do not add a TTS server of any kind.
- Do not invent a panel format in `AGENTS-TTS-COMMS.txt`.
