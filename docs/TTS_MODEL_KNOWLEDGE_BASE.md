# TTS Model Knowledge Base - Creator-Verified Information

**Author:** Nbiish Waabanimikii-Kinawaabakizi | **Date:** August 28, 2025 | **Version:** 3.0

**CRITICAL: This knowledge base contains creator-verified usage instructions for each model. All implementations MUST follow these specifications exactly to ensure proper functionality and optimal results.**

## 🔬 TESTING-FIRST APPROACH: NO MORE VRAM SPECULATION

**Critical Principle: Always test models rather than rely on theoretical specifications.**

### **❌ Why VRAM Requirements Are Misleading:**
- **CUDA vs MPS Differences**: VRAM specs are CUDA-based and don't translate to Apple Silicon MPS
- **Transformers Auto-Detection**: The library automatically optimizes for the actual platform
- **Memory Management**: MPS handles memory differently than CUDA (unified vs dedicated)
- **Real Performance**: Theoretical requirements often don't match actual performance
- **Platform Optimization**: Models may work better on MPS than expected from CUDA specs

### **✅ Our Testing-First Methodology:**
1. **Test Every Model** - Don't assume it won't work based on specs
2. **Use Transformers Auto-Detection** - Let the library handle platform optimization
3. **Measure Actual Performance** - Real-world testing reveals true capabilities
4. **Ignore Theoretical Limits** - Focus on what actually works
5. **Document Real Results** - Replace speculation with empirical data

## 1. F5-TTS (SWivid) - Voice Cloning Model

**Model:** Diffusion Transformer with ConvNeXt V2 architecture  
**Parameters:** ~1B parameters  
**Features:** Fast training and inference, high-quality speech generation  
**Special Capabilities:** Flow matching, diffusion-based generation, voice cloning  
**Auto-Detection:** Uses `device_map="auto"` for automatic device placement across platforms  
**Sample Rate:** 24 kHz  
**License:** MIT (code), CC-BY-NC (models due to Emilia dataset)  

### **⚠️ CRITICAL: This is a VOICE CLONING model - Reference Audio REQUIRED**

**Creator-Verified Usage Instructions:**
```bash
# CLI Inference with voice cloning (REQUIRED)
f5-tts_infer-cli --model F5TTS_v1_Base \
--ref_audio "reference_audio.wav" \
--ref_text "Reference audio transcription" \
--gen_text "Text to synthesize"

# Default settings (still requires reference audio)
f5-tts_infer-cli

# Custom configuration
f5-tts_infer-cli -c custom.toml
```

### **Voice Cloning Requirements:**
- **Reference audio: REQUIRED** - WAV format, any length (clipped to ~12s)
- **Reference text: REQUIRED** - Transcription of reference audio (or empty for ASR)
- **Output:** High-quality cloned voice with natural prosody

### **Installation (UV-compatible):**
```bash
# Install via pip (inference only)
uv pip install f5-tts

# Local editable (training/finetuning)
git clone https://github.com/SWivid/F5-TTS.git
cd F5-TTS
uv pip install -e .
```

### **Important Notes:**
- **This model CANNOT generate speech without reference audio**
- **It's designed specifically for voice cloning applications**
- **Reference audio should be <12s with proper silence at the end**
- **Uppercase letters are uttered letter by letter**
- **Add spaces/punctuation for natural pauses**

---

## 2. Edge TTS (Microsoft) - Standard TTS Model

**Model:** Microsoft Edge's online text-to-speech service  
**Features:** High-quality speech generation, multiple voices  
**Special Capabilities:** 322+ voices, multiple languages, SSML support  
**Auto-Detection:** Works across all platforms (CUDA, MPS, CPU)  
**License:** GPL v3 (community implementation)  

### **✅ Standard TTS - NO Input Audio Required**

**Creator-Verified Usage Instructions:**
```bash
# Basic usage - text only
edge-tts --text "Hello, world!" --write-media hello.mp3

# Change voice
edge-tts --voice ar-EG-SalmaNeural --text "مرحبا كيف حالك؟" --write-media hello_in_arabic.mp3

# Adjust rate, volume, pitch
edge-tts --rate=-50% --text "Hello, world!" --write-media hello_with_rate_lowered.mp3
edge-tts --volume=-50% --text "Hello, world!" --write-media hello_with_volume_lowered.mp3
edge-tts --pitch=-50Hz --text "Hello, world!" --write-media hello_with_pitch_lowered.mp3
```

### **Installation:**
```bash
# Install via pip
uv pip install edge-tts

# Or use pipx for CLI only
pipx install edge-tts
```

### **Available Voices:**
- **322+ voices** across multiple languages
- **Gender options:** Male/Female
- **Content categories:** General, News, Narration, etc.
- **Voice personalities:** Friendly, Positive, Professional, etc.

### **Important Notes:**
- **No voice cloning capability**
- **Internet connection required** (uses Microsoft's online service)
- **High-quality, professional-grade output**
- **Fast processing times**
- **No hardware requirements** (runs on any platform)

---

## 3. Dia (Nari Labs) - Dialogue Generation Model

**Model:** 1.6B parameter dialogue-focused TTS  
**Features:** Ultra-realistic dialogue generation, emotion control, non-verbal sounds  
**Special Capabilities:** Speaker tags ([S1], [S2]), non-verbal expressions (laughs, coughs, etc.)  
**Auto-Detection:** Uses `device_map="auto"` for automatic device placement across platforms  
**License:** Apache 2.0  

### **✅ Standard TTS - NO Input Audio Required (Optional for Voice Cloning)**

**Creator-Verified Usage Instructions:**
```python
# Basic dialogue generation (NO input audio required)
from transformers import AutoProcessor, DiaForConditionalGeneration

text = [
    "[S1] Dia is an open weights text to dialogue model. [S2] You get full control over scripts and voices. [S1] Wow. Amazing. (laughs)"
]

processor = AutoProcessor.from_pretrained("nari-labs/Dia-1.6B-0626")

# Use transformers auto-detection for optimal device handling
model = DiaForConditionalGeneration.from_pretrained(
    "nari-labs/Dia-1.6B-0626",
    device_map="auto",
    dtype=torch.float16  # Use float16 for better performance
)

inputs = processor(text=text, padding=True, return_tensors="pt")
inputs = {k: v.to(model.device) for k, v in inputs.items()}

# Generate audio with official Dia parameters for optimal quality
outputs = model.generate(
    **inputs,
    max_new_tokens=3072,  # Official Dia default
    guidance_scale=3.0,   # Official Dia default
    temperature=1.8,      # Official Dia default
    top_p=0.90,          # Official Dia default
    top_k=45,            # Official Dia default
    do_sample=True        # Official Dia default
)

outputs = processor.batch_decode(outputs)
processor.save_audio(outputs, "example.mp3")
```

### **Dialogue Generation Features:**
- **Speaker tags:** `[S1]`, `[S2]` for multi-speaker conversations
- **Non-verbal expressions:** `(laughs)`, `(coughs)`, `(gasps)`, `(sighs)`, etc.
- **Emotion control:** Natural conversation flow and tone
- **Multi-speaker support:** Up to 2 speakers with consistent voices

### **Voice Cloning (Optional):**
- **Audio prompt for voice consistency** (guide coming soon)
- **Seed fixing for consistent voice generation**
- **5-10 second reference audio recommended**
- **Transcript must use correct speaker tags**

### **Installation:**
```bash
# Install transformers main branch (required)
uv pip install git+https://github.com/huggingface/transformers.git

# Install additional dependencies
uv pip install torch soundfile librosa
```

### **Important Notes:**
- **⚠️ CRITICAL FORMATTING**: Dia requires very specific speaker tag formatting like `[S1]` and `[S2]`
- **User Input Required**: Users should provide their own Dia-specific prompting with proper speaker tags
- **Example Format**: `[S1] Hello there! [S2] How are you? [S1] I'm doing great!`
- **Input text length:** Keep moderate (5-20 seconds of audio)
- **Speaker tags:** Always begin with `[S1]`, alternate between `[S1]` and `[S2]`
- **Non-verbal tags:** Use sparingly from the approved list
- **Performance optimization:** Use `device_map="auto"` and `dtype=torch.float16`
- **Official Parameters:** Using exact parameters from official Dia repository (`max_new_tokens=3072`)
- **Platform support:** Full support for CUDA, MPS (Apple Silicon), and CPU
- **Auto-detection:** Leverages transformers' built-in platform optimization
- **⚠️ Basic Text Warning**: Using basic text without speaker tags may produce poor audio quality

---

## 4. Kyutai TTS - Multilingual Streaming Model

**Model:** 1.6B parameters, multilingual (English/French)  
**Architecture:** Transformer-based with delayed streams  
**Features:** Streaming text input, ultra-low latency  
**Special Capabilities:** Multi-speaker (up to 5 voices), voice cloning with 10-second reference  
**Codec:** Mimi (12.5 Hz, 16 codebooks)  
**Latency:** 220ms end-to-end  

### **✅ Standard TTS - NO Input Audio Required (Optional for Voice Cloning)**

**Creator-Verified Usage Instructions:**
```bash
# PyTorch implementation
echo "Hey, how are you?" | python scripts/tts_pytorch.py - -

# From text file to audio file
python scripts/tts_pytorch.py text_to_say.txt audio_output.wav

# MLX implementation (Apple Silicon)
echo "Hey, how are you?" | python scripts/tts_mlx.py - - --quantize 8

# From text file to audio file
python scripts/tts_mlx.py text_to_say.txt audio_output.wav
```

### **Installation:**
```bash
# PyTorch version
uv pip install moshi

# MLX version (Apple Silicon)
uv pip install moshi-mlx
```

### **Voice Cloning (Optional):**
- **10-second reference audio** for custom voices
- **Automatic voice switching** for multi-speaker
- **CFG distillation** for improved quality

### **Special Features:**
- **Streaming text input** for ultra-low latency
- **Multi-speaker dialogue generation**
- **Automatic prosody adaptation**
- **Background music and speech synthesis**

### **Important Notes:**
- **Ultra-low latency:** 220ms end-to-end
- **Multilingual support:** English and French
- **VCTK voices:** English voices in voice repository
- **CML-TTS voices:** French voices available
- **Hardware support:** CUDA, MPS (Apple Silicon), CPU

---

## 5. Kokoro (Hexgrad) - Ultra-Lightweight Model

**Model:** 82M parameters (ultra-lightweight)  
**Features:** Fast inference, cost-effective deployment  
**Special Capabilities:** Voice cloning, basic TTS functionality  
**License:** Apache 2.0  
**Trade-offs:** Speed/cost vs. quality  

### **✅ Standard TTS - NO Input Audio Required (Optional for Voice Cloning)**

**Creator-Verified Usage Instructions:**
```python
from kokoro import KPipeline
import soundfile as sf

# Initialize pipeline
pipeline = KPipeline(lang_code='a')  # 'a' = American English

text = '''
Kokoro is an open-weight TTS model with 82 million parameters. Despite its lightweight architecture, it delivers comparable quality to larger models while being significantly faster and more cost-efficient.
'''

# Generate audio
generator = pipeline(text, voice='af_heart')
for i, (gs, ps, audio) in enumerate(generator):
    print(i, gs, ps)
    sf.write(f'{i}.wav', audio, 24000)
```

### **Language Support:**
- **🇺🇸 'a'**: American English
- **🇬🇧 'b'**: British English  
- **🇪🇸 'e'**: Spanish
- **🇫🇷 'f'**: French
- **🇮🇳 'h'**: Hindi
- **🇮🇹 'i'**: Italian
- **🇯🇵 'j'**: Japanese (requires `misaki[ja]`)
- **🇧🇷 'p'**: Brazilian Portuguese
- **🇨🇳 'z'**: Mandarin Chinese (requires `misaki[zh]`)

### **Installation:**
```bash
# Install kokoro
uv pip install kokoro>=0.9.4 soundfile

# Install espeak-ng for OOD fallback
# On Ubuntu/Debian: apt-get install espeak-ng
# On macOS: brew install espeak
```

### **Voice Cloning (Optional):**
- **Basic voice cloning capabilities**
- **Limited quality compared to larger models**
- **Fast processing for real-time applications**

### **Important Notes:**
- **Ultra-lightweight:** 82M parameters
- **Fast startup and inference times**
- **Suitable for resource-constrained environments**
- **Quality expectations:** Basic TTS with limited voice cloning
- **Cross-platform:** Works on CUDA, MPS, CPU

---

## 6. VibeVoice (Microsoft) - Long-Form Conversational Model

**Model:** 1.5B parameters, long-form conversational TTS  
**Features:** Up to 90 minutes of speech, multi-speaker (up to 4 distinct speakers)  
**Special Capabilities:** Long-form dialogue, natural turn-taking, podcast-style generation  
**Architecture:** Transformer-based LLM with acoustic/semantic tokenizers and diffusion decoding  
**License:** MIT (research purposes)  

### **✅ Standard TTS - NO Input Audio Required (Optional for Voice Cloning)**

**Creator-Verified Usage Instructions:**
```bash
# Launch Gradio demo
python -m vibevoice.demo

# Direct inference from files
python -m vibevoice.inference

# For 1.5B model
python demo/gradio_demo.py --model_path microsoft/VibeVoice-1.5B --share

# For 7B model  
python demo/gradio_demo.py --model_path WestZhang/VibeVoice-Large-pt --share
```

### **Available Models:**
| Model | Context Length | Generation Length | Weight |
|-------|----------------|-------------------|---------|
| VibeVoice-0.5B-Streaming | - | - | Coming soon |
| VibeVoice-1.5B | 64K | ~90 min | [HF link](https://huggingface.co/microsoft/VibeVoice-1.5B) |
| VibeVoice-7B-Preview | 32K | ~45 min | [HF link](https://huggingface.co/WestZhang/VibeVoice-Large-pt) |

### **Installation:**
```bash
# Clone repository
git clone https://github.com/microsoft/VibeVoice.git
cd VibeVoice/

# Install in editable mode
uv pip install -e .
```

### **Voice Cloning (Optional):**
- **Multi-speaker conversation support**
- **Long-form audio generation** (up to 90 minutes)
- **Natural turn-taking and dialogue flow**
- **Speaker consistency across long conversations**

### **Special Features:**
- **Long-form conversational synthesis**
- **Multi-speaker dialogue generation**
- **Podcast and audiobook generation**
- **Natural conversation flow**
- **Spontaneous background music** (content-aware)

### **Important Notes:**
- **Hardware requirements:** CUDA GPU recommended
- **Chinese speech stability:** Use English punctuation, prefer 7B model
- **Background music:** Spontaneous and content-aware
- **Text normalization:** Minimal - LLM handles complex inputs
- **Singing capabilities:** Yes, with appropriate voice prompts

---

## 📊 Model Comparison Summary

| Model | Input Audio Required | Voice Cloning | Special Features | Hardware Support |
|-------|---------------------|---------------|------------------|------------------|
| **F5-TTS** | ❌ **YES** (Voice Cloning Model) | ✅ Advanced | Flow matching, diffusion | CUDA, MPS, CPU |
| **Edge TTS** | ✅ **NO** | ❌ No | 322+ voices, multiple languages | Any platform |
| **Dia** | ✅ **NO** | ✅ Basic | Dialogue generation, speaker tags | CUDA, MPS, CPU |
| **Kyutai** | ✅ **NO** | ✅ Advanced | Ultra-low latency, streaming | CUDA, MPS, CPU |
| **Kokoro** | ✅ **NO** | ✅ Basic | Ultra-lightweight, fast | CUDA, MPS, CPU |
| **VibeVoice** | ✅ **NO** | ✅ Advanced | Long-form, multi-speaker | CUDA (recommended) |

## 🚨 Critical Implementation Notes

### **Models Requiring Input Audio:**
- **F5-TTS**: **ALWAYS requires reference audio** - this is a voice cloning model by design

### **Models NOT Requiring Input Audio:**
- **Edge TTS**: Standard TTS service
- **Dia**: Standard TTS with dialogue capabilities
- **Kyutai**: Standard TTS with streaming support
- **Kokoro**: Standard TTS with basic voice cloning
- **VibeVoice**: Standard TTS with long-form capabilities

### **Voice Cloning vs. Standard TTS:**
- **Voice Cloning**: Requires reference audio file (F5-TTS, optional for others)
- **Standard TTS**: Generates speech from text only (Edge TTS, Dia, Kyutai, Kokoro, VibeVoice)

## 🔧 Implementation Guidelines

### **For Standard TTS Models:**
1. **No input audio required** for basic functionality
2. **Voice cloning is optional** enhancement
3. **Text input is sufficient** for speech generation
4. **Follow creator-verified usage patterns**

### **For Voice Cloning Models (F5-TTS):**
1. **Reference audio is MANDATORY**
2. **Reference text is REQUIRED** (or empty for ASR)
3. **Cannot function without audio input**
4. **Designed specifically for voice cloning applications**

### **Testing Approach:**
1. **Always test models** rather than assume compatibility
2. **Use transformers auto-detection** for platform optimization
3. **Ignore VRAM specifications** - test on actual hardware
4. **Document real performance** from empirical testing

---

**Professional Note:**
This knowledge base provides accurate, creator-verified information for all 6 TTS models. The previous documentation incorrectly stated that models required input audio for basic text-to-speech generation. Only F5-TTS requires input audio as it's specifically designed as a voice cloning model. All other models function as standard TTS systems that can optionally use voice cloning features.
