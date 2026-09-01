#!/bin/bash
# Global TTS CLI Alias Script
# This script provides system-wide access to the TTS CLI
# It uses 'uv' for fast, isolated execution with in-process optimization

# Resolve the directory of this script (handling symlinks)
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
SCRIPT_DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"

# Ensure we have the project root context for uv to find pyproject.toml
# SCRIPT_DIR is .../scripts, so project root is .../
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ Error: 'uv' is not installed or not in PATH."
    echo "Please install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Run with uv pointing to the project environment while preserving caller CWD
export TTS_CLI_CALLER_DIR="$PWD"
uv --project "$PROJECT_ROOT" run python -m tts_cli.cli "$@"
