# Centralized Design - TTS CLI

**Date**: September 7, 2025  
**Status**: ✅ **IMPLEMENTED** - Centralized Design with Global Access

## 🎯 **Design Philosophy**

The TTS CLI uses a **centralized design** where all model environments and configurations stay in the repository directory, while providing global access through symlinks and proper path resolution.

## 🏗️ **Architecture**

### **Centralized Storage**
```
/Volumes/1tb-sandisk/code-external/tts-cli/
├── .model-envs/                    # All model environments here
│   ├── coqui-tts-env/
│   ├── vibevoice-env/
│   ├── zonos-env/
│   └── environments.json
├── tts_cli/                        # Source code
├── setup-global.sh                 # Setup script
└── pyproject.toml                  # Package configuration
```

### **Global Access**
- **CLI Command**: `cli-tts` works from any directory
- **Environment Resolution**: Always points to repo's `.model-envs/`
- **No Cluttering**: No files created in home directory or system paths

## ✅ **Benefits**

### **1. No System Cluttering**
- ❌ No `~/.tts-cli/` directory
- ❌ No scattered model environments
- ❌ No duplicate installations
- ✅ Everything stays in the repo

### **2. Immediate Updates**
- ✅ Code changes are immediately available everywhere
- ✅ No need to reinstall or update multiple locations
- ✅ Single source of truth for all environments

### **3. Easy Maintenance**
- ✅ All environments in one place
- ✅ Easy to backup or move the entire setup
- ✅ Clear separation from system files

### **4. Development Friendly**
- ✅ Works in development mode
- ✅ Easy to iterate and test changes
- ✅ Version control includes all environments

## 🔧 **Technical Implementation**

### **Environment Manager**
```python
# Always finds project root
while current_dir != current_dir.parent:
    if (current_dir / "pyproject.toml").exists():
        project_root = current_dir
        break
    current_dir = current_dir.parent

# Always uses project root's .model-envs
self.base_path = project_root / ".model-envs"
```

### **Path Resolution**
```python
# Always resolves relative paths to project root
if not path.is_absolute():
    if self.project_root:
        path = self.project_root / path
```

### **Global Installation**
```bash
# Install in development mode (symlinks to repo)
uv pip install -e .

# CLI works from anywhere but uses repo's environments
cd /tmp
cli-tts --text "Hello" --output test.wav
```

## 🚀 **Setup Process**

### **1. Clone Repository**
```bash
git clone https://github.com/nbiish/tts-cli.git
cd tts-cli
```

### **2. Run Setup Script**
```bash
./setup-global.sh
```

This script:
- Installs the package in development mode
- Creates necessary symlinks
- Tests the installation
- Shows usage instructions

### **3. Use from Anywhere**
```bash
# From any directory
cd /tmp
cli-tts --text "Hello world" --output speech.wav
```

## 📊 **Comparison**

| Aspect | Centralized Design | Distributed Design |
|--------|-------------------|-------------------|
| **Storage** | Single repo directory | Scattered across system |
| **Updates** | Immediate | Requires reinstallation |
| **Maintenance** | Easy | Complex |
| **Cluttering** | None | System directories cluttered |
| **Development** | Perfect | Cumbersome |
| **Backup** | Single directory | Multiple locations |

## 🎯 **Usage Examples**

### **Basic Usage**
```bash
# Works from any directory
cd /tmp
cli-tts --text "Hello world" --output hello.wav

cd ~
cli-tts --clipboard --output speech.wav
```

### **Environment Management**
```bash
# All environments stay in repo
cli-tts --list-environments
cli-tts --create-environment coqui-tts
```

### **Development Workflow**
```bash
# Make changes to code
vim tts_cli/cli.py

# Changes are immediately available everywhere
cd /tmp
cli-tts --text "Updated code" --output test.wav
```

## 🔍 **Verification**

### **Check Centralization**
```bash
# All environments in repo
ls -la /path/to/tts-cli/.model-envs/

# No cluttering in home
ls -la ~/.tts-cli/  # Should not exist
```

### **Test Global Access**
```bash
# From different directories
cd /tmp && cli-tts --list-models
cd ~ && cli-tts --text "Test" --output test.wav
```

## 🎉 **Conclusion**

The centralized design provides the best of both worlds:
- **Global Access**: Use `cli-tts` from anywhere
- **No Cluttering**: Everything stays in the repo
- **Easy Development**: Changes are immediately available
- **Simple Maintenance**: Single directory to manage

This approach is perfect for development, testing, and production use while keeping the system clean and organized.
