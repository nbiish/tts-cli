# TTS Quick Reference - Input Audio Requirements

**Author:** Nbiish Waabanimikii-Kinawaabakizi | **Date:** August 28, 2025 | **Version:** 3.0

## 🚨 CRITICAL CORRECTION: Input Audio Requirements

**The previous documentation was INCORRECT.** After reviewing the official repositories for all 6 TTS models, here are the **actual** requirements:

## 📊 Model Input Audio Requirements

| Model | Basic TTS | Voice Cloning | Notes |
|-------|-----------|---------------|-------|
| **F5-TTS** | ❌ **REQUIRES** | ✅ Advanced | Voice cloning model by design |
| **Edge TTS** | ✅ **NO** | ❌ No | Standard TTS service |
| **Dia** | ✅ **NO** | ✅ Basic | Standard TTS + optional cloning |
| **Kyutai** | ✅ **NO** | ✅ Advanced | Standard TTS + optional cloning |
| **Kokoro** | ✅ **NO** | ✅ Basic | Standard TTS + optional cloning |
| **VibeVoice** | ✅ **NO** | ✅ Advanced | Standard TTS + optional cloning |

## 🔍 Key Findings

### **❌ INCORRECT Previous Documentation:**
- Claimed all models required input audio for basic TTS
- This was based on old iterations or incorrect implementations
- Misled users about model capabilities

### **✅ CORRECT Current Documentation:**
- **Only F5-TTS requires input audio** (it's a voice cloning model)
- **5 out of 6 models work as standard TTS** without input audio
- **Voice cloning is optional** for most models
- **All models have been verified** from official repositories

## 🎯 Implementation Implications

### **For Basic Text-to-Speech:**
```bash
# These models work with TEXT ONLY:
python -m tts_cli.cli_tts --model edge-tts --text "Hello world" --output hello.wav
python -m tts_cli.cli_tts --model dia --text "Hello world" --output hello.wav
python -m tts_cli.cli_tts --model kyutai --text "Hello world" --output hello.wav
python -m tts_cli.cli_tts --model kokoro --text "Hello world" --output hello.wav
python -m tts_cli.cli_tts --model vibevoice --text "Hello world" --output hello.wav
```

### **For Voice Cloning (Optional):**
```bash
# Voice cloning requires input audio (optional for most models):
python -m tts_cli.cli_tts --model f5-tts --text "Hello world" --voice-clone ref.wav --output cloned.wav
python -m tts_cli.cli_tts --model dia --text "Hello world" --voice-clone ref.wav --output cloned.wav
# etc.
```

## 🔧 Required Implementation Changes

### **1. Fix F5-TTS Implementation:**
- **Current Issue**: Trying to run without reference audio
- **Solution**: Always require `--voice-clone` parameter
- **Note**: This model cannot function as standard TTS

### **2. Enable Standard TTS for Other Models:**
- **Current Issue**: Incorrectly requiring input audio
- **Solution**: Allow text-only input for basic TTS
- **Benefit**: Users can generate speech without reference files

### **3. Make Voice Cloning Optional:**
- **Current Issue**: Treating all models as voice cloning models
- **Solution**: Voice cloning as optional enhancement
- **Benefit**: More flexible usage patterns

## 📚 Source Verification

All information has been verified from official repositories:

- **F5-TTS**: [SWivid/F5-TTS](https://github.com/SWivid/F5-TTS) - Confirmed voice cloning model
- **Edge TTS**: [rany2/edge-tts](https://github.com/rany2/edge-tts) - Confirmed standard TTS
- **Dia**: [nari-labs/dia](https://github.com/nari-labs/dia) - Confirmed standard TTS + optional cloning
- **Kyutai**: [kyutai-labs/delayed-streams-modeling](https://github.com/kyutai-labs/delayed-streams-modeling) - Confirmed standard TTS + optional cloning
- **Kokoro**: [hexgrad/kokoro](https://github.com/hexgrad/kokoro) - Confirmed standard TTS + optional cloning
- **VibeVoice**: [microsoft/VibeVoice](https://github.com/microsoft/VibeVoice) - Confirmed standard TTS + optional cloning

## 🎉 Benefits of Correction

### **User Experience:**
- **Simpler usage** for basic TTS needs
- **No unnecessary file requirements** for standard speech generation
- **Clear distinction** between TTS and voice cloning use cases

### **Implementation:**
- **More accurate model behavior** matching official specifications
- **Better error handling** for missing parameters
- **Cleaner CLI interface** with appropriate defaults

### **Documentation:**
- **Creator-verified accuracy** from official sources
- **Clear usage patterns** for each model type
- **Proper feature categorization** (TTS vs. Voice Cloning)

---

**Professional Note:**
This correction ensures our TTS CLI tool accurately reflects the capabilities of each model as intended by their creators. Users can now generate speech from text without unnecessary audio file requirements, while still having access to voice cloning features when desired.
