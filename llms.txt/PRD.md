# Product Requirements Document (PRD)

## Project Overview

- **Name:** TTS CLI
- **Version:** 2.0.0
- **Description:** A modern, clean command-line Text-to-Speech tool designed for local execution with isolated environments. It leverages the `uv` package manager to ensure dependency isolation for different TTS models.
- **Purpose:** To provide a fast, privacy-focused, and easy-to-use TTS solution that runs efficiently on consumer hardware (CPU-optimized) without relying on cloud APIs.
- **UX:** Command Line Interface (CLI).

## Key Features

1.  **IndexTTS-2.5 (Sole Engine)**:
    *   Industrial-level zero-shot voice cloning (bilibili IndexTeam), 0.8B params.
    *   Multilingual: Chinese, English, Japanese, Spanish, Arabic (`--lang`).
    *   Emotion control, speaking-speed control (`duration_factor`), pronunciation control (Pinyin / CMU / Kana).
    *   Selected via `--model index-tts` (or `--model auto`, an alias). Requires an accelerator (CUDA/MPS/XPU) + downloaded checkpoints; Apple Silicon MPS is supported.
    *   Runs in an isolated Python 3.11 `uv` environment (IndexTTS requires `<3.12` while the host targets `>=3.12`); the adapter talks to it via subprocess with stdin-JSON (no command injection).
    *   Maintains the stable CLI contract (`--text`, file output, autoplayer).
2.  **Voice Cloning**:
    *   Clone voices using a single reference audio file.
    *   Supports any clean WAV file as input.
    *   Auto-play functionality for cloned voices.
3.  **Persistent Custom Voices**:
    *   **Repository-based Storage**: Custom voices are stored in `custom_voices/` at the project root for portability.
    *   **Auto-Cleaning**: Importing a voice (`--set-clone-voice`) automatically isolates vocals and removes silence.
    *   **Easy Management**: List, select, and unset custom voices via CLI commands.
4.  **Isolated Environments**:
    *   The engine runs in its own `uv` virtual environment.
    *   Prevents dependency hell (e.g. conflicting torch versions).
    *   Automatic creation and management of environments.
5.  **Robust Processing**:
    *   **Text Splitting**: Automatically chunks long text input to prevent memory errors and improve synthesis quality.
    *   **Voice Trimming**: Automatically trims reference audio > 10s to prevent hallucinations.
    *   **Tensor Validation**: Ensures model outputs are valid before saving.
6.  **Smart Audio Management**:
    *   **Auto-Playback**: Automatically plays generated audio by default.
    *   **Caching**: If no output path is specified, saves to `~/.tts-cli/cache/` with rotation.
    *   **Format**: Ensures all output is 16-bit PCM WAV for maximum compatibility.
7.  **Input Flexibility**:
    *   Text argument (`--text`).
    *   Clipboard content (`--clipboard`).
    *   Text file input (`--input-file`).

## Compatibility Contract (Downstream Integrations)

This CLI is used as a speech backend by other agentic tools (e.g. YOLO Mode). Maintain:
- `tts-cli --text "<msg>"` must work and remain stable.
- Non-zero exit codes should be reserved for hard failures.
- Output should stay quiet by default (no logs on stdout unless requested).

## Model Roadmap (2026)

IndexTTS-2.5 is the sole engine. Future candidates (not yet integrated):
- **Kokoro-82M** (Apache-2.0, open-weight): https://huggingface.co/hexgrad/Kokoro-82M
- **Piper** (fast local neural TTS, CLI + ONNX voices): https://github.com/bit-r/piper-TTS

## Architecture

- **Core CLI (`cli.py`)**: The main entry point handling argument parsing and orchestration.
- **Model Registry (`core/model_registry.py`)**: Manages available TTS models.
- **Environment Manager (`core/environment_manager.py`)**: Handles `uv` environment creation, execution, and cleanup. Per-model Python version pinning (e.g. IndexTTS → 3.11).
- **Model Implementations**:
    *   `IndexTTSModel`: IndexTTS-2.5, the sole engine — GPU/MPS multilingual zero-shot voice cloning. Runs in an isolated Python 3.11 env via subprocess; user input passed via stdin JSON (`shell=False`, no command injection). `check_availability()` gates on env + checkpoints + accelerator and reports the specific gap with an actionable hint.

## Critical Constraints

- **Model Scope**: IndexTTS-2.5 is the sole engine. Dependencies isolated in a `uv` env (Python 3.11). Legacy CPU engines (KittenTTS, PocketTTS, Hybrid) and the PocketTTS-specific model daemon have been removed.
- **Security**: Zero Trust principles, input validation, and safe file handling. Subprocess calls use `shell=False` and pass user input via stdin JSON (no command injection).
- **Performance**: IndexTTS-2.5 requires an accelerator (CUDA/MPS/XPU — Apple Silicon MPS supported) and downloaded checkpoints. There is no CPU fallback engine; on a machine without an accelerator, `cli-tts` reports unavailable with an actionable message rather than silently degrading.
