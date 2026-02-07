# 🎙️ Local Audio Cleaning & TTS Guide (MCP Edition)

This comprehensive guide documents the local audio processing capabilities of the `tts-cli` codebase, specifically tailored for use within a **Model Context Protocol (MCP)** environment.

These tools allow AI agents to perform high-quality **Text-to-Speech (TTS)**, **Voice Cloning**, and **Audio Cleaning** entirely locally, ensuring data privacy and zero latency.

---

## ⚡ Quick Reference

| Feature | Flag | Description | Engine |
| :--- | :--- | :--- | :--- |
| **TTS** | `--text "..."` | Generate speech from text | Pocket TTS |
| **Voice Clone** | `--voice-clone <file>` | Clone voice from reference audio | Pocket TTS |
| **Clean Voice** | `--clean-voice [file]` | **Best Practice**: Isolate vocals + Remove silence | Demucs + Silero VAD |
| **Isolate Vocals** | `--isolate-voice [file]` | Remove background music/noise | Demucs (Hybrid Transformer) |
| **Remove Silence** | `--remove-silence [file]` | Trim non-speech segments | Silero VAD |

---

## 🛠️ Prerequisites & Setup

Before an MCP agent can utilize these tools, the specific isolated environments must be initialized. This architecture prevents dependency conflicts.

### 1. Initialize Environments
Run these commands once to set up the heavy-lifting dependencies.

```bash
# 1. Setup the lightweight TTS engine
cli-tts --create-environment pocket-tts

# 2. Setup the heavy audio processing engine (Demucs/VAD)
cli-tts --create-environment audio-processing
```

### 2. Verification
Ensure tools are ready:
```bash
cli-tts --list-environments
# Output should show "Available" for both 'pocket-tts' and 'audio-processing'
```

---

## 📖 Workflows

### 1. Robust Voice Cloning (Recommended)
**Scenario:** You have a messy audio file (e.g., an interview with background noise) and want to clone the speaker's voice to say something new.

**The "One-Shot" Command:**
The CLI can automatically clean the reference audio before cloning it.

```bash
cli-tts \
  --text "This is a clean clone generated from noisy audio." \
  --voice-clone noisy_interview.wav \
  --clean-voice \
  --output final_speech.wav
```

**What happens under the hood:**
1.  **Demucs** separates the vocals from the background noise.
2.  **Silero VAD** removes silence and non-speech artifacts.
3.  **Pocket TTS** analyzes the cleaned vocal profile.
4.  **Generation**: The new text is synthesized using the cleaned profile.

### 2. Standalone Audio Cleaning
**Scenario:** You just want to clean up an audio file for other purposes (e.g., a podcast or dataset preparation).

**Full Cleanup (Isolate + Trim):**
```bash
cli-tts --clean-voice raw_input.wav --output cleaned_output.wav
```

**Isolate Vocals Only (Keep silence/pacing):**
```bash
cli-tts --isolate-voice song.wav --output vocals_only.wav
```

**Remove Silence Only (Keep background ambience):**
```bash
cli-tts --remove-silence lecture.wav --output trimmed_lecture.wav
```

### 3. Basic Text-to-Speech
**Scenario:** Simple generation without cloning.

```bash
# Use default voice
cli-tts --text "System initialized." --output status.wav

# Use a specific built-in voice
cli-tts --text "Alert." --voice javert --output alert.wav
```

---

## 🧠 Technical Details for Agents

### Architecture
*   **Isolation**: Audio processing runs in a separate `uv` environment (`.model-envs/audio-processing-env`) containing PyTorch, Demucs, and Torchaudio. This ensures the main CLI remains lightweight.
*   **Performance**:
    *   **Pocket TTS**: Faster than real-time on modern CPUs.
    *   **Demucs**: Slower (approx. 1-2x real-time on CPU). Recommended to run asynchronously if possible.
    *   **VAD**: Extremely fast (negligible overhead).

### Error Handling
*   **Missing Environment**: If `--clean-voice` is used without the `audio-processing` environment, the CLI will return a specific error code/message. Agents should check for "Audio processing environment not found" and run the setup command if detected.
*   **File Not Found**: Ensure absolute paths are used for `--voice-clone` inputs to avoid CWD ambiguity.

### Integration Tips
*   **Chaining**: You can chain `--clipboard` input with voice cloning for rapid prototyping.
*   **Verification**: Always check the exit code (`$?`) after running a command. `0` indicates success.

---

## 📄 License & Privacy
*   **Local-First**: All processing happens on-device. No audio is sent to the cloud.
*   **Compliance**: Adheres to the project's **AGENTS.md** security guidelines (Zero Trust, minimal privileges).
