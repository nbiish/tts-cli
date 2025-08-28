#!/bin/bash

# TTS CLI Setup Script (Shell Version)
# ====================================
# 
# This script sets up the complete TTS CLI tooling with all 6 TTS models
# in isolated UV environments.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_ENVS_DIR="$PROJECT_ROOT/.model-envs"

# Models to set up
MODELS=("f5-tts" "edge-tts" "dia" "kyutai" "kokoro" "vibevoice")

echo -e "${BLUE}🚀 TTS CLI Setup Starting...${NC}"
echo "=================================================="

# Check requirements
echo -e "${BLUE}🔍 Checking requirements...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${GREEN}✅ Python $PYTHON_VERSION found${NC}"

# Check UV
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ UV not found. Install from: https://docs.astral.sh/uv/${NC}"
    exit 1
fi

UV_VERSION=$(uv --version)
echo -e "${GREEN}✅ UV found: $UV_VERSION${NC}"

# Check Git
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git not found${NC}"
    exit 1
fi

GIT_VERSION=$(git --version)
echo -e "${GREEN}✅ Git found: $GIT_VERSION${NC}"

echo -e "${GREEN}✅ All requirements met!${NC}"

# Create main environment
echo -e "\n${BLUE}🏗️ Creating main tooling environment...${NC}"
if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    cd "$PROJECT_ROOT"
    uv venv
    echo -e "${GREEN}✅ Main environment created${NC}"
else
    echo -e "${YELLOW}⚠️ Main environment already exists${NC}"
fi

# Install main dependencies
if [ -f "$PROJECT_ROOT/main-dependencies.txt" ]; then
    echo -e "${BLUE}📦 Installing main dependencies...${NC}"
    cd "$PROJECT_ROOT/.venv"
    uv pip install -r ../main-dependencies.txt
    echo -e "${GREEN}✅ Main dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️ No main dependencies file found${NC}"
fi

# Create model environments
echo -e "\n${BLUE}🏗️ Creating isolated model environments...${NC}"
mkdir -p "$MODEL_ENVS_DIR"

for model in "${MODELS[@]}"; do
    echo -e "\n${BLUE}📦 Setting up $model environment...${NC}"
    env_dir="$MODEL_ENVS_DIR/${model}-env"
    
    # Create environment
    if [ ! -d "$env_dir/.venv" ]; then
        uv venv "$env_dir/.venv"
        echo -e "${GREEN}✅ $model environment created${NC}"
    else
        echo -e "${YELLOW}⚠️ $model environment already exists${NC}"
    fi
    
    # Install dependencies
    deps_file="$PROJECT_ROOT/${model}-dependencies.txt"
    if [ -f "$deps_file" ]; then
        cd "$env_dir/.venv"
        uv pip install -r "$deps_file"
        echo -e "${GREEN}✅ $model dependencies installed${NC}"
    else
        echo -e "${YELLOW}⚠️ No dependency file found for $model${NC}"
    fi
done

# Install model-specific packages
echo -e "\n${BLUE}📦 Installing model-specific packages...${NC}"

# F5-TTS
if [ -d "$MODEL_ENVS_DIR/f5-tts-env" ]; then
    echo -e "${BLUE}📦 Installing F5-TTS...${NC}"
    cd "$MODEL_ENVS_DIR/f5-tts-env/.venv"
    uv pip install f5-tts
fi

# Edge TTS
if [ -d "$MODEL_ENVS_DIR/edge-tts-env" ]; then
    echo -e "${BLUE}📦 Installing Edge TTS...${NC}"
    cd "$MODEL_ENVS_DIR/edge-tts-env/.venv"
    uv pip install edge-tts
fi

# Dia
if [ -d "$MODEL_ENVS_DIR/dia-env" ]; then
    echo -e "${BLUE}📦 Installing Dia dependencies...${NC}"
    cd "$MODEL_ENVS_DIR/dia-env/.venv"
    uv pip install git+https://github.com/huggingface/transformers.git
    uv pip install torch soundfile librosa
fi

# Kyutai TTS
if [ -d "$MODEL_ENVS_DIR/kyutai-env" ]; then
    echo -e "${BLUE}📦 Installing Kyutai TTS...${NC}"
    cd "$MODEL_ENVS_DIR/kyutai-env/.venv"
    uv pip install moshi-mlx
fi

# Kokoro
if [ -d "$MODEL_ENVS_DIR/kokoro-env" ]; then
    echo -e "${BLUE}📦 Installing Kokoro...${NC}"
    cd "$MODEL_ENVS_DIR/kokoro-env/.venv"
    uv pip install "kokoro>=0.9.2" soundfile
fi

# VibeVoice
if [ -d "$MODEL_ENVS_DIR/vibevoice-env" ]; then
    echo -e "${BLUE}📦 Installing VibeVoice dependencies...${NC}"
    cd "$MODEL_ENVS_DIR/vibevoice-env/.venv"
    uv pip install transformers torch soundfile
fi

# Return to project root
cd "$PROJECT_ROOT"

# Verification
echo -e "\n${BLUE}🧪 Verifying installation...${NC}"

# Test CLI
if python3 -m tts_cli.cli_tts --help &> /dev/null; then
    echo -e "${GREEN}✅ CLI tool working!${NC}"
else
    echo -e "${YELLOW}⚠️ CLI tool may have issues${NC}"
fi

# Test environment listing
if python3 -m tts_cli.cli_tts --list-environments &> /dev/null; then
    echo -e "${GREEN}✅ Environment management working!${NC}"
else
    echo -e "${YELLOW}⚠️ Environment management may have issues${NC}"
fi

echo -e "\n${GREEN}🎉 Setup Complete!${NC}"
echo -e "\n${BLUE}📋 Next Steps:${NC}"
echo "1. Test the CLI: python3 -m tts_cli.cli_tts --help"
echo "2. List models: python3 -m tts_cli.cli_tts --list-models"
echo "3. Test a model: python3 -m tts_cli.cli_tts --text 'Hello' --model edge-tts"
echo -e "\n${BLUE}📚 For more information, see SETUP_INSTRUCTIONS.md${NC}"

echo -e "\n${GREEN}Happy TTS Generation! 🎵${NC}"
