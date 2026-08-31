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
    - [x] Research: Evaluate KittenTTS vs PocketTTS performance (See `RESEARCH_NOTES.md`).

- [x] **KittenTTS Benchmarking (2026-02-22)**:
    - [x] Set up espeak-ng dependency for phonemization
    - [x] Create benchmark scripts for KittenTTS
    - [x] Test multiple voices (expr-voice-2-m, expr-voice-2-f, expr-voice-3-m, expr-voice-3-f)
    - [x] Verify audio output quality through playback
    - [x] Document performance metrics (RTF, speed, file sizes)
    - [x] Compare performance with PocketTTS

- [x] **Hybrid TTS Implementation (2026-02-22)**:
    - [x] Design hybrid architecture with automatic fallback
    - [x] Implement `KittenTTSModel` with timeout and error handling
    - [x] Implement `HybridTTSModel` with automatic fallback logic
    - [x] Update CLI to use hybrid model as default
    - [x] Add environment configuration for KittenTTS
    - [x] Document hybrid architecture in `HYBRID_TTS_ARCHITECTURE.md`

## Pending / Future Tasks

- [x] **IndexTTS-2.5 Engine (2026-08-31)**:
    - [x] Add `IndexTTSModel` adapter (`tts_cli/models/index_tts_model.py`).
    - [x] Register `index-tts` in CLI; add `--lang` flag (ZH/EN/JA/ES/AR).
    - [x] Isolated Python 3.11 `uv` env config (IndexTTS requires `<3.12`).
    - [x] Gate behind `check_availability()` (accelerator + checkpoints); hybrid router skips it on CPU.
    - [x] Fix `.gitignore` bare `models/` rule that was silently ignoring `tts_cli/models/*`.
    - [ ] End-to-end test on a GPU/MPS host with downloaded checkpoints (deferred — needs hardware).
    - [ ] Optional: wire emotion/speed kwargs (`emo_alpha`, `duration_factor`) into CLI flags.

- [ ] **Engine Expansion (2026)**:
    - [ ] Add Kokoro-82M as an optional engine (Apache-2.0): https://huggingface.co/hexgrad/Kokoro-82M
    - [ ] Add Piper as an optional engine (fast local CLI): https://github.com/bit-r/piper-TTS
    - [ ] Ensure all engines support the stable backend contract: `tts-cli --text "<msg>"`

- [ ] **Testing & Validation**:
    - [ ] Test hybrid model with short text (< 100 chars)
    - [ ] Test hybrid model with medium text (100-500 chars)
    - [ ] Test hybrid model with long text (> 500 chars) - should fallback to PocketTTS
    - [ ] Test voice cloning with hybrid model
    - [ ] Test timeout scenarios
    - [ ] Test espeak-ng missing scenario
    - [ ] Add unit tests for HybridTTSModel
    - [ ] Add integration tests for CLI with hybrid model
    - [ ] Add unit tests for `IndexTTSModel` availability gating (mocked env/torch/checkpoints).

- [ ] **Optimization**:
    - [ ] **High Priority**: Implement LRU caching for `voice_state` in `model_daemon.py`.
        - *Why*: Currently re-processes voice audio for every request (~1.9s latency). Caching will reduce warm inference to ~0.5s.
    - [ ] Optimize PocketTTS to make it more competitive with KittenTTS
    - [ ] Add performance metrics collection
    - [ ] Monitor fallback rates and reasons

- [ ] **Features**:
    - [ ] Add `--no-play` flag to optionally disable auto-playback.
    - [ ] Add support for custom output formats (mp3, etc.) - *Low Priority*.
    - [ ] Add a simple TUI (Text User Interface) for selecting voices/models.
    - [ ] Add `--verbose` flag for detailed fallback logging
    - [ ] Add fallback statistics reporting

- [ ] **Documentation**:
    - [ ] Update `README.md` with hybrid model information
    - [ ] Update `MODEL_EVALUATION_SUMMARY.md` with KittenTTS findings
    - [ ] Create voice selection guide explaining when to use each model
    - [ ] Update installation guide with espeak-ng requirements
    - [ ] Create troubleshooting guide for common issues

## Architecture Decision (2026-02-22)

**Decision**: Hybrid approach with KittenTTS as default and automatic PocketTTS fallback.

**Implementation Status**: ✅ **COMPLETED**

**What Was Implemented:**
1. **KittenTTSModel** - Full implementation with timeout and error handling
2. **HybridTTSModel** - Automatic fallback logic for all failure scenarios
3. **CLI Updates** - Default model changed to "auto" (hybrid)
4. **Environment Support** - KittenTTS environment configuration added

**How It Works:**
- Default command `cli-tts "text"` now uses KittenTTS (fast, ~10x real-time)
- Automatically falls back to PocketTTS when:
  - Text is too long (> 500 chars)
  - KittenTTS times out (> 60s)
  - KittenTTS encounters errors
  - Voice cloning is requested
  - espeak-ng is not available
- Users can still force specific models with `--model kitten-tts` or `--model pocket-tts`

**Performance:**
- Short text: KittenTTS (~1s generation, RTF 0.10)
- Medium text: KittenTTS (~2s generation, RTF 0.10)
- Long text: PocketTTS (~4-6s generation, RTF ~0.15)
- Voice cloning: PocketTTS (~8s generation)

**Next Steps:**
1. Test all fallback scenarios
2. Collect user feedback
3. Monitor performance metrics
4. Optimize based on real-world usage
