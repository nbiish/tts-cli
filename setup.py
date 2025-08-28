#!/usr/bin/env python3
"""
TTS CLI Setup Script
====================

This script sets up the complete TTS CLI tooling with all 6 TTS models
in isolated UV environments. It will:

1. Create isolated environments for each TTS model
2. Install all required dependencies
3. Set up the main tooling environment
4. Verify all models are working

Usage:
    python setup.py [--clean] [--verify]

Requirements:
    - Python 3.10+ installed
    - UV package manager installed (https://docs.astral.sh/uv/)
    - Git for cloning repositories
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import argparse


class TTSCLISetup:
    """Main setup class for TTS CLI tooling."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.model_envs_dir = self.project_root / ".model-envs"
        self.models = [
            "f5-tts",
            "edge-tts", 
            "dia",
            "kyutai",
            "kokoro",
            "vibevoice"
        ]
        
    def run_command(self, command, cwd=None, check=True):
        """Run a shell command with proper error handling."""
        print(f"🔄 Running: {command}")
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd or self.project_root,
                check=check,
                capture_output=True,
                text=True
            )
            if result.stdout:
                print(f"✅ Output: {result.stdout.strip()}")
            return result
        except subprocess.CalledProcessError as e:
            print(f"❌ Error: {e}")
            if e.stderr:
                print(f"   Stderr: {e.stderr.strip()}")
            if check:
                raise
            return e
    
    def check_requirements(self):
        """Check if required tools are installed."""
        print("🔍 Checking requirements...")
        
        # Check Python version
        if sys.version_info < (3, 10):
            print("❌ Python 3.10+ required")
            return False
        
        # Check UV
        try:
            result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
            print(f"✅ UV found: {result.stdout.strip()}")
        except FileNotFoundError:
            print("❌ UV not found. Install from: https://docs.astral.sh/uv/")
            return False
        
        # Check Git
        try:
            result = subprocess.run(["git", "--version"], capture_output=True, text=True)
            print(f"✅ Git found: {result.stdout.strip()}")
        except FileNotFoundError:
            print("❌ Git not found. Install Git to continue.")
            return False
        
        print("✅ All requirements met!")
        return True
    
    def create_main_environment(self):
        """Create the main tooling environment."""
        print("\n🏗️ Creating main tooling environment...")
        
        if not (self.project_root / ".venv").exists():
            self.run_command("uv venv")
        
        # Install main dependencies
        self.run_command("uv pip install -r main-dependencies.txt")
        print("✅ Main environment created!")
    
    def create_model_environments(self):
        """Create isolated environments for each TTS model."""
        print("\n🏗️ Creating isolated model environments...")
        
        for model in self.models:
            print(f"\n📦 Setting up {model} environment...")
            env_dir = self.model_envs_dir / f"{model}-env"
            
            # Create environment directory
            env_dir.mkdir(parents=True, exist_ok=True)
            
            # Create UV environment
            self.run_command(f"uv venv {env_dir}/.venv")
            
            # Install dependencies
            deps_file = self.project_root / f"{model}-dependencies.txt"
            if deps_file.exists():
                self.run_command(f"uv pip install -r {deps_file}", cwd=env_dir)
                print(f"✅ {model} environment created!")
            else:
                print(f"⚠️ No dependency file found for {model}")
    
    def install_model_specific_packages(self):
        """Install model-specific packages that may not be in dependency files."""
        print("\n📦 Installing model-specific packages...")
        
        # F5-TTS
        f5_env = self.model_envs_dir / "f5-tts-env"
        if f5_env.exists():
            print("📦 Installing F5-TTS...")
            self.run_command("uv pip install f5-tts", cwd=f5_env)
        
        # Edge TTS
        edge_env = self.model_envs_dir / "edge-tts-env"
        if edge_env.exists():
            print("📦 Installing Edge TTS...")
            self.run_command("uv pip install edge-tts", cwd=edge_env)
        
        # Dia (transformers main branch)
        dia_env = self.model_envs_dir / "dia-env"
        if dia_env.exists():
            print("📦 Installing Dia dependencies...")
            self.run_command("uv pip install git+https://github.com/huggingface/transformers.git", cwd=dia_env)
            self.run_command("uv pip install torch soundfile librosa", cwd=dia_env)
        
        # Kyutai TTS
        kyutai_env = self.model_envs_dir / "kyutai-env"
        if kyutai_env.exists():
            print("📦 Installing Kyutai TTS...")
            self.run_command("uv pip install moshi-mlx", cwd=kyutai_env)
        
        # Kokoro
        kokoro_env = self.model_envs_dir / "kokoro-env"
        if kokoro_env.exists():
            print("📦 Installing Kokoro...")
            self.run_command("uv pip install kokoro>=0.9.2 soundfile", cwd=kokoro_env)
        
        # VibeVoice
        vibevoice_env = self.model_envs_dir / "vibevoice-env"
        if vibevoice_env.exists():
            print("📦 Installing VibeVoice dependencies...")
            self.run_command("uv pip install transformers torch soundfile", cwd=vibevoice_env)
    
    def verify_installation(self):
        """Verify that all models are working."""
        print("\n🧪 Verifying installation...")
        
        # Test the CLI
        try:
            result = self.run_command("python -m tts_cli.cli_tts --list-models", check=False)
            if result.returncode == 0:
                print("✅ CLI tool working!")
            else:
                print("⚠️ CLI tool may have issues")
        except Exception as e:
            print(f"❌ CLI verification failed: {e}")
        
        # Test environment listing
        try:
            result = self.run_command("python -m tts_cli.cli_tts --list-environments", check=False)
            if result.returncode == 0:
                print("✅ Environment management working!")
            else:
                print("⚠️ Environment management may have issues")
        except Exception as e:
            print(f"❌ Environment verification failed: {e}")
    
    def cleanup(self):
        """Clean up all environments (for fresh start)."""
        print("\n🧹 Cleaning up all environments...")
        
        if self.model_envs_dir.exists():
            shutil.rmtree(self.model_envs_dir)
            print("✅ Model environments removed")
        
        main_venv = self.project_root / ".venv"
        if main_venv.exists():
            shutil.rmtree(main_venv)
            print("✅ Main environment removed")
        
        print("✅ Cleanup complete!")
    
    def run_setup(self, clean=False, verify=True):
        """Run the complete setup process."""
        print("🚀 TTS CLI Setup Starting...")
        print("=" * 50)
        
        if not self.check_requirements():
            print("❌ Setup failed: Requirements not met")
            return False
        
        if clean:
            self.cleanup()
        
        try:
            self.create_main_environment()
            self.create_model_environments()
            self.install_model_specific_packages()
            
            if verify:
                self.verify_installation()
            
            print("\n🎉 Setup Complete!")
            print("\n📋 Next Steps:")
            print("1. Test the CLI: python -m tts_cli.cli_tts --help")
            print("2. List models: python -m tts_cli.cli_tts --list-models")
            print("3. Test a model: python -m tts_cli.cli_tts --text 'Hello' --model edge-tts")
            print("\n📚 For more information, see README.md")
            
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="TTS CLI Setup Script")
    parser.add_argument("--clean", action="store_true", help="Clean existing environments before setup")
    parser.add_argument("--verify", action="store_true", default=True, help="Verify installation after setup")
    parser.add_argument("--no-verify", dest="verify", action="store_false", help="Skip verification")
    
    args = parser.parse_args()
    
    setup = TTSCLISetup()
    success = setup.run_setup(clean=args.clean, verify=args.verify)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
