#!/usr/bin/env python3
"""
TTS CLI - Main command-line interface.

This module provides the main CLI interface for the TTS tool following
the tiered composition architecture as a Matter component.
"""

import argparse
import sys
import subprocess
import shutil
import platform
import time
from pathlib import Path
from typing import Optional
import pyperclip

from .core.model_registry import model_registry
from .core.environment_manager import env_manager
from .models.pocket_tts_model import PocketTTSModel


def setup_models() -> None:
    """Register all available TTS models."""
    # Register Pocket TTS model (New compact model)
    model_registry.register_model("pocket-tts", PocketTTSModel)


def create_environment(model_name: str) -> bool:
    """Create environment for a specific model."""
    model_configs = {
        "pocket-tts": [
            "pocket-tts",
            "scipy>=1.9.0"
        ]
    }
    
    if model_name not in model_configs:
        print(f"Unknown model: {model_name}")
        return False
    
    dependencies = model_configs[model_name]
    print(f"Creating environment for {model_name} with dependencies: {', '.join(dependencies)}")
    
    success = env_manager.create_environment(model_name, dependencies)
    if success:
        print(f"✅ Environment created successfully for {model_name}")
    else:
        print(f"❌ Failed to create environment for {model_name}")
    
    return success


def list_models() -> None:
    """List all available models and their status."""
    print("Available TTS Models:")
    print("=" * 50)
    
    models = model_registry.list_models()
    for model_name in models:
        model = model_registry.get_model(model_name)
        if model:
            info = model.get_model_info()
            status = "✅ Available" if model.check_availability() else "❌ Not Available"
            print(f"{model_name:15} | {status:15} | {info['description']}")
        else:
            print(f"{model_name:15} | ❌ Not Loaded")


def list_environments() -> None:
    """List all environments and their status."""
    print("Environment Status:")
    print("=" * 60)
    
    environments = env_manager.list_environments()
    if not environments:
        print("No environments found.")
        return
    
    for env in environments:
        status_icon = "✅" if env["status"] == "Available" else "❌"
        print(f"{status_icon} {env['model']:15} | {env['status']:10} | {env['path']}")
        print(f"   Dependencies: {env['dependencies']}")


def test_model(model_name: str) -> None:
    """Test a specific model."""
    print(f"Testing model: {model_name}")
    
    # Check if environment exists
    if not env_manager.environment_exists(model_name):
        print(f"❌ Environment not found for {model_name}")
        print(f"Create it with: cli-tts --create-environment {model_name}")
        return
    
    # Test environment
    success, message = env_manager.test_environment(model_name)
    if not success:
        print(f"❌ Environment test failed: {message}")
        return
    
    print(f"✅ Environment test passed: {message}")
    
    # Test model functionality
    model = model_registry.get_model(model_name)
    if not model:
        print(f"❌ Model not registered: {model_name}")
        return
    
    if not model.check_availability():
        print(f"❌ Model not available: {model_name}")
        return
    
    print(f"✅ Model {model_name} is available and ready to use")


def generate_speech(text: str, model_name: str, voice: Optional[str], 
                   output_path: str, **kwargs) -> bool:
    """Generate speech from text."""
    model = model_registry.get_model(model_name)
    if not model:
        print(f"Model not found: {model_name}")
        return False
    
    if not model.check_availability():
        print(f"Model not available: {model_name}")
        print(f"Create environment with: cli-tts --create-environment {model_name}")
        return False
    
    print(f"Generating speech with {model_name}...")
    success = model.generate_speech(text, voice, output_path, **kwargs)
    
    if success:
        print(f"✅ Speech generated successfully: {output_path}")
    else:
        print("❌ Failed to generate speech")
    
    return success


def list_voices(model_name: str) -> None:
    """List voices for a specific model."""
    model = model_registry.get_model(model_name)
    if not model:
        print(f"Model not found: {model_name}")
        return
    
    if not model.check_availability():
        print(f"Model not available: {model_name}")
        return
    
    voices = model.list_voices()
    if not voices:
        print(f"No voices found for {model_name}")
        return
    
    print(f"Available voices for {model_name}:")
    print("=" * 50)
    
    # Group voices by language
    voice_groups = {}
    for voice in voices:
        if '-' in voice:
            lang = voice.split('-')[0] + '-' + voice.split('-')[1]
        else:
            lang = "English" if model_name == "pocket-tts" else "General"
        
        if lang not in voice_groups:
            voice_groups[lang] = []
        voice_groups[lang].append(voice)
    
    for lang, voice_list in sorted(voice_groups.items()):
        print(f"\n{lang}:")
        for voice in sorted(voice_list):
            print(f"  - {voice}")


def play_audio(file_path: str) -> None:
    """Play audio file using system default player."""
    print(f"Playing audio: {file_path}")
    try:
        system = platform.system()
        if system == "Darwin":  # macOS
            subprocess.run(["afplay", file_path], check=True)
        elif system == "Linux":
            # Try aplay or paplay
            if shutil.which("aplay"):
                subprocess.run(["aplay", file_path], check=True)
            elif shutil.which("paplay"):
                subprocess.run(["paplay", file_path], check=True)
            else:
                print("❌ No audio player found (aplay/paplay)")
        elif system == "Windows":
            # Use PowerShell to play sound
            subprocess.run(["powershell", "-c", f"(New-Object Media.SoundPlayer '{file_path}').PlaySync()"], check=True)
        else:
            print(f"❌ Unsupported platform for audio playback: {system}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to play audio: {e}")
    except Exception as e:
        print(f"❌ Error playing audio: {e}")


def get_cached_output_path(retention_limit: int = 9) -> str:
    """Get path for new cached audio file and manage retention."""
    # Use user's home directory for cache
    cache_dir = Path.home() / ".tts-cli" / "cache"
    
    # Check permissions and fallback if needed
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        # Test write permission
        test_file = cache_dir / f".test_{int(time.time())}"
        test_file.touch()
        test_file.unlink()
    except (OSError, PermissionError):
        # Fallback to temporary directory if home is not writable
        import tempfile
        cache_dir = Path(tempfile.gettempdir()) / "tts-cli-cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate new filename with timestamp
    timestamp = int(time.time())
    new_file = cache_dir / f"speech_{timestamp}.wav"
    
    # Manage retention
    try:
        # Get list of wav files sorted by creation time (oldest first)
        files = sorted(cache_dir.glob("speech_*.wav"), key=lambda f: f.stat().st_ctime)
        
        # Calculate how many to delete
        # We want to keep (retention_limit - 1) so there's room for the new one
        # Or simply delete until we have space. 
        # The requirement is: "delete after a set number of previous audio files have been saved"
        # Let's interpret "saved" as "existing in cache".
        # If we have N files, and we add 1, we will have N+1.
        # If N >= retention_limit, we should delete (N - retention_limit + 1) oldest files?
        # Let's just keep the count <= retention_limit.
        
        while len(files) >= retention_limit:
            oldest = files.pop(0)
            try:
                oldest.unlink()
                # print(f"Deleted old cache file: {oldest.name}")
            except Exception as e:
                print(f"Failed to delete {oldest}: {e}")
                
    except Exception as e:
        print(f"Warning: Failed to manage cache retention: {e}")
        
    return str(new_file)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="TTS CLI - Command-Line Text-to-Speech Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  cli-tts --text "Hello world" --output hello.wav
  cli-tts --clipboard --model edge-tts --output speech.wav
  cli-tts --create-environment edge-tts
  cli-tts --list-models
  cli-tts --list-voices --model edge-tts
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=False)
    input_group.add_argument("--text", help="Text to convert to speech")
    input_group.add_argument("--clipboard", action="store_true", 
                           help="Read text from clipboard")
    input_group.add_argument("--input-file", help="Read text from file")
    
    # Model and voice options
    parser.add_argument("--model", default="pocket-tts", 
                       help="TTS model to use (default: pocket-tts)")
    parser.add_argument("--voice", help="Voice to use (model-specific)")
    parser.add_argument("--output", help="Output audio file path")
    
    # Environment management
    parser.add_argument("--create-environment", help="Create environment for model")
    parser.add_argument("--cleanup-environment", help="Remove environment for model")
    parser.add_argument("--cleanup-all-environments", action="store_true",
                       help="Remove all environments")
    
    # Information commands
    parser.add_argument("--list-models", action="store_true", 
                       help="List available models")
    parser.add_argument("--list-environments", action="store_true",
                       help="List environment status")
    parser.add_argument("--list-voices", action="store_true",
                       help="List voices for a model")
    parser.add_argument("--test-model", help="Test a specific model")
    
    # Voice cloning
    parser.add_argument("--voice-clone", help="Reference audio file for voice cloning")
    
    args = parser.parse_args()
    
    # Setup models
    setup_models()
    
    # Handle environment management commands
    if args.create_environment:
        create_environment(args.create_environment)
        return
    
    if args.cleanup_environment:
        success = env_manager.cleanup_environment(args.cleanup_environment)
        if success:
            print(f"✅ Environment cleaned up for {args.cleanup_environment}")
        else:
            print(f"❌ Failed to cleanup environment for {args.cleanup_environment}")
        return
    
    if args.cleanup_all_environments:
        success = env_manager.cleanup_all_environments()
        if success:
            print("✅ All environments cleaned up")
        else:
            print("❌ Failed to cleanup all environments")
        return
    
    # Handle information commands
    if args.list_models:
        list_models()
        return
    
    if args.list_environments:
        list_environments()
        return
    
    if args.test_model:
        test_model(args.test_model)
        return
    
    if args.list_voices:
        list_voices(args.model)
        return
    
    # Handle speech generation (only if output is specified or we have input)
    if args.output or args.text or args.clipboard or args.input_file or args.voice_clone:
        text = None
        
        if args.text:
            text = args.text
        elif args.clipboard:
            try:
                text = pyperclip.paste()
                if not text:
                    print("❌ Clipboard is empty")
                    return
                print(f"Using text from clipboard: {text[:50]}...")
            except Exception as e:
                print(f"❌ Failed to read clipboard: {e}")
                return
        elif args.input_file:
            try:
                with open(args.input_file, 'r') as f:
                    text = f.read()
                print(f"Using text from file: {args.input_file}")
            except Exception as e:
                print(f"❌ Failed to read file: {e}")
                return
        
        # If no text provided but voice clone is present, use default text
        if not text and args.voice_clone:
            text = "This is a sample of the cloned voice using Pocket TTS."
            print(f"ℹ️  No text provided. Using default text: '{text}'")
        
        if not text:
            print("❌ No text provided")
            return
        
        # Determine output path
        output_path = args.output
        if not output_path:
            output_path = get_cached_output_path()
        
        # Generate speech
        success = generate_speech(
            text=text,
            model_name=args.model,
            voice=args.voice,
            output_path=output_path,
            voice_clone=args.voice_clone
        )
        
        if success:
            # Play audio by default
            play_audio(output_path)
        else:
            sys.exit(1)
    else:
        print("No input text or output file specified. Use --help for more options.")


if __name__ == "__main__":
    main()
