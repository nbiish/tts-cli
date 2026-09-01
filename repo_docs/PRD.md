# Product Requirements Document (PRD)

## Project Overview

- **Name:** TTS CLI
- **Version:** 2.0.0
- **Description:** A modern, clean command-line Text-to-Speech tool designed for local execution with isolated environments. It leverages the `uv` package manager to ensure dependency isolation for different TTS models.
- **Purpose:** To provide a fast, privacy-focused, and easy-to-use TTS solution that runs efficiently on consumer hardware (CPU-optimized) without relying on cloud APIs.
- **UX:** Command Line Interface (CLI) today. Long-term: a Rust mixer GUI that pops up for tts-cli, watches tts-cli PIDs, queues every agent play as a skippable track list, owns volume for those plays, and sets the permanent WAV generate speed for all tts-cli calls (see `.agents/tasks/TASK.2026-09-01.tts-mixer-gui.md`). Agent speak is CLI-owned 1.8× + random voice.

## Key Features

1.  **IndexTTS-2.5 — Two-Tier Engine (Sole Family)**:
    *   Industrial-level zero-shot voice cloning (bilibili IndexTeam), 0.8B params.
    *   Multilingual: Chinese, English, Japanese, Spanish, Arabic (`--lang`).
    *   **Fast default** (`--model index-tts` / `--model auto`): IndexTTS-2.5 quantized to **Q8 GGUF**, run through `audiocpp_cli` (audio.cpp) on **Metal**. Cold ~43s, RTF ~5.1 on Apple Silicon. No daemon — the subprocess exits after each call, fully releasing RAM/VRAM.
    *   **Quality tier** (`--quality`): full-precision Python IndexTTS-2.5 on **MPS**. Cold ~142s, RTF ~17.2. Full dtype, higher quality. Same no-daemon / unload-on-exit contract.
    *   Both tiers are one-shot subprocesses: cold load → synthesize → write WAV → exit → release all memory. No model state is held between calls.
    *   Emotion control, speaking-speed control (`duration_factor`), pronunciation control (Pinyin / CMU / Kana) on the quality tier.
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
    *   `IndexTTSGGUFModel`: IndexTTS-2.5 **Q8 GGUF** via `audiocpp_cli` (audio.cpp) on Metal — the **fast default** (`index-tts` / `auto`). One-shot subprocess that exits after each call (no daemon, no RAM/VRAM held). `check_availability()` gates on `audiocpp_cli` + the GGUF file + Metal.
    *   `IndexTTSModel`: full-precision Python IndexTTS-2.5 on MPS — the **quality tier** (`index-tts-quality`, selected via `--quality`). Runs in an isolated Python 3.11 env via subprocess with stdin-JSON (`shell=False`, no command injection). Same unload-on-exit contract.

## Critical Constraints

- **Model Scope**: IndexTTS-2.5 is the sole engine. Dependencies isolated in a `uv` env (Python 3.11). Legacy CPU engines (KittenTTS, PocketTTS, Hybrid) and the PocketTTS-specific model daemon have been removed.
- **Security**: Zero Trust principles, input validation, and safe file handling. Subprocess calls use `shell=False` and pass user input via stdin JSON (no command injection).
- **Performance**: IndexTTS-2.5 requires an accelerator (CUDA/MPS/XPU — Apple Silicon MPS supported) and downloaded checkpoints. There is no CPU fallback engine; on a machine without an accelerator, `cli-tts` reports unavailable with an actionable message rather than silently degrading.
