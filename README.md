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

**WE IMPLEMENT THE FOLLOWING ENGINES - NO EXCEPTIONS:**

1. **PocketTTS** (Kyutai) - Fast default. Zero-shot voice cloning, cross-platform CPU (+ Apple Silicon MPS / CUDA). No accelerator required.
2. **IndexTTS-2.5** (bilibili IndexTeam) - Quality tier. Industrial-level zero-shot multilingual voice-cloning TTS (GPU/MPS).

**IMPLEMENTATION RULE:** PocketTTS is the fast default (`auto` / `pocket-tts`); IndexTTS-2.5 is the `--quality` tier (and `--model index-tts` for the GGUF path). All engines run one-shot in an isolated `uv` env and fully unload from RAM/VRAM after each call.

## 🚀 **Current Status**

### ✅ **Complete - Core Infrastructure & IndexTTS-2.5**
- **Core CLI Infrastructure**: Complete tiered architecture implemented
- **Environment Management**: UV-based isolated environments working (per-model Python pinning — IndexTTS → 3.11)
- **Model Registry**: Dynamic model loading and registration system
- **IndexTTS-2.5 Implementation**: Zero-shot multilingual voice-cloning TTS (GPU/MPS) - **SOLE ENGINE**
- **Audio Generation**: Working audio output with auto-playback
- **Voice Management**: Standard voices and voice cloning support
- **CLI Interface**: Full command-line interface operational

## ✨ Features

- **⚡ GPU/MPS Inference**: IndexTTS-2.5 runs on CUDA/MPS/XPU (Apple Silicon supported)
- **🔒 Isolated Environments**: The engine runs in its own UV environment (Python 3.11)
- **🌍 Multilingual**: Chinese, English, Japanese, Spanish, Arabic (`--lang`)
- **🎵 Voice Cloning**: Zero-shot voice cloning via a single reference audio file
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

# Use specific voice
cli-tts "Hello world" --voice alba
```

### Advanced Input Methods

```bash
# Read from clipboard
cli-tts --clipboard

# Piped input (works with any command)
echo "Hello from pipe" | cli-tts
cat story.txt | cli-tts
```

### Voice Cloning & Audio Cleaning
You can use a reference audio file to clone a voice. For best results, clean the audio first using our built-in tools.

```bash
# Basic voice cloning (one-off)
cli-tts --text "Hello world" --voice-clone reference.wav

# 🌟 Persistent Custom Voices
# Import a voice (copies to custom_voices/ as-is)
cli-tts --set-clone-voice path/to/my_voice.wav

# List available custom voices
cli-tts --list-clone-voices

# Switch to an existing custom voice
cli-tts --set-clone-voice my_voice.wav

# Unset custom voice (return to random/default)
cli-tts --unset-clone-voice
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
cli-tts --create-environment pocket-tts   # fast default (CPU + MPS/CUDA)
cli-tts --create-environment index-tts    # IndexTTS-2.5 quality tier

# List available models
cli-tts --list-models

# Remove environment
cli-tts --cleanup-environment pocket-tts
```

## 🤖 Available Models

### 1. PocketTTS (Kyutai) — FAST DEFAULT (`auto` / `pocket-tts`)
- **Speed**: ⚡ Fastest open zero-shot-cloning engine (2026 Picovoice benchmark: ~1.7s first-audio). Cold ~11.6s, RTF ~1.1 on Apple Silicon CPU.
- **Quality**: ✅ Natural zero-shot voice cloning from a single reference clip
- **Features**: Streaming, cross-platform CPU + MPS/CUDA, European languages (EN/ES/IT/DE/PT/FR)
- **Voice Cloning**: ✅ Zero-shot (single reference audio); bundled `examples/default_voice.wav` fallback
- **Implementation**: Kyutai PocketTTS, runs in an isolated Python 3.11 `uv` env via subprocess
- **Requirements**: None (CPU); optional MPS/CUDA for speed. Weights download from HF on first run.
- **Best for**: Fast agent voice summaries on any OS, zero-shot cloning without an accelerator.

### 2. IndexTTS-2.5 (bilibili IndexTeam) — QUALITY TIER (`--quality` / `index-tts` / `index-tts-quality`)
- **Speed**: `index-tts` (GGUF Q8 via audio.cpp, Metal/CUDA/Vulkan/CPU) cold ~43s; `index-tts-quality` (full Python, MPS/CUDA) cold ~142s
- **Quality**: ✅ Industrial-level natural speech, zero-shot voice cloning
- **Features**: Multilingual (ZH/EN/JA/ES/AR), emotion control, speaking-speed control, pronunciation control
- **Voice Cloning**: ✅ Zero-shot (single reference audio)
- **Implementation**: IndexTTS-2.5, runs in an isolated Python 3.11 `uv` env via subprocess
- **Requirements**: `index-tts` — audio.cpp + GGUF + backend; `index-tts-quality` — accelerator (CUDA/MPS/XPU) + checkpoints
- **Best for**: Highest-fidelity multilingual cloning on accelerated hardware

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
   cli-tts --create-environment pocket-tts   # fast default
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
    ├── PocketTTSModel      (PocketTTS, fast default)
    ├── IndexTTSGGUFModel   (IndexTTS-2.5 GGUF, audio.cpp)
    └── IndexTTSModel       (IndexTTS-2.5, quality tier)
```

### Environment Isolation

The engine runs in its own isolated UV environment:

```
.model-envs/
└── index-tts-env/
    └── .venv/   (Python 3.11 + indextts)
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

# 3. Voice cloning workflow (zero-shot, single reference):
cli-tts --text "This is my voice" --voice-clone myvoice.wav --output cloned.wav

# 4. Multilingual generation:
cli-tts --text "你好，世界" --lang ZH --output zh.wav
cli-tts --text "こんにちは" --lang JA --output ja.wav

# 5. Use a persistent custom voice:
cli-tts --set-clone-voice my_voice.wav
cli-tts --text "Speaking with my saved voice" --output saved.wav

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
