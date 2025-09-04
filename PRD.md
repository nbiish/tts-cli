# Product Requirements Document (PRD) - TTS CLI

## 🎯 **EXECUTIVE SUMMARY**

The TTS CLI is a modern, clean command-line text-to-speech tool that provides access to multiple state-of-the-art TTS models through isolated UV environments. The tool enables users to generate high-quality speech from text using various models, with support for voice cloning, clipboard integration, and cross-platform compatibility.

## ⚠️ **CRITICAL IMPLEMENTATION SCOPE**

**WE IMPLEMENT ONLY THE FOLLOWING 8 MODELS - NO EXCEPTIONS:**

1. **Edge TTS** (Community) - Community-maintained Python package for text-to-speech conversion (NO API KEY REQUIRED)
2. **VibeVoice** https://github.com/rany2/edge-tts
3. **F5-TTS** (SWivid) - Voice cloning and synthesis model
4. **Dia** (Nari Labs) - Multilingual TTS model
5. **Marvis TTS** (Marvis-Labs) - Real-time voice cloning specialist
6. **Kyutai TTS** (Kyutai) - Open-source TTS model
7. **Kokoro** (Hexgrad) - Lightweight TTS model
8. **Zonos** (Zyphra) - Advanced voice cloning model

**ABSOLUTE RESTRICTIONS:**
- ❌ **NO SUPPLEMENTARY MODELS** - We do not add any additional TTS models beyond these 8
- ❌ **NO FAUX IMPLEMENTATIONS** - We do not create mock or placeholder implementations
- ❌ **NO CUSTOM MODELS** - We do not develop or integrate custom TTS models
- ❌ **NO MODEL SUBSTITUTIONS** - We do not replace any of these 8 models with alternatives
- ❌ **NO EXPERIMENTAL MODELS** - We do not add experimental or beta TTS models

**IMPLEMENTATION RULE:** If a model from this list cannot be implemented or becomes unavailable, we remove it entirely rather than substitute it with an alternative.

## 🚀 **IMPLEMENTATION PROGRESS**

### **Current Status: Phase 1 Complete**
- ✅ **Environment Management**: UV-based isolated environments working
- ✅ **Model Registry**: Dynamic model loading and registration system
- ✅ **Edge TTS Implementation**: First model implemented with fallback mechanism
- ✅ **Voice Management**: Voice listing and validation working
- ✅ **CLI Interface**: Full command-line interface operational

### **Edge TTS Status**
- **Implementation**: ✅ Complete - Uses standard edge-tts package API only
- **Environment**: ✅ Isolated UV environment created
- **Service Status**: ⚠️ Edge TTS service returning 401 errors (external service issue)
- **Error Handling**: ✅ Fails gracefully when service unavailable (no fake audio)
- **Testing**: ✅ Verified - CLI properly handles service failures
- **Next Steps**: Monitor service status, consider alternative TTS models for production use

### **Next Phase: Additional Models**
- 🔄 **VibeVoice**: Ready for implementation
- 🔄 **F5-TTS**: Ready for implementation  
- 🔄 **Dia**: Ready for implementation
- 🔄 **Marvis TTS**: Ready for implementation
- 🔄 **Kyutai**: Ready for implementation
- 🔄 **Kokoro**: Ready for implementation
- 🔄 **Zonos**: Ready for implementation

## 📋 **PRODUCT OVERVIEW**

### **Product Name**
TTS CLI - Command-Line Text-to-Speech Tool

### **Product Vision**
To provide a unified, reliable, and user-friendly command-line interface for accessing multiple TTS models with proper environment isolation and comprehensive voice management.

### **Target Users**
- **Developers** building applications with TTS capabilities
- **Content Creators** needing high-quality voice generation
- **Researchers** working with speech synthesis
- **Accessibility Advocates** creating voice-enabled tools
- **Indigenous Language Preservationists** working with voice synthesis

### **Key Value Propositions**
- **Unified Interface**: Single CLI for multiple TTS models
- **Environment Isolation**: No dependency conflicts between models
- **Voice Cloning**: High-quality voice cloning capabilities
- **Cross-Platform**: Works on macOS, Linux, and Windows
- **Easy Setup**: Simple installation and environment management

---

## 🎯 **PRODUCT GOALS & OBJECTIVES**

### **Primary Goals**
1. **Reliability**: Provide consistent, error-free TTS generation
2. **Performance**: Fast, efficient speech synthesis
3. **Quality**: High-quality audio output across all models
4. **Usability**: Intuitive command-line interface
5. **Maintainability**: Clean, modular architecture

### **Success Metrics**
- **Installation Success Rate**: >95% successful installations
- **Model Availability**: 100% of supported models working
- **User Satisfaction**: Positive feedback on voice quality
- **Performance**: <5 seconds for typical text generation
- **Reliability**: <1% failure rate in production use

---

## 🏗️ **TECHNICAL ARCHITECTURE**

### **Core Components**

```
TTS CLI
├── CLI Interface (cli.py)
├── Model Registry (core/model_registry.py)
├── Environment Manager (core/environment_manager.py)
├── Voice Manager (core/voice_manager.py)
└── Model Implementations
    ├── EdgeTTSModel
    ├── VibeVoiceModel
    ├── F5TTSModel
    ├── DiaModel
    ├── MarvisTTSModel
    ├── KyutaiModel
    ├── KokoroModel
    └── ZonosModel
```

### **Environment Isolation Strategy**
```
.model-envs/
├── edge-tts-env/
│   └── .venv/
├── vibevoice-env/
│   └── .venv/
├── f5-tts-env/
│   └── .venv/
├── dia-env/
│   └── .venv/
├── marvis-tts-env/
│   └── .venv/
├── kyutai-env/
│   └── .venv/
├── kokoro-env/
│   └── .venv/
└── zonos-env/
    └── .venv/
```

---

## 🤖 **SUPPORTED MODELS & REQUIREMENTS**

### **1. Edge TTS (Community) - PRIMARY TARGET**

#### **Model Specifications**
- **Version**: 7.2.3 (August 28, 2025)
- **Parameters**: ```uv pip install edge-tts```
- **Speed**: ⚡ Very fast (~2 seconds)
- **Quality**: ✅ High quality neural voices
- **GPU Required**: ❌ No (CPU-based service)

#### **Voice Information**
- **Total Voices**: 322+ voices
- **Languages**: Extensive multilingual support
- **English Voices**: 50+ voices including:
  - `en-US-AriaNeural` (Female, General, Friendly)
  - `en-US-JennyNeural` (Female, General, Friendly)
  - `en-US-GuyNeural` (Male, General, Friendly)
  - `en-US-DavisNeural` (Male, General, Friendly)
  - `en-US-AmberNeural` (Female, General, Friendly)
  - `en-US-AnaNeural` (Female, General, Friendly)
  - `en-US-AshleyNeural` (Female, General, Friendly)
  - `en-US-BrandonNeural` (Male, General, Friendly)
  - `en-US-ChristopherNeural` (Male, General, Friendly)
  - `en-US-CoraNeural` (Female, General, Friendly)
  - `en-US-ElizabethNeural` (Female, General, Friendly)
  - `en-US-EricNeural` (Male, General, Friendly)
  - `en-US-JacobNeural` (Male, General, Friendly)
  - `en-US-JaneNeural` (Female, General, Friendly)
  - `en-US-JasonNeural` (Male, General, Friendly)
  - `en-US-MichelleNeural` (Female, General, Friendly)
  - `en-US-MonicaNeural` (Female, General, Friendly)
  - `en-US-NancyNeural` (Female, General, Friendly)
  - `en-US-RogerNeural` (Male, General, Friendly)
  - `en-US-SaraNeural` (Female, General, Friendly)
  - `en-US-TonyNeural` (Male, General, Friendly)

#### **Usage Requirements**
- **Input**: Text only
- **Output**: MP3, WAV with SRT subtitlesd
- **Implementation**: Extremely simple Python package

#### **Voice Cloning**
- **Supported**: ❌ Not supported
- **Alternative**: Use voice selection from available voices

---

### **2. VibeVoice (Microsoft) - SECONDARY TARGET**

#### **Model Specifications**
- **Version**: VibeVoice-1.5B and VibeVoice-Large (August 2025)
- **License**: MIT (research purposes)
- **Parameters**: 1.5B / Large variant
- **Speed**: 🚀 Moderate (~30 seconds)
- **Quality**: ✅ High quality, expressive speech

#### **Voice Information**
- **Context Length**: 64K tokens (1.5B), 32K tokens (Large)
- **Generation Length**: ~90 minutes (1.5B), ~45 minutes (Large)
- **Speakers**: Up to 4 distinct speakers
- **Languages**: English, Chinese (with some instability in Chinese)
- **Voice Cloning**: ✅ Supported

#### **Usage Requirements**
- **Input**: Text + optional speaker embedding
- **Output**: High-quality audio
- **Network**: Internet connection for model download
- **Dependencies**: `transformers>=4.40.0`, `torch>=2.0.0`, `torchaudio>=2.0.0`, `flash-attn>=2.0.0`

#### **Voice Cloning**
- **Supported**: ✅ Yes
- **Requirements**: Speaker embedding or reference audio
- **Quality**: High-quality voice cloning

---

### **3. F5-TTS (SWivid) - VOICE CLONING SPECIALIST**

#### **Model Specifications**
- **Version**: F5-TTS v1 Base (March 12, 2025)
- **Speed**: 🐌 Slow (~50 seconds)
- **Quality**: ✅ High quality voice cloning

#### **Voice Information**
- **Voice Cloning**: ✅ Primary feature
- **Reference Audio**: 5-30 seconds required
- **Languages**: Multilingual support

#### **Usage Requirements**
- **Input**: Text + reference audio (REQUIRED)
- **Output**: High-quality cloned voice
- **Dependencies**: `f5-tts`

#### **Voice Cloning**
- **Supported**: ✅ Yes (primary feature)
- **Requirements**: Reference audio (5-30 seconds)
- **Quality**: High-quality voice cloning

---

### **4. Kokoro (Hexgrad) - LIGHTWEIGHT SPECIALIST**

#### **Model Specifications**
- **Version**: Kokoro-82M v1.0 (January 27, 2025)
- **Parameters**: 82M (extremely lightweight)
- **Speed**: ⚡ Very fast

#### **Voice Information**
- **Languages**: English, Chinese, French, Japanese, Hindi, Italian, Portuguese, Spanish
- **English Voices**: 20+ voices including:
  - `af_heart` (Female, American)
  - `af_aoede` (Female, American)
  - `af_bella` (Female, American)
  - `af_jessica` (Female, American)
  - `af_kore` (Female, American)
  - `af_nicole` (Female, American)
  - `af_nova` (Female, American)
  - `af_river` (Female, American)
  - `af_sarah` (Female, American)
  - `af_sky` (Female, American)
  - `am_adam` (Male, American)
  - `am_echo` (Male, American)
  - `am_eric` (Male, American)
  - `am_fenrir` (Male, American)
  - `am_liam` (Male, American)
  - `am_michael` (Male, American)
  - `am_onyx` (Male, American)
  - `am_puck` (Male, American)
  - `am_santa` (Male, American)
  - `bf_alice` (Female, British)
  - `bf_emma` (Female, British)
  - `bf_isabella` (Female, British)
  - `bf_lily` (Female, British)
  - `bm_daniel` (Male, British)
  - `bm_fable` (Male, British)
  - `bm_george` (Male, British)
  - `bm_lewis` (Male, British)

#### **Usage Requirements**
- **Input**: Text only
- **Output**: WAV files (24kHz)
- **Network**: Internet connection for model download
- **Dependencies**: `kokoro>=0.9.4`, `soundfile>=0.12.0`, `espeak-ng`

#### **Voice Cloning**
- **Supported**: ❌ Not supported
- **Alternative**: Use voice selection from available voices

---

### **5. Zonos (Zyphra) - HIGH-QUALITY VOICE CLONING**

#### **Model Specifications**
- **Version**: Zonos-v0.1 (August 2025)d
- **Parameters**: 1.6B (Transformer and SSM variants)d
- **Quality**: ✅ High quality, expressived
- **Memory**: High

#### **Voice Information**
- **Languages**: English, Japanese, Chinese, French, German
- **Voice Cloning**: ✅ Excellent (5-30 seconds reference audio)
- **Output**: 44kHz native
- **Training Data**: 200k+ hours multilingual speech

#### **Usage Requirements**
- **Input**: Text + reference audio (5-30 seconds)
- **Output**: High-quality audio (44kHz)d
- **Dependencies**: `torch>=2.0.0`, `torchaudio>=2.0.0`, `espeak-ng`

#### **Voice Cloning**
- **Supported**: ✅ Yes (excellent quality)
- **Requirements**: Reference audio (5-30 seconds)
- **Quality**: High-quality voice cloning

---

### **6. Dia (Nari Labs) - DIALOGUE SPECIALIST**

#### **Model Specifications**
- **Version**: Dia 1.6B (April 21, 2025)d
- **Parameters**: 1.6B
- **Speed**: 🚀 Moderate
- **Quality**: ✅ High quality, natural dialogue

#### **Voice Information**
- **Specialization**: Dialogue generation, multi-speaker conversations
- **Languages**: English (primary)
- **Context Length**: ~800 seconds of speech
- **Voice Cloning**: ✅ Supported

#### **Usage Requirements**
- **Input**: Text + optional speaker embedding
- **Output**: High-quality dialogue audio
- **Dependencies**: `torch`, `transformers`

#### **Voice Cloning**
- **Supported**: ✅ Yes
- **Requirements**: Speaker embedding or reference audio
- **Quality**: High-quality dialogue generation

---

### **7. Marvis TTS (Marvis-Labs) - REAL-TIME VOICE CLONING SPECIALIST**

#### **Model Specifications**
- **Version**: Marvis-TTS-250m-v0.1 (August 26, 2025)
- **Parameters**: 250M (multimodal backbone) + 60M (audio decoder)
- **Speed**: ⚡ Very fast (real-time streaming capable)
- **Quality**: ✅ High quality, natural speech flow

#### **Voice Information**
- **Languages**: English (primary), German, Portuguese, French, Mandarin (coming soon)
- **Voice Cloning**: ✅ Excellent (10 seconds reference audio)
- **Specialization**: Real-time streaming, edge deployment, voice cloning
- **Architecture**: Sesame CSM-1B with Kyutai mimi codec
- **Output**: 24kHz audio

#### **Usage Requirements**
- **Input**: Text + optional reference audio (10 seconds for voice cloning)
- **Output**: High-quality streaming audio
- **Dependencies**: `mlx-audio` or `transformers`, `torch`

#### **Voice Cloning**
- **Supported**: ✅ Yes (primary feature)
- **Requirements**: 10 seconds of reference audio
- **Quality**: High-quality voice cloning with natural flow

---

### **8. Kyutai TTS - REAL-TIME SPECIALIST**

#### **Model Specifications**
- **Version**: Kyutai 2.6B (September 2024)
- **License**: CC-BY-4.0
- **Parameters**: 2.6B
- **Speed**: ⚡ Very fast (real-time capable)
- **Quality**: ✅ Good quality for real-time use

#### **Voice Information**
- **Languages**: English, French
- **Word Error Rate**: 6.4% (English), higher for French
- **Specialization**: Real-time applications, low latency
- **Voice Cloning**: ❌ Not supported

#### **Usage Requirements**
- **Input**: Text only
- **Output**: Real-time audio
- **Dependencies**: `torch`, `transformers`

#### **Voice Cloning**
- **Supported**: ❌ Not supported
- **Alternative**: Use voice selection from available voices

---

## 🎯 **FUNCTIONAL REQUIREMENTS**

### **Core Features**

#### **1. Text-to-Speech Generation**
- **Input Methods**:
  - Direct text input via `--text` parameter
  - Clipboard input via `--clipboard` flag
  - File input via `--input-file` parameter
- **Output Formats**: WAV, MP3 (model-dependent)
- **Model Selection**: Via `--model` parameter
- **Voice Selection**: Via `--voice` parameter (model-dependent)

#### **2. Voice Cloning**
- **Supported Models**: VibeVoice, F5-TTS, Zonos, Dia, Marvis TTS
- **Input Requirements**: Reference audio file via `--voice-clone` parameter
- **Audio Requirements**: 5-30 seconds of clean reference audio (10 seconds for Marvis TTS)
- **Output Quality**: High-quality cloned voice

#### **3. Environment Management**
- **Environment Creation**: `--create-environment MODEL_NAME`
- **Environment Listing**: `--list-environments`
- **Environment Testing**: `--test-model MODEL_NAME`
- **Environment Cleanup**: `--cleanup-environment MODEL_NAME`

#### **4. Model Information**
- **Model Listing**: `--list-models`
- **Voice Listing**: `--list-voices` (model-specific)
- **Model Status**: Environment and dependency status
- **Help System**: `--help` with model-specific information

#### **5. Voice Library Management**
- **Voice Library**: `--voice-library` for voice library management

---

## 🎨 **USER EXPERIENCE REQUIREMENTS**

### **Command-Line Interface**

#### **Basic Usage**
```bash
# Simple text-to-speech
cli-tts --text "Hello, world!" --output hello.wav

# Model selection
cli-tts --model edge-tts --text "Hello, world!" --output hello.wav

# Voice selection
cli-tts --model edge-tts --voice en-US-AriaNeural --text "Hello, world!" --output hello.wav

# Clipboard input
cli-tts --clipboard --output speech.wav

# Voice cloning
cli-tts --model f5-tts --text "Hello, world!" --voice-clone reference.wav --output cloned.wav
```

#### **Environment Management**
```bash
# List available models
cli-tts --list-models

# List environments
cli-tts --list-environments

# Create environment
cli-tts --create-environment edge-tts

# Cleanup
cli-tts --cleanup-environment edge-tts
```

#### **Help System**
```bash
# General help
cli-tts --help

# Model-specific help
cli-tts --help --model edge-tts

# Voice information
cli-tts --list-voices --model edge-tts
```

### **Error Handling**
- **Clear Error Messages**: Descriptive error messages with solutions
- **Graceful Degradation**: Fallback to available models when possible
- **Recovery Suggestions**: Specific commands to resolve issues
- **Logging**: Detailed logging for debugging

---

## 🔧 **TECHNICAL REQUIREMENTS**

### **Dependencies**

#### **Core Dependencies**
- **uv**: Package manager for environment management
- **pyperclip**: Clipboard integration
- **soundfile**: Audio file handling
- **numpy**: Numerical operations
- **rich**: Terminal output formatting

#### **Model-Specific Dependencies**
- **Edge TTS**: 
- **VibeVoice**: 
- **F5-TTS**: 
- **Kokoro**: 
- **Zonos**: 
- **Dia**: 
- **Marvis TTS**: 
- **Kyutai**: 

---

## 📊 **SUCCESS CRITERIA**

### **Functional Success**
- ✅ All 8 models successfully integrated
- ✅ Environment isolation working correctly
- ✅ Voice cloning functional for supported models
- ✅ Cross-platform compatibility achieved
- ✅ Performance targets met

### **User Experience Success**
- ✅ Installation success rate >95%
- ✅ User satisfaction with voice quality
- ✅ Clear error messages and recovery guidance
- ✅ Intuitive command-line interface
- ✅ Comprehensive help system

### **Technical Success**
- ✅ Clean, modular architecture
- ✅ Proper dependency management
- ✅ Efficient resource usage
- ✅ Comprehensive testing coverage
- ✅ Documentation completeness

### **Model Implementation Constraints**
- **STRICT MODEL LIMIT**: Only the 8 specified models will be implemented
- **NO SUBSTITUTIONS**: If a model cannot be implemented, it is removed entirely
- **NO SUPPLEMENTARY MODELS**: No additional TTS models beyond the specified 8
- **NO FAUX IMPLEMENTATIONS**: No mock or placeholder implementations
- **NO CUSTOM MODELS**: No custom TTS model development or integration
- **NO EXPERIMENTAL MODELS**: No beta or experimental TTS models

---

## 📚 **DOCUMENTATION REQUIREMENTS**

### **User Documentation**
- **README.md**: Comprehensive usage guide
- **Installation Guide**: Step-by-step installation instructions
- **Model Guide**: Detailed information about each model
- **Voice Guide**: Voice selection and management guide
- **Troubleshooting Guide**: Common issues and solutions

---
