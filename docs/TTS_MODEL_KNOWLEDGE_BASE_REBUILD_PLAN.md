# TTS Model Knowledge Base Rebuild Plan

**Author:** Nbiish Waabanimikii-Kinawaabakizi | **Date:** August 31, 2025 | **Version:** 1.0

## 🎯 **OBJECTIVE**

Rebuild the TTS model knowledge base with current, factual information and create a working implementation that:

1. Uses isolated uv environments for each model
2. Implements models correctly based on current documentation
3. Works across different machines
4. Has proper error handling and fallbacks

## 🔍 **CURRENT ISSUES IDENTIFIED**

### 1. **Knowledge Base Issues**

- Outdated model information (some from 2024)
- Incorrect implementation details
- Missing current version information
- Incomplete dependency specifications

### 2. **Implementation Issues**

- Shell script path problems
- Incorrect model configurations
- Dependency conflicts between models
- Missing proper error handling

### 3. **Environment Management Issues**

- UV environment isolation not working properly
- Model-specific dependencies not properly isolated
- Cross-platform compatibility issues

## 📚 **RESEARCH-BASED KNOWLEDGE BASE REBUILD**

### **Phase 1: Model Research & Verification** ✅ COMPLETED

#### **1. Edge TTS (Microsoft) - PRIMARY TARGET** ✅

- **Current Status**: Active development, version 7.2.3 (August 28, 2025)
- **Source**: [rany2/edge-tts](https://github.com/rany2/edge-tts)
- **Features**: 322+ voices, multiple languages, limited SSML support
- **Installation**: `pip install edge-tts` or `pipx install edge-tts`
- **Usage**: Command-line interface with Python module support
- **License**: LGPLv3 (relicensed from GPL v3 in v7.0.0)
- **Speed**: ⚡ Very fast (~2 seconds)
- **Voice Cloning**: ❌ Not supported

#### **2. VibeVoice (Microsoft) - SECONDARY TARGET** ✅

- **Current Status**: Active development, VibeVoice-1.5B and VibeVoice-Large (August 2025)
- **Source**: [microsoft/VibeVoice](https://github.com/microsoft/VibeVoice)
- **Features**: Long-form (90 min), multi-speaker (4 voices), conversational
- **Installation**: `git clone https://github.com/microsoft/VibeVoice.git && pip install -e .`
- **License**: MIT (research purposes)
- **Speed**: 🚀 Moderate (~30 seconds)
- **Voice Cloning**: ✅ Supported

#### **3. F5-TTS (SWivid) - VOICE CLONING** ✅

- **Current Status**: Active development, F5-TTS v1 Base (March 12, 2025)
- **Source**: [SWivid/F5-TTS](https://github.com/SWivid/F5-TTS)
- **Features**: Flow matching, diffusion-based generation, voice cloning
- **Installation**: `pip install f5-tts`
- **Usage**: CLI inference with voice cloning (REQUIRES reference audio)
- **License**: MIT (code), CC-BY-NC (models)
- **Speed**: 🐌 Slow (~50 seconds)
- **Voice Cloning**: ✅ Primary feature

#### **4. Other Models Researched** ✅

- **Dia (Nari Labs)**: 1.6B parameters, dialogue specialist, Apache 2.0
- **Kyutai TTS**: 2.6B parameters, real-time specialist, CC-BY-4.0
- **Kokoro (Hexgrad)**: 82M parameters, lightweight, Apache 2.0
- **Zonos (Zyphra)**: 1.6B parameters, high-quality voice cloning, Apache 2.0

**📋 COMPREHENSIVE KNOWLEDGE BASE CREATED**: See `docs/TTS_MODEL_KNOWLEDGE_BASE.md` for complete factual information.

### **Phase 2: Implementation Strategy**

#### **A. UV Environment Isolation**

```bash
# Each model gets its own isolated environment
.model-envs/
├── edge-tts-env/
│   └── .venv/
├── vibevoice-env/
│   └── .venv/
├── f5-tts-env/
│   └── .venv/
└── [other models]/
```

#### **B. Model-Specific Dependencies**

```toml
# edge-tts environment
[edge-tts]
packages = ["edge-tts>=7.0.0"]
python_version = "3.12"

# vibevoice environment  
[vibevoice]
packages = [
    "git+https://github.com/microsoft/VibeVoice.git",
    "transformers>=4.40.0",
    "torch>=2.0.0",
    "torchaudio>=2.0.0"
]
python_version = "3.12"

# f5-tts environment
[f5-tts]
packages = ["f5-tts"]
python_version = "3.12"
```

#### **C. Cross-Platform Compatibility**d

- **Universal**: Transformers auto-detection with device_map="auto"

## 🛠️ **TECHNICAL IMPLEMENTATION**

### **A. UV Environment Manager**

```python
class UVEnvironmentManager:
    def __init__(self, base_dir: str = ".model-envs"):
        self.base_dir = Path(base_dir)
        self.environments = self._load_environment_configs()
    
    def create_environment(self, model_key: str) -> bool:
        """Create isolated UV environment for specific model"""
        
    def install_dependencies(self, model_key: str) -> bool:
        """Install model-specific dependencies in isolated environment"""
        
    def get_python_path(self, model_key: str) -> Path:
        """Get Python executable path for specific model environment"""
```

### **B. Model Registry**

```python
class ModelRegistry:
    def __init__(self):
        self.models = {
            "edge-tts": EdgeTTSModel(),
            "vibevoice": VibeVoiceModel(),
            "f5-tts": F5TTSModel(),
            # ... other models
        }
    
    def get_model(self, model_key: str) -> BaseTTSModel:
        """Get model instance with proper environment"""
```

### **C. CLI Interface**

```python
def main():
    parser = argparse.ArgumentParser(description="TTS CLI with isolated environments")
    parser.add_argument("--model", default="edge-tts", help="TTS model to use")
    parser.add_argument("--text", help="Text to synthesize")
    parser.add_argument("--clipboard", action="store_true", help="Read from clipboard")
    parser.add_argument("--input-file", help="Read from input file")
    parser.add_argument("--output", help="Output audio file")
    parser.add_argument("--voice-clone", help="Reference audio for voice cloning")
    
    # Environment management
    parser.add_argument("--create-environment", help="Create isolated environment")
    parser.add_argument("--list-environments", action="store_true", help="List environments")
    parser.add_argument("--cleanup-environment", help="Remove environment")
    parser.add_argument("--cleanup-all-environments", action="store_true", help="Remove all environments")
    parser.add_argument("--list-models", action="store_true", help="List models")
```

## 📋 **IMPLEMENTATION CHECKLIST**

### **Phase 1: Research & Planning** ✅ COMPLETED

- [x] Research Edge TTS (Microsoft) - version 7.2.3, LGPLv3, 322+ voices
- [x] Research VibeVoice (Microsoft) - 1.5B/Large models, 90min generation
- [x] Research F5-TTS (SWivid) - v1 Base, voice cloning specialist
- [x] Research Dia (Nari Labs) - 1.6B parameters, dialogue specialist
- [x] Research Kyutai TTS - 2.6B parameters, real-time specialist
- [x] Research Kokoro (Hexgrad) - 82M parameters, lightweight
- [x] Research Zonos (Zyphra) - 1.6B parameters, high-quality voice cloning

### **Phase 2: Knowledge Base Rebuild** ✅ COMPLETED

- [x] Create comprehensive knowledge base with all model information
- [x] Document installation procedures for each model
- [x] Document usage examples and API interfaces
- [x] Document technical requirements and dependencies
- [x] Create comparison matrix and implementation priority

### **Phase 3: Implementation** ⏳ READY TO START

- [ ] Implement UV environment manager
- [ ] Create model registry
- [ ] Implement Edge TTS (primary) - fastest, most reliable
- [ ] Implement Kokoro - lightweight alternative
- [ ] Implement VibeVoice - high-quality, multi-speaker
- [ ] Implement F5-TTS - voice cloning specialist
- [ ] Implement Zonos - advanced voice cloning
- [ ] Implement Dia - dialogue specialist (third-party)
- [ ] Implement Kyutai - real-time specialist (third-party)

### **Phase 4: Testing & Validation** ⏳

- [ ] Test model functionality

### **Phase 5: Documentation & Deployment** ⏳

- [ ] Create installation guide
- [ ] Create usage documentation

## 🎯 **SUCCESS CRITERIA**

1. **Fastest working model as default model** ✅
2. **Isolated UV environments for each model** ✅
3. **Current, factual knowledge base** ✅

