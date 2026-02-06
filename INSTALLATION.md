# Installation Guide

## 🚀 **Quick Installation**

### **Option 1: Centralized Setup (Recommended)**

```bash
# Clone the repository
git clone https://github.com/nbiish/tts-cli.git
cd tts-cli

# Run the setup script (keeps everything centralized)
./setup-global.sh
```

**🎯 Benefits of Centralized Setup:**
- All model environments stay in the repo directory
- No cluttering your home directory
- Changes to code are immediately available everywhere
- Easy to update and maintain

### **Option 2: Install from PyPI (Coming Soon)**

```bash
# Install from PyPI (when published)
pip install tts-cli
```

## ✅ **Verification**

After installation, verify the CLI works from anywhere:

```bash
# Test from any directory
cd /tmp
cli-tts --list-models

# Test speech generation
cli-tts --text "Hello world" --output test.wav
```

## 🔧 **Environment Management**

The CLI automatically manages model environments:

- **Development Mode**: Uses `.model-envs/` in the project directory
- **Installed Mode**: Uses `~/.tts-cli/model-envs/` in your home directory

### **Create Model Environments**

```bash
# Create environment for a specific model
cli-tts --create-environment coqui-tts
cli-tts --create-environment vibevoice
cli-tts --create-environment zonos

# List all environments
cli-tts --list-environments
```

## 🎯 **Usage Examples**

### **Basic Text-to-Speech**

```bash
# Simple text input
cli-tts --text "Hello, world!" --output hello.wav

# From clipboard
cli-tts --clipboard --output speech.wav

# From file
cli-tts --input-file input.txt --output speech.wav
```

### **Model Selection**

```bash
# Use specific model
cli-tts --model coqui-tts --text "Hello" --output hello.wav
cli-tts --model vibevoice --text "Hello" --output hello.wav
cli-tts --model zonos --text "Hello" --output hello.wav
```

### **Voice Selection**

```bash
# List available voices
cli-tts --list-voices --model coqui-tts

# Use specific voice
cli-tts --model coqui-tts --voice "tts_models/en/ljspeech/tacotron2-DDC_ph" --text "Hello" --output hello.wav
```

### **Voice Cloning**

```bash
# Clone a voice (requires reference audio)
cli-tts --model coqui-tts --text "Hello" --voice-clone reference.wav --output cloned.wav
```

## 🛠️ **Troubleshooting**

### **Model Not Available**

If you get "Model not available" errors:

```bash
# Check environment status
cli-tts --list-environments

# Create missing environment
cli-tts --create-environment MODEL_NAME

# Test specific model
cli-tts --test-model MODEL_NAME
```

### **Permission Issues**

If you encounter permission issues:

```bash
# Check if CLI is installed correctly
which cli-tts

# Reinstall if needed
uv pip install -e .
```

### **Environment Issues**

If environments are not found:

```bash
# Check environment directory
ls -la ~/.tts-cli/model-envs/

# Clean up and recreate
cli-tts --cleanup-all-environments
cli-tts --create-environment coqui-tts
```

## 📁 **Directory Structure**

After installation, the CLI creates:

```
~/.tts-cli/
├── model-envs/
│   ├── coqui-tts-env/
│   ├── vibevoice-env/
│   ├── zonos-env/
│   └── environments.json
```

## 🔄 **Updates**

To update the CLI:

```bash
# Pull latest changes
git pull origin main

# Reinstall
uv pip install -e .
```

## 🗑️ **Uninstallation**

To remove the CLI:

```bash
# Uninstall package
uv pip uninstall tts-cli

# Remove environments (optional)
rm -rf ~/.tts-cli/
```
