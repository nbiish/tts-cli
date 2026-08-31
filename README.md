# TTS CLI - Command-Line Text-to-Speech Tool

<div align="center">
  <hr width="50%">
  <h3>Support This Project</h3>
  <table style="border: none; border-collapse: collapse;">
    <tr style="border: none;">
      <td align="center" style="border: none; vertical-align: middle; padding: 20px;">
        <h4>Stripe</h4>
        <img src="qr-stripe-donation.png" alt="Scan to donate" width="180"/>
        <p><a href="https://raw.githubusercontent.com/nbiish/license-for-all-works/8e9b73b269add9161dc04bbdd79f818c40fca14e/qr-stripe-donation.png">Donate via Stripe</a></p>
      </td>
      <td align="center" style="border: none; vertical-align: middle; padding: 20px;">
        <a href="https://www.buymeacoffee.com/nbiish">
          <img src="buy-me-a-coffee.svg" alt="Buy me a coffee" />
        </a>
      </td>
    </tr>
  </table>
  <hr width="50%">
</div>

A modern, clean command-line TTS tool with isolated environments using the `uv` package manager. Each TTS tool runs in its own isolated environment to prevent dependency conflicts.

**🌍 Use from anywhere on your system** - Once installed, the `cli-tts` command works from any directory!

## 🚀 **Quick Start**

```bash
# Clone and setup (keeps everything centralized)
git clone https://github.com/nbiish/tts-cli.git
cd tts-cli
./setup-global.sh

# Use from anywhere!
cd /tmp
cli-tts --text "Hello world" --output speech.wav
```

**🎯 Centralized Design**: All model environments stay in the repo directory - no cluttering your system! Changes are immediately available everywhere.

## ⚠️ **CRITICAL IMPLEMENTATION SCOPE**

**WE IMPLEMENT THE FOLLOWING ENGINE - NO EXCEPTIONS:**

1. **KittenTTS nano int8** (KittenML) - Ultra-lightweight CPU ONNX TTS. The fastest engine on this machine (cold ~7.9s, RTF ~0.47) and the most portable (no accelerator; macOS/Linux/Windows/WSL). Fixed built-in voices (no zero-shot cloning).

**IMPLEMENTATION RULE:** `kitten-tts-nano` is the sole engine (`auto` is an alias). It runs one-shot in an isolated `uv` env (Python 3.11) and fully unloads from RAM after each call.

## 🚀 **Current Status**

### ✅ **Complete - Core Infrastructure & KittenTTS**
- **Core CLI Infrastructure**: Complete tiered architecture implemented
- **Environment Management**: UV-based isolated environments working (per-model Python pinning — KittenTTS → 3.11)
- **Model Registry**: Dynamic model loading and registration system
- **KittenTTS Implementation**: Ultra-lightweight CPU ONNX TTS (fixed voices) - **SOLE ENGINE**
- **Audio Generation**: Working audio output with auto-playback
- **Voice Management**: Built-in voice selection (`--voice`)
- **CLI Interface**: Full command-line interface operational

## ✨ Features

- **⚡ CPU Inference**: KittenTTS runs on CPU — no GPU/MPS required (Apple Silicon, Linux, Windows, WSL)
- **🔒 Isolated Environments**: The engine runs in its own UV environment (Python 3.11)
- **🎵 Built-in Voices**: 8 fixed voices (e.g. `expr-voice-5-m`); select with `--voice`
- **📋 Clipboard | Text | Text File | Pipe Support**: Flexible input methods
- **🔊 Auto-Playback**: Automatically plays generated audio
- **💾 Smart Caching**: Auto-manages output files with rotation
- **🔄 Cross-Platform**: Works on macOS, Linux, and Windows

## Usage

### Basic Text-to-Speech

```bash
# Generate speech from text (plays automatically)
cli-tts "Hello world"

# Or use explicit flag
cli-tts --text "Hello world"

# Save to specific file (also plays)
cli-tts "Hello world" --output hello.wav

# Use a specific built-in voice (default: expr-voice-5-m)
cli-tts "Hello world" --voice expr-voice-5-m

# List all built-in voices
cli-tts --list-voices
```

### Advanced Input Methods

```bash
# Read from clipboard
cli-tts --clipboard

# Piped input (works with any command)
echo "Hello from pipe" | cli-tts
cat story.txt | cli-tts
```

### Voices

KittenTTS ships 8 fixed built-in voices (no zero-shot cloning). Select one with `--voice`:

```bash
# Use a specific built-in voice
cli-tts --text "Hello world" --voice expr-voice-2-f

# List all voices
cli-tts --list-voices
```

### Audio Processing Tools
The CLI includes powerful tools to clean and process audio files independently.

**Prerequisite:** Create the audio processing environment:
```bash
cli-tts --create-environment audio-processing
```

**Commands:**
```bash
# 🧹 Full Cleanup (Demucs + VAD) - Best for voice cloning prep
cli-tts --clean-voice input.wav --output cleaned.wav

# 🎤 Isolate Vocals (Demucs) - Remove background music/noise
cli-tts --isolate-voice input.wav --output vocals.wav

# 🔇 Remove Silence (VAD) - Trim silence between speech
cli-tts --remove-silence input.wav --output trimmed.wav
```

### Environment Management

```bash
# Create environment (Required first time)
cli-tts --create-environment kitten-tts   # sole engine (CPU, fixed voices)

# List available models
cli-tts --list

# Remove environment
cli-tts --cleanup-environment kitten-tts
```

## 🤖 Available Models

### 1. KittenTTS nano int8 (KittenML) — SOLE ENGINE (`auto` / `kitten-tts-nano`)
- **Speed**: ⚡ Fastest on this machine — cold ~7.9s, RTF ~0.47 (Apple Silicon CPU).
- **Quality**: ✅ Natural speech from 8 fixed built-in voices (no zero-shot cloning)
- **Features**: Ultra-lightweight (15M / 25MB), CPU-only (no accelerator), cross-platform, English
- **Voices**: 8 built-in voices (`expr-voice-2..5` m/f); select with `--voice` (default `expr-voice-5-m`); `cli-tts --list-voices`
- **Implementation**: KittenTTS, runs in an isolated Python 3.11 `uv` env via subprocess
- **Requirements**: None (CPU). Weights download from HF on first run.
- **Best for**: Fast, portable agent voice summaries on any OS without an accelerator.

### 2. Audio Processing Tools (Demucs & VAD)
- **Demucs**: Hybrid Transformer for state-of-the-art music source separation (isolates vocals).
- **Silero VAD**: Enterprise-grade Voice Activity Detection to remove silence.
- **Use Case**: Cleaning noisy audio for voice cloning datasets.

## 🔧 First-Time Setup

1. **Install the CLI**:
   ```bash
   python setup-cli.py
   ```

2. **Create environment**:
   ```bash
   cli-tts --create-environment kitten-tts   # sole engine
   ```

3. **Test it works**:
   ```bash
   cli-tts --text "Test"
   ```

## 🏗️ Architecture

The TTS CLI uses a clean, modular architecture:

```
TTS CLI
├── CLI Interface (cli.py)
├── Model Registry (core/model_registry.py)
├── Environment Manager (core/environment_manager.py)
└── Model Implementations
    └── KittenTTSModel      (KittenTTS nano int8, sole engine)
```

### Environment Isolation

The engine runs in its own isolated UV environment:

```
.model-envs/
└── kitten-tts-env/
    └── .venv/   (Python 3.11 + kittentts + onnxruntime)
```


This prevents dependency conflicts between different models and ensures clean, reproducible environments.

## 🐛 Troubleshooting

### Common Issues

**"UV not found" error**:
```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**"Environment not found" error**:
```bash
# Create the required environment
cli-tts --create-environment MODEL_NAME
```

**"Model not working" error**:
```bash
# Test the model
cli-tts --test-model MODEL_NAME

# Recreate the environment if needed
cli-tts --cleanup-environment MODEL_NAME
cli-tts --create-environment MODEL_NAME
```

### Getting Help

```bash
# Show help
cli-tts --help

# List available models
cli-tts --list-models

# List environment status
cli-tts --list-environments
```

## 📚 Examples

### Quick Examples

```bash
# 1. Copy text to clipboard, then run:
echo "Your text here" | pbcopy
cli-tts --clipboard --output speech.wav

# 2. Direct text input:
cli-tts --text "Hello, this is a test of the TTS CLI tool" --output test.wav

# 3. Streamlined agent entry (--prompt is an alias for --text):
cli-tts --prompt "Task done. Next step: pin the Hugging Face kitten weights by digest before the next environment create." --output agent.wav

# 4. Choose a built-in voice:
cli-tts --text "Hello world" --voice expr-voice-2-f --output voice.wav

# 5. Set/check the default model:
cli-tts --set-default kitten-tts-nano
cli-tts --list

# 6. Debug mode:
cli-tts --debug --text "Test" --output debug.wav --log debug.log
```

## Citation

```bibtex
@misc{tts-cli2026,
  author/creator/steward = {ᓂᐲᔥ ᐙᐸᓂᒥᑮ-ᑭᓇᐙᐸᑭᓯ (Nbiish Waabanimikii-Kinawaabakizi), also known legally as JUSTIN PAUL KENWABIKISE, professionally documented as Nbiish-Justin Paul Kenwabikise, Anishinaabek Dodem (Anishinaabe Clan): Animikii (Thunder), descendant of Chief ᑭᓇᐙᐸᑭᓯ (Kinwaabakizi) of the Beaver Island Band and enrolled member of the sovereign Grand Traverse Band of Ottawa and Chippewa Indians},
  title/description = {tts-cli},
  type_of_work = {Indigenous digital creation/software incorporating traditional knowledge and cultural expressions},
  year = {2026},
  publisher/source/event = {GitHub repository under tribal sovereignty protections},
  howpublished = {\url{https://github.com/nbiish/tts-cli}},
  note = {Authored and stewarded by ᓂᐲᔥ ᐙᐸᓂᒥᑮ-ᑭᓇᐙᐸᑭᓯ (Nbiish Waabanimikii-Kinawaabakizi), also known legally as JUSTIN PAUL KENWABIKISE, professionally documented as Nbiish-Justin Paul Kenwabikise, Anishinaabek Dodem (Anishinaabe Clan): Animikii (Thunder), descendant of Chief ᑭᓇᐙᐸᑭᓯ (Kinwaabakizi) of the Beaver Island Band and enrolled member of the sovereign Grand Traverse Band of Ottawa and Chippewa Indians. This work embodies Indigenous intellectual property, traditional knowledge systems (TK), traditional cultural expressions (TCEs), and associated data protected under tribal law, federal Indian law, treaty rights, Indigenous Data Sovereignty principles, and international indigenous rights frameworks including UNDRIP. All usage, benefit-sharing, and data governance are governed by the COMPREHENSIVE RESTRICTED USE LICENSE FOR INDIGENOUS CREATIONS WITH TRIBAL SOVEREIGNTY, DATA SOVEREIGNTY, AND WEALTH RECLAMATION PROTECTIONS.}
}
```

## Copyright

Copyright © 2026 ᓂᐲᔥ ᐙᐸᓂᒥᑮ-ᑭᓇᐙᐸᑭᓯ (Nbiish Waabanimikii-Kinawaabakizi), also known legally as JUSTIN PAUL KENWABIKISE, professionally documented as Nbiish-Justin Paul Kenwabikise, Anishinaabek Dodem (Anishinaabe Clan): Animikii (Thunder), a descendant of Chief ᑭᓇᐙᐸᑭᓯ (Kinwaabakizi) of the Beaver Island Band, and an enrolled member of the sovereign Grand Traverse Band of Ottawa and Chippewa Indians. This work embodies Traditional Knowledge and Traditional Cultural Expressions. All rights reserved.
