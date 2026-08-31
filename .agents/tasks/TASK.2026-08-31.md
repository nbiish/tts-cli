# TASK: Add IndexTTS-2.5 as optional GPU engine

**Date:** 2026-08-31
**Branch:** `feat/index-tts-engine`
**Worktree:** `../index-tts-engine`
**Classification:** Confidential

## Objective

Add IndexTTS-2.5 (https://github.com/index-tts/index-tts) as a new optional TTS engine
alongside the existing KittenTTS / PocketTTS / Hybrid stack. The engine is **opt-in** via
`--model index-tts` and gated by hardware availability so the default CPU-first contract is
preserved.

## Decisions (confirmed with operator)

1. **Intent:** Add as a new optional engine (not replace, not default).
2. **Version:** IndexTTS-2.5 (latest, multilingual: ZH/EN/JA/ES/AR).
3. **GPU handling:** Gate behind `--model index-tts`; `check_availability()` reports False
   without an accelerator (CUDA/MPS) + checkpoints. Hybrid auto-router skips it. No change
   to the default CPU contract.

## Constraints & Notes

- **Python conflict:** IndexTTS requires `>=3.10,<3.12`; tts-cli requires `>=3.12`.
  IndexTTS runs in an isolated uv env pinned to Python 3.11 (env_manager already supports a
  `python_version` param). The adapter talks to it via subprocess (same pattern as
  KittenTTSModel's `_generate_in_environment`).
- **Hardware:** IndexTTS-2.5 supports CUDA (cu128), MPS (Apple Silicon), and CPU (slow).
  `check_availability()` requires the isolated env to exist AND torch to report an accelerator
  (cuda/mps/xpu). Pure-CPU machines report unavailable → hybrid router skips it.
- **API:** `from indextts.infer_v2_5 import IndexTTS2`;
  `tts.infer(spk_audio_prompt=<wav>, text=<str>, lang=<ZH|EN|JA|ES|AR>, output_path=<wav>)`
  writes 22050 Hz 16-bit PCM WAV directly to `output_path`.
- **Checkpoints:** User downloads `IndexTeam/IndexTTS-2.5` to `checkpoints/` (HF or ModelScope).
  The adapter locates `checkpoints/config.yaml` relative to the repo root and the
  `INDEX_TTS_MODEL_DIR` env var.
- **Stable backend contract:** `tts-cli --text "<msg>"` must remain unchanged. IndexTTS is
  only invoked when explicitly selected.

## Deliverables

- `tts_cli/models/index_tts_model.py` — IndexTTSModel adapter (BaseTTSModel).
- `tts_cli/models/__init__.py` — export IndexTTSModel.
- `tts_cli/cli.py` — register `index-tts`; add to `create_environment` configs; add `--lang`
  flag; pass `lang`/`voice_clone` through to generation.
- `llms.txt/PRD.md` — document the new engine + GPU-optional tier.
- `llms.txt/TODO.md` — mark engine-expansion item in progress.

## Verification

- `python -c "import ast; ast.parse(open('tts_cli/models/index_tts_model.py').read())"`
- `python -c "from tts_cli.models.index_tts_model import IndexTTSModel"` (import check).
- `cli-tts --list-models` shows `index-tts` (reports Not Available on CPU-only/no-env).
- `cli-tts --model index-tts --text "hi"` fails gracefully with a clear message when
  unavailable (no crash, no change to default `auto` path).

## Security

- No secrets. No `.env`. No hardcoded keys. IndexTTS is open-weight (bilibili Model Use
  License). Dependencies installed via uv in an isolated env (pinned by upstream `uv.lock`).
- Subprocess uses `shell=False` (list args). Text is passed via stdin to avoid command
  injection (no `python -c` with interpolated text).
