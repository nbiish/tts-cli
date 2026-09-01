# TASK 2026-09-01 — Six deterministic masters plus three custom slash chairs

## Goal
Update the tts-cli masters roster across the codebase to six deterministic production/security chairs and three custom `___ / ___` chairs (filled in by agent judgment based on current task), and port the updated skill to `~/code/ainish-coder/.agents/skills/tts-cli/SKILL.md`.

## Masters Specification
Six deterministic:
1. `What would this adversarial / security master suggest?`
2. `What would this privacy / data-protection regulatory master suggest?`
3. `What would this supply-chain / third-party-risk master suggest?`
4. `What would this systems-architecture / devops / infrastructure master suggest?`
5. `What would this reliability / verification master suggest?`
6. `What would this governance / sovereignty master suggest?`

Three custom/fill-in:
7. `What would this ___ / ___ master suggest?`
8. `What would this ___ / ___ master suggest?`
9. `What would this ___ / ___ master suggest?`

## Files to Update
- `.agents/skills/tts-cli/SKILL.md`: Frontmatter description, 6 deterministic + 3 custom chairs.
- `tts_cli/cli.py`: Update `DETERMINISTIC_MASTERS`, `SLASH_MASTERS`, `MASTER_QUESTIONS`, `NEXT_STEP_ONESHOT_PROMPT`.
- `AGENTS.md`: Update product goals, `<OUTPUT>` section, bash code block.
- `llms.txt`: Update speak contract and user preferences.
- `MCP_AUDIO_GUIDE.md`: Update reference table.
- `testing/`: Update all contract and CLI tests (`test_agents_output_contract.py`, `test_skill_cli_only.py`, `test_next_step_prompt.py`).
- `~/code/ainish-coder/.agents/skills/tts-cli/SKILL.md`: Copy byte-identical skill.

## Verification
- `python3 -m pytest testing/ -q` passes 100%.
- `python3 -m tts_cli.cli --next-step-prompt` outputs the 6+3 questions.
