# TASK 2026-09-01 — Nine deterministic masters plus three slash chairs

**Branch:** `feat/nine-plus-three-masters`
**Worktree:** `../tts-cli-masters`
**Classification:** Confidential — no secrets

## Goal

Agent speak uses **twelve** one-sentence answers. Nine chairs are
deterministic production/security names. Three chairs use the
`What would this {a} / {b} master suggest?` prompt shape.

## Roster (binding)

Nine deterministic (no slash):

1. adversarial-security
2. privacy
3. supply-chain
4. systems-architecture
5. reliability
6. test
7. release
8. product
9. governance

Three slash:

1. marketing / sales
2. human-factors / ear
3. license / sovereignty

Dropped dual names: privacy / data-minimization, networks / supply-chain,
reliability / SRE, test / QA, release / rollback, product / operator-trust,
governance / license / sovereignty (triple). `craft / next-agent` stays gone.

Canonical list: `tts_cli/cli.py` `DETERMINISTIC_MASTERS` then `SLASH_MASTERS`.
`MASTER_QUESTIONS` is length 12. Skill, `AGENTS.md` `<OUTPUT>`, `llms.txt`,
and `MCP_AUDIO_GUIDE.md` copy those questions verbatim.

## Skills in this repo

Keep: `tts-cli`, `pqc-secrets`, `pqc-signatures-security`,
`production-security`, `code-security`, `llm-security`.

Remove unused vendored packs (operator already pulled them off main).
Hub skill is not vendored: install with `wtf skill install`.

## After merge

Copy `.agents/skills/tts-cli/SKILL.md` into ainish-coder only
(`/Users/nbiish/code/ainish-coder/.agents/skills/tts-cli/SKILL.md`).
Byte-identical. Do not copy other skills. Do not copy until `main` holds
this merge.

## Out of scope

- Mixer GUI (`.agents/tasks/TASK.2026-09-01.tts-mixer-gui.md`).
- Rewriting historical COMMS/task files that still say eleven.
- Copying the skill into wtf-is-going-on-mcp this hop.

## Verify

`python -m pytest testing/ -q --no-cov` from the worktree. Skill, next-step
prompt, and AGENTS/llms contract tests must pass.
