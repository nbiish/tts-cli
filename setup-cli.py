#!/usr/bin/env python3
"""
Setup script for TTS CLI.

This script installs the TTS CLI tool and sets up the necessary environment.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list, description: str) -> bool:
    """Run a command and return success status."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False


def check_uv_installed() -> bool:
    """Check if uv is installed."""
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_uv() -> bool:
    """Install uv package manager."""
    print("Installing uv package manager...")
    
    # Try different installation methods
    install_commands = [
        ["curl", "-LsSf", "https://astral.sh/uv/install.sh", "|", "sh"],
        ["pip", "install", "uv"],
        ["pipx", "install", "uv"]
    ]
    
    for cmd in install_commands:
        if cmd[0] == "curl":
            # Handle curl command specially
            try:
                result = subprocess.run(
                    "curl -LsSf https://astral.sh/uv/install.sh | sh",
                    shell=True, check=True, capture_output=True, text=True
                )
                print("✅ uv installed successfully")
                return True
            except subprocess.CalledProcessError:
                continue
        else:
            if run_command(cmd, f"Installing uv with {cmd[0]}"):
                return True
    
    print("❌ Failed to install uv. Please install it manually:")
    print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
    return False


def install_tts_cli() -> bool:
    """Install the TTS CLI package."""
    return run_command([sys.executable, "-m", "pip", "install", "-e", "."], 
                      "Installing TTS CLI package")


def main():
    """Main setup function."""
    print("🚀 Setting up TTS CLI...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ pyproject.toml not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Check Python version
    if sys.version_info < (3, 12):
        print("❌ Python 3.12 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Check/install uv
    if not check_uv_installed():
        if not install_uv():
            sys.exit(1)
    else:
        print("✅ uv package manager is already installed")
    
    # Install TTS CLI
    if not install_tts_cli():
        sys.exit(1)
    
    print("\n🎉 TTS CLI setup completed successfully!")
    print("\nNext steps:")
    print("1. Create environment for Edge TTS:")
    print("   cli-tts --create-environment edge-tts")
    print("\n2. Test the installation:")
    print("   cli-tts --text 'Hello world' --output test.wav")
    print("\n3. List available models:")
    print("   cli-tts --list-models")


if __name__ == "__main__":
    main()
