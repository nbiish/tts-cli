# Installation Guide

## 🚀 **Quick Installation**

### **Option 1: Centralized Setup (Recommended)**

```bash
# Clone the repository
git clone https://github.com/nbiish/tts-cli.git
cd tts-cli

# Run the setup script (keeps everything centralized)
./scripts/setup-global.sh
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
cli-tts --list

# Test speech generation
cli-tts --text "Hello world" --output test.wav
```

## 🔧 **Environment Management**

The CLI automatically manages model environments:

- **Development Mode**: Uses `.model-envs/` in the project directory
- **Installed Mode**: Uses `~/.tts-cli/model-envs/` in your home directory

### **Create Model Environments**

```bash
# Create the KittenTTS environment (Python 3.11 + kittentts + onnxruntime)
cli-tts --create-environment kitten-tts

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

# Streamlined agent entry (--prompt is an alias for --text)
cli-tts --prompt "Task done. Next step: pin the Hugging Face kitten weights by digest before the next environment create." --output agent.wav
```

### **Model Selection**

```bash
# KittenTTS nano is the sole engine (default). 'auto' is an alias.
cli-tts --model kitten-tts-nano --text "Hello" --output hello.wav

# Set/check the default
cli-tts --set-default kitten-tts-nano
cli-tts --list
```

### **Voices**

KittenTTS ships 8 fixed built-in voices (no zero-shot cloning). Agent
speak omits `--voice` (CLI-owned random + 1.8× next chat). Operators may
pin a name:

```bash
# Operator override
cli-tts --text "Hello" --voice expr-voice-2-f --output voice.wav

# List all voices
cli-tts --list-voices
```

## 🛠️ **Troubleshooting**

### **Model Not Available**

If you get "Model not available" errors:

```bash
# Check environment status
cli-tts --list-environments

# Create missing environment
cli-tts --create-environment kitten-tts

# Test the model
cli-tts --test-model kitten-tts-nano
```

> KittenTTS runs on CPU — no accelerator or downloaded checkpoints are
> required. Weights download from Hugging Face on first run.

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
cli-tts --create-environment kitten-tts
```

## 📁 **Directory Structure**

After installation, the CLI creates:

```
~/.tts-cli/
├── model-envs/
│   ├── kitten-tts-env/   (Python 3.11 + kittentts + onnxruntime)
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
