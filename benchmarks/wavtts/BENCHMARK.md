# WavTTS Benchmark — vs IndexTTS-2.5 (Apple Silicon)

> Date: 2026-08-31 (UTC-4). Hardware: Apple Silicon, MPS/Metal.
> Sources: [worstchan/WavTTS](https://huggingface.co/worstchan/WavTTS) ·
> [cwx-worst-one/WavTTS](https://github.com/cwx-worst-one/WavTTS) ·
> [arXiv:2606.03455](https://arxiv.org/abs/2606.03455) ·
> measured run on this machine.

## 1. What WavTTS is (factual)

- **WavTTS** ("Towards High-Quality Zero-Shot TTS via Direct Raw Waveform
  Modeling"): end-to-end zero-shot TTS that generates speech **directly in the
  raw waveform space** — no mel-spectrogram, VAE latent, or codec-token
  intermediate. Built on **flow matching with DiT**, waveform patchification,
  multi-scale mel-spectrogram supervision, optimized noise scheduling.
- **Codebase:** based on **F5-TTS** (non-autoregressive).
- **Checkpoint:** `model_1200000.pt`, **10.8 GB** (WavTTS_Large). 16 kHz output.
- **License:** CC BY-NC 4.0 (weights, due to the Emilia training dataset);
  MIT (code). **Non-commercial only.**
- **Inference API:** `wavtts_infer-cli -p <ckpt> -v <vocab> -r <ref_audio>
  -s <ref_text> -t <gen_text> --device <dev>`. **Requires `ref_text`**
  (a transcription of the reference clip) — unlike IndexTTS, which needs only
  the reference audio.
- **Designed for CUDA** (install instructions use `torch==2.6.0 …cu124`).

## 2. Architecture difference vs IndexTTS-2.5 (the real question)

| Dimension | WavTTS | IndexTTS-2.5 |
|---|---|---|
| Generation | **Non-autoregressive** (flow matching + DiT) | **Autoregressive** (GPT backbone) |
| Output space | **Direct raw waveform** (no vocoder) | Mel → BigVGAN vocoder |
| Checkpoint | 10.8 GB (Large) | ~5.1 GB |
| Sample rate | 16 kHz | 22.05 kHz |
| Reference input | audio **+ ref_text** (transcription) | audio only |
| Target hardware | CUDA (cu124) | CUDA / MPS / XPU |
| License | CC BY-NC 4.0 (non-commercial) | bilibili (research/eval) |
| Prompting controls | `--speed`, `--nfe_step`, `--cfg_strength` | emo_vector, duration_factor, pronunciation tags |

The architectures are **fundamentally different**: WavTTS is non-autoregressive
flow-matching in waveform space (potentially fast *on CUDA*); IndexTTS-2.5 is
autoregressive GPT + vocoder. The "fastest" claim for WavTTS depends on CUDA —
on Apple Silicon it does not hold (see §3).

## 3. Measured run on Apple Silicon (MPS)

Setup: WavTTS_Large, `model_1200000.pt` (10.8 GB), torch 2.6.0 (MPS build),
Python 3.10 `uv` env on the internal disk (the 1 TB external was full). Reference
`/tmp/ref_bench.wav` (7.10 s, known text). Same generation text as the IndexTTS
benchmark: *"cli-tts is ready for all agents. IndexTTS-2.5 is the sole engine.
Next step: verify the voice channel end to end."*

```
[2026-08-31T19:52Z] START WavTTS inference (--device mps)
… model loaded (10.8 GB), "Generating audio in 1 batches…"
  0%|          | 0/1 [00:00<?, ?it/s]   ← stuck at 0%
[2026-08-31T20:09Z] KILLED — no progress after ~17 minutes, 0% completion.
```

**Result: WavTTS did not produce audio.** Flow-matching inference on the
10.8 GB WavTTS_Large checkpoint hung at 0% on MPS for ~17 minutes and was
killed. No output WAV was generated. This is consistent with WavTTS being a
CUDA-first model (install path is `cu124`); the MPS backend is not a supported
target for this model's direct-waveform DiT.

## 4. Comparison table (this machine)

| Engine | Runtime | Cold to first audio | RTF | Output | Verdict on Apple Silicon |
|---|---|---|---|---|---|
| **IndexTTS-2.5 GGUF Q8** | audio.cpp / Metal | **~37 s** | **~1.5** | 22.05 kHz | ✅ fast default |
| IndexTTS-2.5 Python | indextts / MPS | ~266 s | ~40 (cold) | 22.05 kHz | ⚠️ `--quality` only |
| **WavTTS Large** | F5-TTS / MPS | **>17 min, no output** | n/a | 16 kHz | ❌ impractical |

## 5. Conclusion

- **WavTTS is not viable on this Apple Silicon machine.** It is CUDA-oriented
  (10.8 GB, direct-waveform flow-matching) and did not produce any audio on MPS
  within 17 minutes. Its CC BY-NC 4.0 license also blocks commercial use.
- **IndexTTS-2.5 GGUF Q8 via audio.cpp on Metal remains the correct fast
  default** (~37 s cold, RTF ~1.5, 22.05 kHz), with the Python IndexTTS-2.5
  path as the `--quality` tier.
- WavTTS would only be worth revisiting on a CUDA host, and only if a
  non-commercial license is acceptable. On Apple Silicon, do not adopt it.
- Disk note: the 10.8 GB checkpoint + ~4 GB env were placed on the internal
  disk (the 1 TB external was full) and **removed after the run** — internal
  disk reclaimed to 90 GB free. No persistent footprint.
