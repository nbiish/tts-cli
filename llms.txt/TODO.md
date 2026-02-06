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

## Pending / Future Tasks

- [ ] **Testing**:
    - [ ] Add unit tests for `VoiceManager`.
    - [ ] Add integration tests for full CLI workflow.
    - [ ] Add specific tests for voice cloning edge cases (e.g., corrupted audio files).

- [ ] **Features**:
    - [ ] Add `--no-play` flag to optionally disable auto-playback.
    - [ ] Add support for custom output formats (mp3, etc.) - *Low Priority*.
    - [ ] Add a simple TUI (Text User Interface) for selecting voices/models.

- [ ] **Documentation**:
    - [ ] Create a dedicated `VOICE_CLONING.md` guide.
    - [ ] Update `CONTRIBUTING.md` with new architectural details.
