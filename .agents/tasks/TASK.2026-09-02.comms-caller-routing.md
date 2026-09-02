# TASK 2026-09-02 — Ensure AGENTS-TTS-COMMS.txt Outputs in Caller Terminal Location

**Branch:** `fix/comms-caller-routing`
**Worktree:** `../comms-caller-routing`
**Classification:** Confidential — no secrets

## Goal

Ensure `AGENTS-TTS-COMMS.txt` reliably outputs at the `.git` root of the calling project where `cli-tts` is invoked from, across detached child processes, without requiring agents to make directory decisions or pass extra arguments in their prompts.

## Requirements

1. **Explicit Argv Propagation**:
   - Add `--caller-dir` flag to `cli-tts`.
   - In parent `cli-tts --prompt`, resolve `caller_dir = args.caller_dir or os.environ.get("TTS_CLI_CALLER_DIR") or os.getcwd()`.
   - Propagate `--caller-dir <dir>` via `_detached_child_argv` so caller directory survives process detach, session detachment, and environment changes across all platforms.
2. **Backend Threading**:
   - Pass `caller_dir` through `generate_speech` to `_log_to_agents_tts_comms` and `read_last_suggestion`.
   - Pass `caller_dir` into `_comms_file(start_dir)` and `_find_repo_root(start_dir)`.
3. **Agent Skill Contract**:
   - Keep `.agents/skills/tts-cli/SKILL.md` clean and focused solely on prompting without requiring the agent to manage paths or options.
   - Transparent automatic routing handled entirely by backend.
4. **Merge Conflict Resolution**:
   - Cleanly resolve merge conflicts in `AGENTS-TTS-COMMS.txt` preserving entries in chronological order.
5. **Testing**:
   - Unit tests covering `--caller-dir` priority over env var, argv propagation, and caller-specific ledger routing.
   - End-to-end integration test verifying that detached generation from a nested project directory outputs to that project's `.git` root.
