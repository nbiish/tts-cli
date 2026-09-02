# TASK — KittenTTS as the default main engine

- date: 2026-09-02
- branch: `feat/kitten-default-engine`
- worktree: `../kitten-default-engine`
- operator ask: "Let's make the kittentts the default main model for speed."

## Problem

The CLI is mid-migration. Help text, `README.md`, and `AGENTS.md <OUTPUT>` already
present `kitten-tts-nano` as the default (`auto` resolves to it), but the actual
resolution still lands on MOSS:

- `tts_cli/cli.py` `DEFAULT_MODEL_FALLBACK = "moss-tts-nano"` — the built-in
  fallback used by `get_default_model()` when neither `TTS_CLI_DEFAULT_MODEL`
  nor `~/.tts-cli/default_model` is set.
- `setup_models()` registers `auto` → `MossTTSModel` and labels MOSS "primary default".
- `AGENTS.md` (IDENTITY, PRODUCT GOALS), `llms.txt` (product contract), and
  `tts_cli/models/__init__.py` still call MOSS the primary default engine.

KittenTTS nano is the fastest engine on this machine (cold ~7.9s, RTF ~0.47,
15M int8, CPU ONNX), which is why the operator wants it as the default.

## Change

1. `tts_cli/cli.py`:
   - `DEFAULT_MODEL_FALLBACK = "kitten-tts-nano"` (the actual flip).
   - `SELECTABLE_MODELS` reordered, kitten first; MOSS stays selectable
     (`--model moss-tts-nano` / `--set-default moss-tts-nano`) — removal is
     out of scope.
   - `setup_models()` docstring + registry: kitten primary default, `auto`
     alias → `KittenTTSModel`; MOSS secondary zero-shot cloning engine.
   - Fix stale `get_default_model()` docstring (`pocket-tts` → `kitten-tts-nano`).
   - `--model` / `--set-default` help text name both engines with kitten default.
   - `--list` marks the default engine; `--diagnostics` groups Kitten (default)
     and MOSS (secondary).
2. `tts_cli/models/__init__.py` docstring: flip primary/secondary.
3. Docs (DOX pass): `llms.txt` product contract, `AGENTS.md` IDENTITY +
   PRODUCT GOALS, `README.md` "sole engine" wording → "default engine" with a
   short secondary MOSS section.
4. Tests: new `testing/test_default_model.py` locks the fallback, env override,
   config-file override, invalid-config fallback, and registry default alias.

## Constraints

- One task = one branch = one worktree; no direct commits to `main`.
- No banned crypto, no secrets touched (config file stores a model name only).
- Skill `.agents/skills/tts-cli/SKILL.md` is engine-agnostic — unchanged
  (byte-identity preserved; no `--sync-skills` needed).
- `llms.txt` is the PRD anchor: contract updated in the same change.

## Verification

- `python -m pytest testing/ -q` from the worktree — all green (95+ tests).
- `cli-tts --list` / `--diagnostics` show `kitten-tts-nano` as default
  (smoke-tested via the repo wrapper).

## Merge

Gates pass → ask operator to confirm merge → cleanup worktree + branch.
