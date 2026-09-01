# TASK 2026-08-31 — fused next-step (no panel)

**Branch:** `feat/tts-fused-suggestion`
**Worktree:** `../tts-panel-council`
**Classification:** Confidential — no secrets

## Goal

The "Next step:" line that `cli-tts` speaks and appends to
`AGENTS-TTS-COMMS.txt` is a **silent fusion** of answers to every
"What would this {master} suggest?" question in
`.agents/skills/tts-cli/SKILL.md`. The model answers internally, writes
**one** imperative into `--prompt`. The CLI stays a dumb recorder.

## Non-goals

- No `Panel:` block, chair keys, or engine-side split/strip.
- No first-match leftover-risk rule.
- No subagents role-playing the room.

## Chairs (silent; extra beyond the original six marked)

Original: adversarial security; networks/supply-chain; systems architecture;
reliability/SRE; product/operator-trust; craft/next-agent.

Added: privacy/data-minimization (spoken + public ledger); test/QA;
release/rollback; human-factors/ear; governance/license/sovereignty.

## Done when

- Skill and `AGENTS.md` `<OUTPUT>` agree: answer the "What would this {master} suggest?" list → fuse → one `Next step:`.
- Engine code has no panel schema.
- Ledger header describes fused order only.
- `llms.txt` User Preferences match.

## Verify

`rg -n 'PANEL_CHAIR|_strip_panel|Panel:' tts_cli/` must be empty.
`pytest testing/test_extract_suggestion.py testing/test_last_suggestion.py -q --no-cov`
