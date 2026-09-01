# TASK 2026-09-01 — Route AGENTS-TTS-COMMS.txt to Caller Repository Root

**Branch:** `feat/comms-caller-repo-root`
**Worktree:** `../tts-cli-comms-caller-repo-root`
**Classification:** Confidential — no secrets

## Goal

Make `AGENTS-TTS-COMMS.txt` dynamic to the caller repository root from which `cli-tts`
is invoked, rather than writing strictly to the `tts-cli` package repository.
This allows agents and operators across multiple separate repositories to track, review,
and reference their own project-specific suggestion transcripts and context.

## Requirements

1. **Repo Root Resolution**:
   - Resolve caller working directory via `os.environ.get("TTS_CLI_CALLER_DIR")` or `Path.cwd()`.
   - Find repository root via `git rev-parse --show-toplevel` with fallback filesystem traversal for `.git` (directory or file).
   - If outside a git repository, fallback to caller working directory.
2. **Dynamic Ledger Path**:
   - `_comms_file()` returns `<resolved_repo_root>/AGENTS-TTS-COMMS.txt`.
   - `read_last_suggestion()` reads from `<resolved_repo_root>/AGENTS-TTS-COMMS.txt`.
3. **Auto-Header on Creation**:
   - When writing to a newly created `AGENTS-TTS-COMMS.txt` in a project, write the canonical header comments before appending the first entry.
4. **Detached Child Preservation**:
   - Ensure detached child process spawned by parent `cli-tts --prompt` preserves caller directory and inherits `TTS_CLI_CALLER_DIR`.
5. **Global Wrapper CWD Preservation**:
   - `scripts/tts-cli-global.sh` uses `uv --project "$PROJECT_ROOT"` and exports `TTS_CLI_CALLER_DIR="$PWD"` instead of `cd "$PROJECT_ROOT"`.
6. **Testing**:
   - Unit tests covering git root, subdirectory, worktree, non-git dir, env override, auto-header creation, and `read_last_suggestion`.
