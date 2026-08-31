# TTS Landscape Audit — 2026-08-31

> Question: is IndexTTS-2.5 GGUF (our current fast default) actually the most
> performant speedy model for agent summaries on Apple Silicon, or did we miss a
> faster one? Audited 2026-08-31 against the legacy models we carried and the
> current Apple-Silicon TTS field.
> Sources: [RLX TTS benchmarks](https://github.com/MIT-RLX/rlx-models/blob/main/TTS.md) ·
> [MetalRT speech benchmarks](https://www.runanywhere.ai/blog/metalrt-speech-fastest-stt-tts-apple-silicon) ·
> [mlx-gepard-swift](https://github.com/xocialize/mlx-gepard-swift) ·
> [supertone-inc/supertonic](https://github.com/supertone-inc/supertonic/) ·
> our own IndexTTS-2.5 / WavTTS measurements on this machine.

## 1. Our use case (the constraint that picks the winner)

Agent end-of-chat summaries: **short text** (1–2 sentences), **zero-shot voice
cloning** of the operator's voice from a single reference clip, **low latency**
matters (the operator may be away from screen), Apple Silicon (MPS/Metal),
**no daemon** (unload after each call). So the deciding capability is
**zero-shot cloning + speed on Metal**, not raw fixed-voice throughput.

## 2. Apple-Silicon Metal RTF leaderboard (zero-shot cloning highlighted)

| model | RTF (Metal) | zero-shot clone? | footprint | notes |
|---|---|---|---|---|
| Kokoro-82M (StyleTTS2) | **0.05–0.84×** | partial (voice embeddings, not arbitrary clip) | ~330 MB | fastest fixed-voice; MetalRT hits RTF 0.0014 |
| **Gepard-1.0** | **~0.24–0.4×** | **YES** | ~1.2 GB | AR + NanoCodec, 22.05 kHz, **TTFA 17 ms**, streaming |
| LuxTTS (ZipVoice-distill) | 0.16× | YES (cloning) | — | CFM, 3 subgraphs |
| F5-TTS | 0.12× | yes | — | (WavTTS base) — but WavTTS_Large 10.8 GB **hung on our MPS** |
| Zonos | 0.12× | ? | — | very fast |
| Moss-nano | 0.24× | ? | — | very fast |
| Chatterbox | 0.09× (MLX) | YES (cloning) | ~2 GB | we have it in HF cache; Metal timed out in RLX bench |
| Qwen3-TTS 0.6B | ~1.05–1.7× | yes | 0.6 B | best speed/quality of large models |
| Supertonic 3 | 1.10× | no (fixed) | 99 M | ONNX CPU, multi-lang |
| Piper | 3.95× | no (fixed) | tiny | fast fixed-voice |
| **IndexTTS-2.5 GGUF Q8** (ours) | **~1.5× (cold ~37 s)** | **YES** | 3.5 GB | audio.cpp/Metal; current default |
| IndexTTS-2.5 Python (ours) | ~40× (cold ~266 s) | YES | 5.1 GB | MPS; `--quality` tier |
| WavTTS Large | **>17 min, no output** | YES | 10.8 GB | CUDA-first; **impractical on MPS** (see wavtts/BENCHMARK.md) |

## 3. Answer: yes, we missed a faster model — Gepard-1.0

For our exact use case (short text + **zero-shot cloning** + Apple Silicon),
**Gepard-1.0** is the standout we missed:

- **Same capability** as IndexTTS-2.5: clone a voice from a single short
  reference clip.
- **~4–6× faster** on Metal: RTF ~0.24 (4.2× realtime) vs our IndexTTS-2.5
  GGUF RTF ~1.5.
- **~2000× lower latency**: time-to-first-audio **17 ms** vs our **~37 s cold**
  (Gepard streams; IndexTTS GGUF cold-loads the whole model each call).
- **Smaller**: ~1.2 GB resident vs 3.5 GB GGUF (+ 5.1 GB Python tier).
- **Same output**: 22.05 kHz mono, like IndexTTS.
- **Native Apple Silicon** Metal/MLX, streaming-first; requires macOS 26+
  (this machine is darwin 25.6.0 = macOS 26.x ✓).
- Whisper intelligibility: 6/6 (greedy) in the RLX bench.

Caveats (honest):
- Gepard is **not** the absolute fastest TTS on Apple Silicon —
  **Kokoro-82M** (via MetalRT) is faster (RTF 0.0014) — but Kokoro is
  fixed/embedding-voice, not arbitrary-clip zero-shot cloning. If a small set
  of preset voices is acceptable for summaries, Kokoro is faster still.
- **Inflect-Nano** (~4.6 M, ~48× realtime) is the raw-speed champion but is
  FastSpeech-style fixed-voice, not zero-shot cloning.
- Gepard integration into our Python `tts-cli` is **not drop-in**: the
  production path is Swift/MLX (`mlx-gepard-swift`) or Rust (`rlx-gepard`).
  IndexTTS-2.5 GGUF won on **integration simplicity** (audio.cpp CLI → subprocess
  adapter, exactly our existing pattern). Adopting Gepard means a new runtime
  (Swift MLX engine or the RLX Rust crate), not just a new GGUF.

## 4. Cleanup performed this audit

- Pruned from the HF cache (legacy TTS removed from tts-cli earlier, ~354 MB):
  `kyutai/pocket-tts`, `kyutai/pocket-tts-without-voice-cloning`,
  `KittenML/kitten-tts-{mini-0.8, nano-0.8-int8, nano-0.1}`.
- Re-verified `cli-tts --list-models`: `index-tts` / `auto` (GGUF fast) and
  `index-tts-quality` (Python) all ✅ Available after prune.
- Disk: external 1 TB now 490 GB free (pressure already resolved before this
  audit); internal disk reclaimed to 90 GB free after the WavTTS run.

## 5. Remaining HF-cache candidates (operator to decide — not pruned)

These are the operator's models, not legacy-tts-cli assets, so left in place:
- `LiquidAI/LFM2.5-VL-1.6B-GGUF` — 7.5 GB, **not TTS** (vision-language).
- `nari-labs/Dia-1.6B` — 6.0 GB, TTS/dialogue (CUDA-oriented).
- `ResembleAI/chatterbox` — 2.0 GB, zero-shot cloning TTS (a Gepard
  alternative; MLX path exists).
- `fastrtc/kokoro-onnx` — 337 MB, Kokoro (fastest fixed-voice).
- ASR models (`cohere-transcribe`, `parakeet`, `canary`) — useful for
  transcription, kept.

## 6. Recommendation

**New constraint (operator, 2026-08-31): tts-cli must be system-agnostic —
run on Linux, Windows, WSL, and macOS.** This reshapes the ranking by
**portability**, not just speed:

| path | macOS | Linux | Windows/WSL | portable? |
|---|---|---|---|---|
| **IndexTTS-2.5 GGUF via audio.cpp** | Metal | CUDA/Vulkan/CPU | Vulkan/CPU | **YES** (audio.cpp backends: metal/cuda/hip/vulkan/cpu) |
| IndexTTS-2.5 Python | MPS | CUDA/XPU/CPU | CUDA/CPU | **YES** (torch covers all) |
| Gepard-1.0 (mlx-gepard-swift) | Metal | ❌ | ❌ | **NO** — Swift/MLX, macOS 26+ only |
| Gepard-1.0 (rlx-gepard Rust crate) | Metal | Vulkan/CPU? | ? | maybe — unverified cross-platform |
| WavTTS | ❌ (hung) | CUDA | CUDA | no (CUDA-only + non-commercial) |
| Kokoro-82M (ONNX) | CPU/Metal | CPU | CPU | **YES** (ONNX Runtime is cross-platform) |

Under the portability constraint:
1. **IndexTTS-2.5 GGUF via audio.cpp is the correct fast default** — it is
   cross-platform (audio.cpp supports `metal|cuda|hip|vulkan|cpu|best`), and
   `--backend best` lets the runtime auto-pick. This keeps one code path across
   all four OS targets. **Gepard loses the speed lead in practice** because its
   fast path (Swift/MLX) is macOS-only; the Rust crate path is unverified
   cross-platform and a heavier integration.
2. **Make the backend auto-detect**, not hardcoded to `metal`. The adapter
   must probe the OS + accelerator and pass the right `--backend` (or
   `--backend best`). The Python tier already auto-detects via torch
   (CUDA/MPS/XPU/CPU).
3. **Make the autoplayer cross-platform** (`afplay` macOS / `aplay`|`paplay`
   Linux / PowerShell `Media.SoundPlayer` Windows) — currently macOS-only.
4. **Drop the macOS-`say` dependency** for the seed reference voice — ship a
   bundled cross-platform reference WAV (or generate one via the engine
   itself on first run).
5. Keep Kokoro-82M (ONNX) as a future portable fixed-voice option if preset
   voices ever suffice.

