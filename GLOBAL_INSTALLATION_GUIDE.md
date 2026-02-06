# Global TTS CLI Installation Guide

This guide provides comprehensive instructions for installing the TTS CLI tool system-wide, enabling access from any directory on your system.

## Quick Start

Execute these commands in sequence:

```bash
# 1. Clone and navigate to the project
git clone <repository-url>
cd tts-cli

# 2. Install project dependencies
uv sync

# 3. Install the CLI globally using the bash wrapper approach
sudo cp tts-cli-global.sh /usr/local/bin/tts-cli
sudo chmod +x /usr/local/bin/tts-cli
```

## Verification

Test the global installation:

```bash
# Test from any directory
cd ~
tts-cli --help

# Test speech generation
tts-cli --text "Hello world" --output ~/test-audio.wav

# Test with clipboard (copy text first)
tts-cli --clipboard --output ~/clipboard-test.wav
```

## Installation Methods

### Method 1: Bash Wrapper Script (Recommended)

This method creates a global `tts-cli` command that works from any directory.

#### Create the Wrapper Script

The project includes a pre-configured wrapper script `tts-cli-global.sh`:

```bash
#!/bin/bash
# Global TTS CLI wrapper script
/Users/nbiish/miniconda3/bin/python -m tts_cli.cli "$@"
```

#### Install Globally

```bash
# Copy to system PATH
sudo cp tts-cli-global.sh /usr/local/bin/tts-cli

# Make executable
sudo chmod +x /usr/local/bin/tts-cli

# Verify installation
which tts-cli
# Should output: /usr/local/bin/tts-cli
```

### Method 2: Symbolic Link (Alternative)

If you prefer symbolic links:

```bash
# From project directory
sudo ln -sf "$(pwd)/tts-cli-global.sh" /usr/local/bin/tts-cli
```

## Environment Requirements

### Python Environment

The wrapper script uses the conda Python installation:

- **Required**: `/Users/nbiish/miniconda3/bin/python`
- **Package**: `tts_cli` must be installed in this environment

### Package Installation

Ensure the TTS CLI package is available:

```bash
# Check if package is installed
/Users/nbiish/miniconda3/bin/python -c "import tts_cli; print('✅ tts_cli package found')"

# If needed, install in conda environment
conda activate base
pip install -e /Volumes/1tb-sandisk/code-external/tts-cli
```

## Testing Different Scenarios

### Basic Functionality Test

```bash
# From project directory
tts-cli --help

# From home directory
cd ~
tts-cli --help

# From temporary directory
cd /tmp
tts-cli --help
```

### Speech Generation Tests

```bash
# Short text test
tts-cli --text "This is a test" --output ~/short-test.wav

# Long text test with clipboard
# 1. Copy long text to clipboard
# 2. Run command
tts-cli --clipboard --output ~/long-test.wav

# Model specification
tts-cli --text "Testing specific model" --model vibevoice --output ~/model-test.wav
```

### Performance Verification

Expected results for VibeVoice model:

- **Processing**: 1.5-2.5x real-time factor
- **Quality**: 24kHz output, natural speech
- **File sizes**: ~100-150KB per 5 seconds of audio
- **Hardware**: Apple MPS acceleration when available

## Troubleshooting

### Common Issues

1. **Command not found**

   ```bash
   # Check if file exists
   ls -la /usr/local/bin/tts-cli
   
   # Check permissions
   file /usr/local/bin/tts-cli
   ```

2. **Permission denied**

   ```bash
   # Fix permissions
   sudo chmod +x /usr/local/bin/tts-cli
   ```

3. **Python not found**

   ```bash
   # Verify Python path in wrapper script
   head -n 3 /usr/local/bin/tts-cli
   
   # Check if Python exists
   ls -la /Users/nbiish/miniconda3/bin/python
   ```

4. **Module not found**

   ```bash
   # Test Python module directly
   /Users/nbiish/miniconda3/bin/python -m tts_cli.cli --help
   ```

### Uninstallation

To remove the global installation:

```bash
# Remove the wrapper script
sudo rm /usr/local/bin/tts-cli

# Verify removal
which tts-cli
# Should output: tts-cli not found
```

## Advanced Configuration

### Custom Python Path

If using a different Python installation, edit the wrapper script:

```bash
# Edit the wrapper script
sudo nano /usr/local/bin/tts-cli

# Change the Python path:
#!/bin/bash
/path/to/your/python -m tts_cli.cli "$@"
```

### System-wide Environment Variables

For additional configuration:

```bash
# Add to ~/.bashrc or ~/.zshrc
export TTS_CLI_MODEL="vibevoice"
export TTS_CLI_OUTPUT_DIR="~/audio-output"
```

## Verification Checklist

After installation, verify these work:

- [ ] `tts-cli --help` shows usage information
- [ ] `tts-cli --text "test" --output ~/test.wav` creates audio file
- [ ] Command works from different directories (home, /tmp, etc.)
- [ ] VibeVoice model generates speech successfully
- [ ] Clipboard functionality works with copied text
- [ ] File outputs have expected sizes and quality

## Technical Details

### File Locations

- **Wrapper Script**: `/usr/local/bin/tts-cli`
- **Python Executable**: `/Users/nbiish/miniconda3/bin/python`
- **Project Location**: `/Volumes/1tb-sandisk/code-external/tts-cli`
- **Model Cache**: `~/.cache/modelscope/`

### Dependencies

- **Core**: Python 3.9+, conda environment
- **Models**: ModelScope VibeVoice 1.5B
- **Hardware**: Apple MPS for acceleration
- **System**: macOS with bash/zsh shell

This installation method provides reliable system-wide access to the TTS CLI while maintaining proper environment isolation and dependency management.
