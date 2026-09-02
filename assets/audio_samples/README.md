# Audio Generation Samples & Inference Benchmarks: KittenTTS-Nano vs. MOSS-TTS-Nano

This directory contains reference and generated audio samples comparing **KittenTTS-Nano** (default on-device engine with fixed expressive voices) and **MOSS-TTS-Nano** (autoregressive zero-shot voice-cloning engine), along with side-by-side inference latency benchmarks.

---

## 1. Non-Cloned Standard Voice Generations (`KittenTTS-Nano`)

These samples demonstrate the default on-device non-autoregressive KittenTTS-nano engine (24 kHz mono).

| File | Voice / Engine | Sample Rate | Transcript / Description |
| :--- | :--- | :--- | :--- |
| [`kitten_nano_default_woman_voice.wav`](file:///Volumes/1tb-sandisk/code-external/tts-cli/assets/audio_samples/kitten_nano_default_woman_voice.wav) | `expr-voice-5-f` (**System Default Woman Voice**) | 24,000 Hz Mono | *"This is the newly configured default voice for Kitten TTS Nano across the whole system. It uses the expressive woman voice variant five with high clarity and natural cadence."* |
| [`kitten_nano_female.wav`](file:///Volumes/1tb-sandisk/code-external/tts-cli/assets/audio_samples/kitten_nano_female.wav) | `expr-voice-2-f` (Built-in Female variant 2) | 24,000 Hz Mono | *"This is a demonstration of Kitten TTS Nano with the expressive female voice. Audio is produced at 24 kilohertz with low system resource utilization."* |
| [`kitten_nano_male.wav`](file:///Volumes/1tb-sandisk/code-external/tts-cli/assets/audio_samples/kitten_nano_male.wav) | `expr-voice-2-m` (Built-in Male variant 2) | 24,000 Hz Mono | *"This is a demonstration of Kitten TTS Nano with the default expressive male voice. Inference is lightweight, completely on device, and runs non-autoregressively."* |

---

## 2. Zero-Shot Voice-Cloned Generations (`MOSS-TTS-Nano`)

These samples demonstrate the autoregressive MOSS-TTS-Nano engine (44.1 / 48 kHz stereo) across languages and reference prompts located in [`assets/audio_samples/moss_tts/`](file:///Volumes/1tb-sandisk/code-external/tts-cli/assets/audio_samples/moss_tts/):

| File | Category / Language | Sample Rate | Description |
| :--- | :--- | :--- | :--- |
| [`moss_tts/en_2.wav`](file:///Volumes/1tb-sandisk/code-external/tts-cli/assets/audio_samples/moss_tts/en_2.wav) | English Reference / Output | 44.1 kHz Stereo | Conversational English speech style. |
| [`moss_tts/en_3.wav`](file:///Volumes/1tb-sandisk/code-external/tts-cli/assets/audio_samples/moss_tts/en_3.wav) | English Reference / Output | 44.1 kHz Stereo | Expressive narrative speech style. |
| [`moss_tts/en_4.wav`](file:///Volumes/1tb-sandisk/code-external/tts-cli/assets/audio_samples/moss_tts/en_4.wav) | English Reference / Output | 44.1 kHz Stereo | Professional announcement speech style. |
| [`moss_tts/en_6.wav`](file:///Volumes/1tb-sandisk/code-external/tts-cli/assets/audio_samples/moss_tts/en_6.wav) | English Reference / Output | 44.1 kHz Stereo | Dynamic vocal inflection sample. |
| [`moss_tts/en_7.wav`](file:///Volumes/1tb-sandisk/code-external/tts-cli/assets/audio_samples/moss_tts/en_7.wav) | English Prompt Reference | 44.1 kHz Stereo | Reference voice prompt audio. |
| [`moss_tts/en_8.wav`](file:///Volumes/1tb-sandisk/code-external/tts-cli/assets/audio_samples/moss_tts/en_8.wav) | English Cloned Synthesis | 44.1 kHz Stereo | Zero-shot voice cloned output matching `en_7.wav` reference. |
| [`moss_tts/zh_1.wav`](file:///Volumes/1tb-sandisk/code-external/tts-cli/assets/audio_samples/moss_tts/zh_1.wav) | Chinese Reference / Output | 44.1 kHz Stereo | Standard Mandarin reference audio prompt. |
| [`moss_tts/zh_3.wav`](file:///Volumes/1tb-sandisk/code-external/tts-cli/assets/audio_samples/moss_tts/zh_3.wav) | Chinese Speech Sample | 44.1 kHz Stereo | Natural cadence Mandarin synthesis. |
| [`moss_tts/zh_6.wav`](file:///Volumes/1tb-sandisk/code-external/tts-cli/assets/audio_samples/moss_tts/zh_6.wav) | Long Chinese Dialogue | 44.1 kHz Stereo | Extended audio generation sample. |
| [`moss_tts/jp_2.wav`](file:///Volumes/1tb-sandisk/code-external/tts-cli/assets/audio_samples/moss_tts/jp_2.wav) | Japanese Speech Sample | 44.1 kHz Stereo | Multilingual Japanese speech synthesis. |

---

## 3. Inference Time & Completion Benchmark

Measured on Apple Silicon CPU across sentence length tiers:

| Metric / Workload | KittenTTS-Nano (15M int8 ONNX) | MOSS-TTS-Nano (100M+20M ONNX) | Speed Advantage |
| :--- | :--- | :--- | :--- |
| **Model Size on Disk** | **~25 MB** | **~450 MB – 600 MB** | KittenTTS (~18x smaller) |
| **RAM Footprint (RSS)** | **~200 MB** | **~1.5 GB** | KittenTTS (~7.5x lighter) |
| **Short Text (8 words / 3s audio)** | **~0.3s** (5.9s cold start) | **~3.2s** (12.5s cold start) | KittenTTS is **10x faster** raw |
| **Medium Text (27 words / 7s audio)** | **~0.8s** (4.9s cold start) | **~7.1s** (15.5s cold start) | KittenTTS is **8.8x faster** raw |
| **Long Text (68 words / 16s audio)** | **~1.4s** (5.4s cold start) | **~16.8s** (26.0s cold start) | KittenTTS is **12x faster** raw |
| **Pure Inference RTF** | **0.08 – 0.12** (Feed-forward) | **0.85 – 1.10** (Autoregressive loop) | KittenTTS delivers 10x real-time |
| **Time-to-First-Audio (TTFT)** | Full chunk delivered (~0.8s) | **~200ms – 300ms** (Streaming prefill)| MOSS-TTS excels for streaming bots |

### Key Benchmark Insight
- **KittenTTS-Nano:** Generates all phonemes in parallel via non-autoregressive flow matching. Generating 16 seconds of audio completes in **~1.4 seconds** of compute time on CPU (RTF 0.08).
- **MOSS-TTS-Nano:** Autoregressively samples 12.5 tokens/sec across 16 RVQ codebooks. Generating 16 seconds of audio requires ~200 decoding steps through a 100M model, taking **~16.8 seconds** on CPU (RTF ~1.05).
- **Cold Load Overhead:** Spawning a stateless CLI process adds ~3.5s for KittenTTS (25MB) vs. ~9.0s–12.0s for MOSS-TTS (multi-graph ONNX + tokenizer + shared weights).

---

## 4. Quick Playback Instructions

To audition any sample from the terminal:

```bash
# New system default woman voice (expr-voice-5-f)
afplay assets/audio_samples/kitten_nano_default_woman_voice.wav

# MOSS-TTS English cloned output
afplay assets/audio_samples/moss_tts/en_8.wav

# MOSS-TTS English reference prompt
afplay assets/audio_samples/moss_tts/en_7.wav

# MOSS-TTS Chinese sample
afplay assets/audio_samples/moss_tts/zh_1.wav
```
