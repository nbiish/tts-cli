#!/bin/bash
# Setup script for global TTS CLI access with symlinks
# This keeps everything centralized in the repo while providing global access

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Setting up TTS CLI for global access...${NC}"

# Get the script directory (project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo -e "${YELLOW}Project root: $SCRIPT_DIR${NC}"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ uv is not installed. Please install uv first:${NC}"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Install the package in development mode
echo -e "${YELLOW}📦 Installing TTS CLI package...${NC}"
cd "$SCRIPT_DIR"
uv pip install -e .

# Create symlink for easy access (optional)
if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Create a symlink in a common location
    SYMLINK_DIR="$HOME/.local/bin"
    mkdir -p "$SYMLINK_DIR"
    
    # Check if cli-tts is already in PATH
    if command -v cli-tts &> /dev/null; then
        echo -e "${GREEN}✅ cli-tts is already available in PATH${NC}"
    else
        echo -e "${YELLOW}⚠️  cli-tts is not in PATH. Add $SYMLINK_DIR to your PATH:${NC}"
        echo "export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo "Add this to your ~/.bashrc, ~/.zshrc, or ~/.profile"
    fi
fi

# Test the installation
echo -e "${YELLOW}🧪 Testing installation...${NC}"
if cli-tts --help &> /dev/null; then
    echo -e "${GREEN}✅ TTS CLI is working correctly${NC}"
else
    echo -e "${RED}❌ TTS CLI installation failed${NC}"
    exit 1
fi

# Show usage information
echo -e "${GREEN}🎉 Setup complete!${NC}"
echo ""
echo -e "${BLUE}Usage:${NC}"
echo "  cli-tts --help                    # Show help"
echo "  cli-tts --list-models             # List available models"
echo "  cli-tts --text 'Hello' --output hello.wav  # Generate speech"
echo ""
echo -e "${BLUE}Environment Management:${NC}"
echo "  cli-tts --create-environment coqui-tts  # Create model environment"
echo "  cli-tts --list-environments             # List environments"
echo ""
echo -e "${YELLOW}Note: All model environments are stored in:${NC}"
echo "  $SCRIPT_DIR/.model-envs/"
echo ""
echo -e "${YELLOW}This keeps everything centralized in the repo while providing global access.${NC}"
echo -e "${YELLOW}Changes to the code are immediately available everywhere!${NC}"
