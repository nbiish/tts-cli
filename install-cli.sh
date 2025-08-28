#!/bin/bash

# TTS CLI Global Installer (Shell Version)
# ========================================
# 
# This script installs the TTS CLI tool globally so users can access
# the 'cli-tts' command from anywhere on their system.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI_MODULE="tts_cli.cli_tts"
COMMAND_NAME="cli-tts"

echo -e "${BLUE}🚀 TTS CLI Global Installer${NC}"
echo "========================================"

# Check if TTS CLI is set up
if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    echo -e "${RED}❌ TTS CLI not set up. Please run 'python setup.py' first.${NC}"
    exit 1
fi

# Determine system and find install path
SYSTEM=$(uname -s | tr '[:upper:]' '[:lower:]')
HOME_DIR="$HOME"

if [[ "$SYSTEM" == "darwin" ]]; then
    # macOS
    INSTALL_PATHS=(
        "$HOME_DIR/.local/bin"
        "$HOME_DIR/bin"
        "/usr/local/bin"
        "/opt/homebrew/bin"
    )
elif [[ "$SYSTEM" == "linux" ]]; then
    # Linux
    INSTALL_PATHS=(
        "$HOME_DIR/.local/bin"
        "$HOME_DIR/bin"
        "/usr/local/bin"
        "/usr/bin"
    )
else
    # Windows or other
    echo -e "${YELLOW}⚠️  Unsupported system: $SYSTEM${NC}"
    echo "Please use the Python installer: python install-cli.py"
    exit 1
fi

# Find available install path
INSTALL_PATH=""
for path in "${INSTALL_PATHS[@]}"; do
    if [ -d "$path" ] || mkdir -p "$path" 2>/dev/null; then
        if [ -w "$path" ]; then
            INSTALL_PATH="$path"
            break
        fi
    fi
done

if [ -z "$INSTALL_PATH" ]; then
    echo -e "${RED}❌ No suitable installation path found${NC}"
    echo "Available paths:"
    for path in "${INSTALL_PATHS[@]}"; do
        if [ -d "$path" ] && [ -w "$path" ]; then
            echo -e "  ${GREEN}✅ $path${NC}"
        else
            echo -e "  ${RED}❌ $path${NC}"
        fi
    done
    exit 1
fi

echo -e "${BLUE}📁 Installing to: $INSTALL_PATH${NC}"

# Create entry point script
SCRIPT_PATH="$INSTALL_PATH/$COMMAND_NAME"
PROJECT_VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
SCRIPT_CONTENT="#!/bin/bash
# TTS CLI Entry Point
export PYTHONPATH=\"$PROJECT_ROOT:\$PYTHONPATH\"
exec \"$PROJECT_VENV_PYTHON\" -m $CLI_MODULE \"\$@\"
"

echo -e "${BLUE}📝 Creating entry point script...${NC}"
echo "$SCRIPT_CONTENT" > "$SCRIPT_PATH"
chmod +x "$SCRIPT_PATH"
echo -e "${GREEN}✅ Entry point script created: $SCRIPT_PATH${NC}"

# Add to PATH
echo -e "${BLUE}🔧 Adding to PATH...${NC}"

# Find shell configuration file
SHELL_CONFIG=""
if [ -f "$HOME_DIR/.zshrc" ]; then
    SHELL_CONFIG="$HOME_DIR/.zshrc"
elif [ -f "$HOME_DIR/.bashrc" ]; then
    SHELL_CONFIG="$HOME_DIR/.bashrc"
elif [ -f "$HOME_DIR/.bash_profile" ]; then
    SHELL_CONFIG="$HOME_DIR/.bash_profile"
elif [ -f "$HOME_DIR/.profile" ]; then
    SHELL_CONFIG="$HOME_DIR/.profile"
fi

if [ -n "$SHELL_CONFIG" ]; then
    # Check if already in PATH
    if grep -q "$INSTALL_PATH" "$SHELL_CONFIG" 2>/dev/null; then
        echo -e "${GREEN}✅ Path already in $SHELL_CONFIG${NC}"
    else
        # Add to shell config
        echo "" >> "$SHELL_CONFIG"
        echo "# TTS CLI PATH" >> "$SHELL_CONFIG"
        echo "export PATH=\"$INSTALL_PATH:\$PATH\"" >> "$SHELL_CONFIG"
        echo -e "${GREEN}✅ Added to $SHELL_CONFIG${NC}"
        echo -e "${YELLOW}⚠️  Please restart your terminal or run: source $SHELL_CONFIG${NC}"
    fi
    
    # Add to current session
    export PATH="$INSTALL_PATH:$PATH"
    echo -e "${GREEN}✅ Added to current session PATH${NC}"
else
    echo -e "${YELLOW}⚠️  No shell configuration file found${NC}"
    echo "You may need to manually add $INSTALL_PATH to your PATH"
fi

# Verify installation
echo -e "${BLUE}🧪 Verifying installation...${NC}"
if "$SCRIPT_PATH" --help >/dev/null 2>&1; then
    echo -e "${GREEN}✅ CLI command verification successful!${NC}"
else
    echo -e "${YELLOW}⚠️  CLI command may have issues${NC}"
fi

echo -e "\n${GREEN}🎉 Installation Complete!${NC}"
echo -e "\n${BLUE}📋 Usage:${NC}"
echo "  $COMMAND_NAME --help"
echo "  $COMMAND_NAME --list-models"
echo "  $COMMAND_NAME --text 'Hello' --model edge-tts"

echo -e "\n${GREEN}✅ The '$COMMAND_NAME' command is now available globally!${NC}"
echo -e "📁 Installed at: $SCRIPT_PATH"

echo -e "\n${BLUE}💡 Pro tip:${NC}"
echo "You can now use '$COMMAND_NAME' from any directory on your system!"

echo -e "\n${GREEN}Happy TTS Generation! 🎵${NC}"
