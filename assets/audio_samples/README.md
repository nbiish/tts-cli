# Audio Generation Samples: Non-Cloned vs. Voice-Cloned

This directory contains reference and generated audio samples comparing **KittenTTS-Nano** (default on-device engine with fixed expressive voices) and **MOSS-TTS-Nano** (autoregressive zero-shot voice-cloning engine).

---

## 1. Non-Cloned Standard Voice Generations (`KittenTTS-Nano`)

These samples demonstrate the default on-device non-autoregressive KittenTTS-nano engine (24 kHz mono).

| File | Voice / Engine | Sample Rate | Transcript / Description |
| :--- | :--- | :--- | :--- |
| [`kitten_nano_default_woman_voice.wav`](file:///Volumes/1tb-sandisk/code-external/eval-moss-tts-nano/assets/audio_samples/kitten_nano_default_woman_voice.wav) | `expr-voice-5-f` (**System Default Woman Voice**) | 24,000 Hz Mono | *"This is the newly configured default voice for Kitten TTS Nano across the whole system. It uses the expressive woman voice variant five with high clarity and natural cadence."* |
| [`kitten_nano_female.wav`](file:///Volumes/1tb-sandisk/code-external/eval-moss-tts-nano/assets/audio_samples/kitten_nano_female.wav) | `expr-voice-2-f` (Built-in Female variant 2) | 24,000 Hz Mono | *"This is a demonstration of Kitten TTS Nano with the expressive female voice. Audio is produced at 24 kilohertz with low system resource utilization."* |
| [`kitten_nano_male.wav`](file:///Volumes/1tb-sandisk/code-external/eval-moss-tts-nano/assets/audio_samples/kitten_nano_male.wav) | `expr-voice-2-m` (Built-in Male variant 2) | 24,000 Hz Mono | *"This is a demonstration of Kitten TTS Nano with the default expressive male voice. Inference is lightweight, completely on device, and runs non-autoregressively."* |

**Key Characteristics:**
- Generated in parallel across phonemes in ~0.5s–1.2s total compute time.
- Highly crisp, intelligible, deterministic cadence.
- System default voice is now pinned to the last woman voice (`expr-voice-5-f`) when `--voice` is omitted.
- Zero voice-cloning prompt required.

---

## 2. Zero-Shot Voice-Cloned Generations (`MOSS-TTS-Nano`)

These samples demonstrate the autoregressive MOSS-TTS-Nano engine (44.1 / 48 kHz stereo) conditioned on reference speech prompts.

| File | Type / Engine | Sample Rate | Description |
| :--- | :--- | :--- | :--- |
| [`moss_tts_nano_prompt_ref_en.wav`](file:///Volumes/1tb-sandisk/code-external/eval-moss-tts-nano/assets/audio_samples/moss_tts_nano_prompt_ref_en.wav) | English Reference Audio | 44,100 Hz Stereo | Original reference speaker prompt audio used as conditioning. |
| [`moss_tts_nano_cloned_output_en.wav`](file:///Volumes/1tb-sandisk/code-external/eval-moss-tts-nano/assets/audio_samples/moss_tts_nano_cloned_output_en.wav) | Cloned Speech Output | 44,100 Hz Stereo | Synthesized utterance replicating the reference speaker's acoustic timbre, natural cadence, and breathing pauses. |
| [`moss_tts_nano_prompt_ref_zh.wav`](file:///Volumes/1tb-sandisk/code-external/eval-moss-tts-nano/assets/audio_samples/moss_tts_nano_prompt_ref_zh.wav) | Chinese Reference Audio | 44,100 Hz Stereo | Multilingual reference audio for zero-shot Chinese speech synthesis. |

**Key Characteristics:**
- Autoregressive discrete token generation (12.5 tokens/sec across 16 RVQ codebooks).
- 48 kHz studio-grade stereo reproduction with natural acoustic timbre and prosodic inflection.
- Time-to-first-token ~150ms–300ms prefill for streaming playback.

---

## 3. Quick Playback Instructions

To play any sample directly from the terminal using the repository's sequential speaker lock:

```bash
# KittenTTS Male sample
afplay assets/audio_samples/kitten_nano_male.wav

# KittenTTS Female sample
afplay assets/audio_samples/kitten_nano_female.wav

# MOSS-TTS Voice-Cloned English sample
afplay assets/audio_samples/moss_tts_nano_cloned_output_en.wav
```
