# Product Requirements Document (PRD)

## Project Overview

- **Name:** TTS CLI
- **Version:** 2.0.0
- **Description:** A modern, clean command-line Text-to-Speech tool designed for local execution with isolated environments. It leverages the `uv` package manager to ensure dependency isolation for different TTS models.
- **Purpose:** To provide a fast, privacy-focused, and easy-to-use TTS solution that runs efficiently on consumer hardware (CPU-optimized) without relying on cloud APIs.
- **UX:** Command Line Interface (CLI).

## Key Features

1.  **Hybrid TTS (Default)**:
    *   Uses a fast default engine for short/medium prompts, with automatic fallback for robustness.
    *   Maintains a stable CLI contract (`--text`, file output, autoplayer).
2.  **Pocket TTS (Fallback Engine)**:
    *   Lightweight, CPU-optimized text-to-speech for long text and reliability.
    *   High-quality natural speech.
2.  **Voice Cloning**:
    *   Clone voices using a single reference audio file.
    *   Supports any clean WAV file as input.
    *   Auto-play functionality for cloned voices.
3.  **IndexTTS-2.5 (Optional GPU/MPS Engine)**:
    *   Industrial-level zero-shot voice cloning (bilibili IndexTeam).
    *   Multilingual: Chinese, English, Japanese, Spanish, Arabic (`--lang`).
    *   Emotion control, speaking-speed control (`duration_factor`), pronunciation control (Pinyin / CMU / Kana).
    *   **Opt-in** via `--model index-tts`; gated by accelerator availability (CUDA/MPS/XPU) + checkpoints.
    *   CPU-first default contract preserved: hybrid `auto` router skips it on CPU-only machines.
    *   Runs in an isolated Python 3.11 `uv` environment (IndexTTS requires `<3.12`).
3.  **Persistent Custom Voices**:
    *   **Repository-based Storage**: Custom voices are stored in `custom_voices/` at the project root for portability.
    *   **Auto-Cleaning**: Importing a voice (`--set-clone-voice`) automatically isolates vocals and removes silence.
    *   **Easy Management**: List, select, and unset custom voices via CLI commands.
4.  **Isolated Environments**:
    *   Each model runs in its own `uv` virtual environment.
    *   Prevents dependency hell (e.g., conflicting torch versions).
    *   Automatic creation and management of environments.
5.  **Robust Processing**:
    *   **Text Splitting**: Automatically chunks long text input to prevent memory errors and improve synthesis quality.
    *   **Voice Trimming**: Automatically trims reference audio > 10s to prevent hallucinations.
    *   **Tensor Validation**: Ensures model outputs are valid before saving.
6.  **Smart Audio Management**:
    *   **Auto-Playback**: Automatically plays generated audio by default.
    *   **Caching**: If no output path is specified, saves to `~/.tts-cli/cache/` with rotation.
    *   **Format**: Ensures all output is 16-bit PCM WAV for maximum compatibility.
5.  **Input Flexibility**:
    *   Text argument (`--text`).
    *   Clipboard content (`--clipboard`).
    *   Text file input (`--input-file`).

## Compatibility Contract (Downstream Integrations)

This CLI is used as a speech backend by other agentic tools (e.g. YOLO Mode). Maintain:
- `tts-cli --text "<msg>"` must work and remain stable.
- Non-zero exit codes should be reserved for hard failures.
- Output should stay quiet by default (no logs on stdout unless requested).

## Model Roadmap (2026)

When adding engines, prefer open, local-first options with permissive licensing:
- **IndexTTS-2.5** (bilibili Model Use License) — ✅ added as opt-in GPU/MPS engine (`--model index-tts`).
- **Kokoro-82M** (Apache-2.0, open-weight): https://huggingface.co/hexgrad/Kokoro-82M
- **Piper** (fast local neural TTS, CLI + ONNX voices): https://github.com/bit-r/piper-TTS

## Architecture

- **Core CLI (`cli.py`)**: The main entry point handling argument parsing and orchestration.
- **Model Registry (`core/model_registry.py`)**: Manages available TTS models.
- **Environment Manager (`core/environment_manager.py`)**: Handles `uv` environment creation, execution, and cleanup. Per-model Python version pinning (e.g. IndexTTS → 3.11).
- **Model Implementations**:
    *   `HybridTTSModel`: Default `auto` router — KittenTTS first, PocketTTS fallback. Skips unavailable engines (e.g. IndexTTS on CPU-only machines).
    *   `KittenTTSModel`: Fast CPU-optimized TTS, 8 expressive voices.
    *   `PocketTTSModel`: Kyutai Pocket TTS, CPU voice cloning.
    *   `IndexTTSModel`: IndexTTS-2.5, opt-in GPU/MPS multilingual zero-shot voice cloning. Runs in an isolated Python 3.11 env via subprocess; gated by `check_availability()`.

## Critical Constraints

- **Model Scope**: Local-first engines only; keep dependencies isolated per engine with `uv`. Default path stays CPU-first; GPU-class engines (IndexTTS) are opt-in and gated by availability.
- **Security**: Zero Trust principles, input validation, and safe file handling. Subprocess calls use `shell=False` and pass user input via stdin JSON (no command injection).
- **Performance**: Core/default path optimized for CPU execution; no GPU required for default functionality. IndexTTS requires an accelerator (CUDA/MPS/XPU) and downloaded checkpoints.
