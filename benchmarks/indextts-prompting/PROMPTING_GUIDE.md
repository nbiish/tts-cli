# IndexTTS-2.5 — Expert Prompting Guide

> Factual basis: [IndexTeam/IndexTTS-2.5](https://huggingface.co/IndexTeam/IndexTTS-2.5)
> model card + `audiocpp_cli --help` (audio.cpp 0.6.1, Metal). All claims below are
> drawn from those two sources and from measured runs on this machine
> (Apple Silicon, MPS/Metal). Where a feature is runtime-specific, it is marked
> **[Python]** or **[audio.cpp]**.

## 1. Architecture — is there a significant difference?

**Short answer: the *model* is the same; the *runtime* and *precision* differ,
and that changes which prompting controls are available.**

The underlying model is identical in both paths — IndexTTS-2.5, an
**autoregressive zero-shot TTS** with a **GPT backbone (~0.8B params)**, a
**flow-matching speech-to-mel decoder**, and a **BigVGAN vocoder**, outputting
**22.05 kHz** waveforms. The GGUF file (`index-tts2_5-q8_0.gguf`, 3.5 GB) is the
*same weights* quantized to **Q8_0 (8-bit)** and packaged into a single ggml
file; it is not a different architecture.

| Dimension | Normal (Python, `IndexTeam/IndexTTS-2.5`) | Quantized (GGUF Q8, `audio.cpp` on Metal) |
|---|---|---|
| Model weights | IndexTTS-2.5, **bf16/f32** full precision | IndexTTS-2.5, **Q8_0** 8-bit quantized |
| Runtime | `indextts` Python lib (GPT + flow-matching + BigVGAN, full pipeline) | `audiocpp_cli` — C++/ggml reimplementation, Metal kernels |
| Accelerator | MPS (Apple Silicon) / CUDA / XPU | Metal (Apple Silicon); CUDA/HIP/Vulkan elsewhere |
| Emotion control | **8-float vector** `[happy, angry, sad, afraid, disgusted, melancholic, surprised, calm]` — mixable, continuous | **`--emotion <name>`** — single named emotion (coarse) |
| Speaking speed | **`duration_factor`** (0.5–2.0; >1.0 slower, <1.0 faster) | **`--speaking-rate <float>`** and/or **`--duration-seconds`** / `--target-duration-seconds` |
| Pronunciation control | **Yes** — `<word|reading>` inline tags: Pinyin (ZH), CMU phonemes (EN), Kana (JA) | **No** inline pronunciation tags |
| Pitch / energy | Not exposed directly | **`--pitch-shift <float>`**, **`--energy-scale <float>`** |
| Cross-lingual clone | Yes (voice transfers across ZH/EN/JA/ES/AR) | Yes (`--voice-ref` + `--language`) |
| Languages | ZH, EN, JA, ES, AR | ZH, EN, JA, ES, AR (`--language`, lowercase code) |
| Cold-start cost | ~142 s (full pipeline load on MPS) | ~43 s (ggml load + Metal kernel compile) |
| RTF (155-char prompt) | ~17.2 | ~5.1 |
| Memory between calls | Released on subprocess exit (no daemon) | Released on subprocess exit (no daemon) |

**The significant, decision-relevant difference is the *prompting surface*, not
the architecture.** The Python path exposes the **fine-grained, mixable emotion
vector** and **inline pronunciation tags** — the two features that most change
output character. The audio.cpp path trades those for **named emotion** plus
**pitch/energy/speaking-rate** controls the Python API does not expose, and is
**3.3× faster** cold. Choose by which controls you need, not by "model quality"
in the abstract — Q8 quantization is light enough that the timbre/cloning
fidelity is very close to bf16 for short agent-summary prompts (the model card
notes fidelity loss mainly appears with `use_random=True` emotion sampling, which
neither default path uses).

## 2. Prompting surface — what you can actually control

### 2.1 Shared by both runtimes

- **`text`** — the prompt to speak. Keep agent summaries under ~500 chars; the
  model **splits long text into segments** and concatenates with short silence,
  so **prosody is not modelled across segment boundaries** (model card
  limitation). For natural delivery, prefer one clause per run and avoid
  mid-sentence segment breaks.
- **`language`** — `ZH | EN | JA | ES | AR` (audio.cpp takes lowercase, e.g.
  `en`; Python takes uppercase `EN`). Pick the language that matches the text;
  mismatched language + text degrades pronunciation.
- **`voice-ref` / `spk_audio_prompt`** — the reference clip for zero-shot
  cloning. **Emotion is disentangled from timbre** (model card), so the
  reference controls *who* speaks, not *how* they feel.

### 2.2 Python-only (`IndexTTS2.infer`)

- **`emo_vector`** — 8 floats in the exact order
  `[happy, angry, sad, afraid, disgusted, melancholic, surprised, calm]`.
  Values are continuous and **mixable** (e.g. `[0.6, 0, 0, 0, 0, 0.3, 0, 0]` =
  happy-with-melancholic undertone). This is the most expressive single lever.
- **`duration_factor`** — `0.5`–`2.0`. `>1.0` slows down, `<1.0` speeds up.
  `1.0` = reference rate. For agent status summaries, `1.0`–`1.1` sounds
  measured; `0.9` sounds brisk.
- **Pronunciation tags** — `<word|reading>` inline in the text:
  - ZH Pinyin: `他在银<行|XING2>里<行|HANG2>走了半天。` (polyphone disambiguation)
  - EN CMU phonemes: `<read|RIY D>`
  - JA Kana: `<日本|ニホン>`
  Use for proper nouns, polyphones, and acronyms the base model misreads.
- **`use_qwen_emo=True`** — enables emotion *from a text description* (loads the
  QwenEmotion model). Without it, `use_emo_text=True` raises at inference time.

### 2.3 audio.cpp-only (`audiocpp_cli`)

- **`--emotion <name>`** — a single named emotion (coarse; not mixable). The
  valid names correspond to the 8 vector dimensions:
  `happy | angry | sad | afraid | disgusted | melancholic | surprised | calm`.
- **`--speaking-rate <float>`** — rate multiplier (faster/slower).
- **`--pitch-shift <float>`** — pitch offset (Python has no equivalent).
- **`--energy-scale <float>`** — energy/intensity scaling (Python has no
  equivalent).
- **`--duration-seconds` / `--target-duration-seconds` / `--reference-duration-seconds`**
  — absolute duration targeting instead of a relative factor.
- **`--metrics`** — prints wall time, audio duration, and RTF after generation
  (use this for benchmarking, not `time`).

## 3. Expert techniques (factual, from the model card)

### 3.1 Reference-clip selection (the biggest single quality lever)
- **Clean, single-speaker, 5–15 s** clips clone best. Background noise and
  multi-speaker audio bleed into the timbre.
- The reference sets **timbre only**; emotion comes from `emo_vector` /
  `--emotion`, so pick a neutral-emotion reference and drive emotion via the
  control — do *not* try to steer emotion by picking an emotional reference
  (that fights the disentanglement).
- For cross-lingual transfer, a reference in *any* of the 5 languages can be
  spoken in *any* other language.

### 3.2 Emotion
- **Python:** use the **vector**, not a single 1.0. Subtle mixes read as more
  human: `[0.5, 0, 0, 0, 0, 0.2, 0, 0.3]` (calm-happy) beats `[1,0,0,0,0,0,0,0]`.
  Avoid `use_random=True` for cloning — the model card warns it **reduces cloning
  fidelity**.
- **audio.cpp:** `--emotion` is one name at a time. For agent summaries,
  `calm` or `happy` are the safe defaults; `surprised`/`afraid` sound off for
  status readouts.

### 3.3 Speed
- **Python `duration_factor`**: `1.0`–`1.1` for summaries (measured, clear).
  `0.9` for terse/fast readouts. Stay in `0.5`–`2.0`; outside is unsupported.
- **audio.cpp `--speaking-rate`**: equivalent lever; pair with
  `--target-duration-seconds` when you need an exact length (e.g. fit a slot).

### 3.4 Pronunciation (Python only)
- Wrap **only** the misread token: `<IndexTTS|IH N D EH K S T IY S>`.
  Over-tagging natural words hurts flow.
- Use for: polyphones (ZH `<行|HANG2>`), foreign proper nouns, acronyms,
  numbers with ambiguous reading.

### 3.5 Text shaping (both)
- One idea per sentence. The model splits long text at boundaries and **does
  not carry prosody across the split** — so put natural breaks (periods) where
  you want a pause, and avoid comma-spliced run-ons that the splitter will
  chop mid-thought.
- For agent summaries: lead with the outcome, then the one next step. Short,
  declarative. No markdown, no bullets — TTS reads symbols literally.

## 4. Decision rule for this repo

- **Default = audio.cpp GGUF Q8** (`index-tts` / `auto`): fastest, good enough
  for agent status readouts where emotion nuance is irrelevant. Use
  `--emotion calm` and `--speaking-rate` ~1.0.
- **`--quality` = Python IndexTTS-2.5**: use when you need the **emotion
  vector**, **pronunciation tags**, or **cross-lingual nuance** — i.e. anything
  where "how it's said" matters more than speed.
- Both unload fully on process exit — no RAM/VRAM held between calls.
