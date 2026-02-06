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

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
echo -e "${YELLOW}Project root: $PROJECT_ROOT${NC}"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ uv is not installed. Please install uv first:${NC}"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Install the package in development mode
echo -e "${YELLOW}📦 Installing TTS CLI package...${NC}"
cd "$PROJECT_ROOT"
uv pip install -e .

# 3. Install the CLI globally using the bash wrapper approach
echo -e "${YELLOW}🔗 Creating global link...${NC}"

# Use the wrapper script from the scripts directory
sudo cp "$SCRIPT_DIR/tts-cli-global.sh" /usr/local/bin/cli-tts
sudo chmod +x /usr/local/bin/cli-tts

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
echo "  cli-tts --create-environment pocket-tts  # Create model environment"
echo "  cli-tts --list-environments             # List environments"
echo ""
echo -e "${YELLOW}Note: All model environments are stored in:${NC}"
echo "  $PROJECT_ROOT/.model-envs/"
echo ""
echo -e "${YELLOW}This keeps everything centralized in the repo while providing global access.${NC}"
echo -e "${YELLOW}Changes to the code are immediately available everywhere!${NC}"
