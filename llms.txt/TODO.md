# TODO List

## Completed Tasks

- [x] **Core Infrastructure**:
    - [x] Basic CLI structure with `argparse`.
    - [x] `uv` integration for environment management.
    - [x] Tiered architecture (CLI -> Registry -> Environment Manager -> Model).

- [x] **Pocket TTS Implementation**:
    - [x] Model integration (`PocketTTSModel`).
    - [x] Environment creation with `pocket-tts` and `scipy`.
    - [x] Basic speech generation.

- [x] **Voice Cloning**:
    - [x] Support for reference audio input (`--voice-clone`).
    - [x] Audio format normalization (converting float32 to int16 WAV).
    - [x] Auto-generation of default text if none provided.

- [x] **Audio Management**:
    - [x] Auto-playback on all platforms (macOS, Linux, Windows).
    - [x] Caching system in `~/.tts-cli/cache/`.
    - [x] Fallback to system temp directory if cache is not writable.
    - [x] Automatic cache rotation (limit: 9 files).

- [x] **Cleanup**:
    - [x] Removal of legacy models (Coqui, Edge, VibeVoice, Zonos).
    - [x] Streamlining of `README.md` and installation guides.

- [x] **Stability & Migration**:
    - [x] Implement robust text splitting (chunking) for long inputs.
    - [x] Add automatic voice file trimming (>10s) to prevent hallucinations.
    - [x] Enhance tensor validation to prevent crashes.
    - [x] Align architecture with `local-tts-mcp` best practices.

## Pending / Future Tasks

- [x] **IndexTTS-2.5 Engine (2026-08-31)**:
    - [x] Add `IndexTTSModel` adapter (`tts_cli/models/index_tts_model.py`).
    - [x] Register `index-tts` in CLI; add `--lang` flag (ZH/EN/JA/ES/AR).
    - [x] Isolated Python 3.11 `uv` env config (IndexTTS requires `<3.12`).
    - [x] Gate behind `check_availability()` (accelerator + checkpoints); hybrid router skips it on CPU.
    - [x] Fix `.gitignore` bare `models/` rule that was silently ignoring `tts_cli/models/*`.
    - [ ] End-to-end test on a GPU/MPS host with downloaded checkpoints (deferred — needs hardware).
    - [ ] Optional: wire emotion/speed kwargs (`emo_alpha`, `duration_factor`) into CLI flags.

- [ ] **Testing**:
    - [ ] Add unit tests for `VoiceManager`.
    40|    - [ ] Add integration tests for full CLI workflow.
    - [ ] Add specific tests for voice cloning edge cases (e.g., corrupted audio files).
    - [ ] Add unit tests for `IndexTTSModel` availability gating (mocked env/torch/checkpoints).

- [ ] **Features**:
    - [ ] Add `--no-play` flag to optionally disable auto-playback.
    - [ ] Add support for custom output formats (mp3, etc.) - *Low Priority*.
    - [ ] Add a simple TUI (Text User Interface) for selecting voices/models.

- [ ] **Documentation**:
    - [ ] Create a dedicated `VOICE_CLONING.md` guide.
    - [ ] Update `CONTRIBUTING.md` with new architectural details.
