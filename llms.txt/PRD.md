# Product Requirements Document (PRD)

## Project Overview

- **Name:** TTS CLI
- **Version:** 2.0.0
- **Description:** A modern, clean command-line Text-to-Speech tool designed for local execution with isolated environments. It leverages the `uv` package manager to ensure dependency isolation for different TTS models.
- **Purpose:** To provide a fast, privacy-focused, and easy-to-use TTS solution that runs efficiently on consumer hardware (CPU-optimized) without relying on cloud APIs.
- **UX:** Command Line Interface (CLI).

## Key Features

1.  **Pocket TTS (Default Model)**:
    *   Lightweight, CPU-optimized text-to-speech.
    *   Faster than real-time generation.
    *   High-quality natural speech.
2.  **Voice Cloning**:
    *   Clone voices using a single reference audio file.
    *   Supports any clean WAV file as input.
    *   Auto-play functionality for cloned voices.
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

## Architecture

- **Core CLI (`cli.py`)**: The main entry point handling argument parsing and orchestration.
- **Model Registry (`core/model_registry.py`)**: Manages available TTS models.
- **Environment Manager (`core/environment_manager.py`)**: Handles `uv` environment creation, execution, and cleanup.
- **Model Implementations**:
    *   `PocketTTSModel`: Adapter for the Kyutai Pocket TTS library.

## Critical Constraints

- **Model Scope**: STRICTLY limited to **Pocket TTS** implementation.
- **Security**: Zero Trust principles, input validation, and safe file handling.
- **Performance**: Optimized for CPU execution; no GPU requirements for core functionality.
