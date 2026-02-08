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
from .core.audio_processor import audio_processor
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
        ],
        "audio-processing": [
            "demucs",
            "torch",
            "torchaudio",
            "numpy",
            "soundfile"
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
    # We allow positional arguments for text, or flags
    parser.add_argument("input_text", nargs="?", help="Text to convert to speech (optional positional argument)")
    
    input_group = parser.add_argument_group("Input Options")
    input_group.add_argument("--text", help="Text to convert to speech (explicit flag)")
    input_group.add_argument("--clipboard", action="store_true", 
                           help="Read text from clipboard")
    input_group.add_argument("--input-file", help="Read text from file")
    
    # Audio Processing Options
    processing_group = parser.add_argument_group("Audio Processing Options")
    processing_group.add_argument("--isolate-voice", nargs="?", const=True, metavar="FILE",
                                help="Isolate voice using Demucs. If FILE provided, processes that file.")
    processing_group.add_argument("--remove-silence", nargs="?", const=True, metavar="FILE",
                                help="Remove silence using VAD. If FILE provided, processes that file.")
    processing_group.add_argument("--clean-voice", nargs="?", const=True, metavar="FILE",
                                help="Full cleanup: Isolate voice (Demucs) AND remove silence (VAD).")
    processing_group.add_argument("--process-audio", help="Process an existing audio file (independent of TTS)")

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
    parser.add_argument("--set-clone-voice", help="Set a persistent clone voice from a file (cleans and saves to custom_voices/)")
    parser.add_argument("--unset-clone-voice", action="store_true", help="Remove the persistent clone voice and return to default behavior")
    
    args = parser.parse_args()
    
    # Setup models
    setup_models()

    # Handle unset-clone-voice command
    if args.unset_clone_voice:
        custom_voices_dir = Path("custom_voices")
        if custom_voices_dir.exists():
            cleaned_any = False
            for f in custom_voices_dir.glob("*.wav"):
                try:
                    f.unlink()
                    cleaned_any = True
                except Exception as e:
                    print(f"❌ Failed to delete {f.name}: {e}")
            
            if cleaned_any:
                print("✅ Custom clone voice unset. Reverted to default random voice.")
            else:
                print("ℹ️  No custom clone voice was set.")
        else:
            print("ℹ️  No custom clone voice was set.")
        return

    # Handle set-clone-voice command
    if args.set_clone_voice:
        input_voice = args.set_clone_voice
        if not Path(input_voice).exists():
            print(f"❌ Input file not found: {input_voice}")
            return

        if not audio_processor.check_availability():
             print("❌ Audio processing environment not found. Run: cli-tts --create-environment audio-processing")
             return

        print(f"Processing and setting clone voice from: {input_voice}")
        
        # Ensure custom_voices directory exists
        custom_voices_dir = Path("custom_voices")
        custom_voices_dir.mkdir(exist_ok=True)
        
        # Define output path
        # We use a fixed name or keep original name? 
        # User said "folder that has no file in it... drop a voice file in there"
        # Let's clean it and save as 'default_clone.wav' to be unambiguous, 
        # or we could just use the filename. 
        # Let's use 'default.wav' to make auto-detection simple and consistent.
        target_path = custom_voices_dir / "default.wav"
        
        # Process: Isolate -> Remove Silence
        import tempfile
        import os
        
        try:
            # 1. Isolate Voice
            fd, temp_isolated = tempfile.mkstemp(suffix="_isolated.wav")
            os.close(fd)
            
            print("Step 1/2: Isolating voice...")
            success = audio_processor.isolate_voice(input_voice, temp_isolated)
            if not success:
                print("❌ Voice isolation failed.")
                os.unlink(temp_isolated)
                return
            
            # 2. Remove Silence
            print("Step 2/2: Removing silence...")
            success = audio_processor.remove_silence(temp_isolated, str(target_path))
            
            # Cleanup temp
            if os.path.exists(temp_isolated):
                os.unlink(temp_isolated)
                
            if success:
                print(f"✅ Clone voice set successfully! Saved to: {target_path}")
                print("This voice will now be used by default for all generations.")
            else:
                print("❌ Failed to set clone voice.")
                
        except Exception as e:
            print(f"❌ Error setting clone voice: {e}")
            
        return
    
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
        
    # Handle standalone audio processing
    # Check if any processing input is provided
    process_input = args.process_audio
    
    # Check if file arguments were provided to flags
    if isinstance(args.clean_voice, str):
        if process_input and process_input != args.clean_voice:
             print("❌ Error: Multiple input files specified for processing.")
             return
        process_input = args.clean_voice

    if isinstance(args.isolate_voice, str):
        if process_input and process_input != args.isolate_voice:
             print("❌ Error: Multiple input files specified for processing.")
             return
        process_input = args.isolate_voice
        
    if isinstance(args.remove_silence, str):
        if process_input and process_input != args.remove_silence:
             print("❌ Error: Multiple input files specified for processing.")
             return
        process_input = args.remove_silence

    if process_input:
        if not args.output:
            print("❌ Output file must be specified for audio processing.")
            return
            
        current_path = process_input
        final_output = args.output
        
        # Determine actions
        do_isolate = bool(args.isolate_voice) or bool(args.clean_voice)
        do_silence = bool(args.remove_silence) or bool(args.clean_voice)
        
        # If user just supplied input via process-audio but no flags, ask for action
        if not (do_isolate or do_silence):
             print("❌ No processing action specified (use --isolate-voice or --remove-silence).")
             return

        import tempfile
        import os
        
        try:
            temp_files = []
            
            # 1. Isolate Voice
            if do_isolate:
                if not audio_processor.check_availability():
                     print("❌ Audio processing environment not found. Run: cli-tts --create-environment audio-processing")
                     return
                
                print("Processing: Isolating voice...")
                # If we also have remove_silence, we need a temp file
                if do_silence:
                    fd, temp_out = tempfile.mkstemp(suffix=".wav")
                    os.close(fd)
                    temp_files.append(temp_out)
                    out_target = temp_out
                else:
                    out_target = final_output
                
                success = audio_processor.isolate_voice(current_path, out_target)
                if not success:
                    print("❌ Voice isolation failed.")
                    return
                current_path = out_target
                
            # 2. Remove Silence
            if do_silence:
                if not audio_processor.check_availability():
                     print("❌ Audio processing environment not found. Run: cli-tts --create-environment audio-processing")
                     return
                     
                print("Processing: Removing silence...")
                success = audio_processor.remove_silence(current_path, final_output)
                if not success:
                    print("❌ Silence removal failed.")
                    return
            
            print(f"✅ Audio processing complete: {final_output}")
            
        finally:
            # Cleanup temp files
            for f in temp_files:
                if os.path.exists(f):
                    os.unlink(f)
        return

    # Handle speech generation
    text = None
    
    # Pre-process voice clone file if needed
    voice_clone_path = args.voice_clone
    
    # If no explicit voice or clone is set, check for a default custom voice
    if not args.voice and not voice_clone_path:
        custom_voices_dir = Path("custom_voices")
        if custom_voices_dir.exists():
            # Look for any wav file, prioritizing 'default.wav' or most recent
            wav_files = list(custom_voices_dir.glob("*.wav"))
            if wav_files:
                # If default.wav exists, use it
                default_voice = custom_voices_dir / "default.wav"
                if default_voice.exists():
                    voice_clone_path = str(default_voice)
                    print(f"ℹ️  Using default clone voice: {voice_clone_path}")
                else:
                    # Otherwise use the most recently modified wav file
                    latest_voice = max(wav_files, key=lambda p: p.stat().st_mtime)
                    voice_clone_path = str(latest_voice)
                    print(f"ℹ️  Using detected custom voice: {voice_clone_path}")

    temp_voice_files = []
    
    # Determine if we need to process the voice clone file
    do_process_clone = False
    if voice_clone_path:
        if args.clean_voice or args.isolate_voice or args.remove_silence:
            do_process_clone = True
            
    if do_process_clone:
        if not audio_processor.check_availability():
             print("❌ Audio processing environment not found for voice cloning. Run: cli-tts --create-environment audio-processing")
             return
        
        print(f"Preprocessing voice clone source: {voice_clone_path}")
        import tempfile
        import os
        
        current_path = voice_clone_path
        
        # Determine actions
        do_isolate = bool(args.isolate_voice) or bool(args.clean_voice)
        do_silence = bool(args.remove_silence) or bool(args.clean_voice)
        
        try:
            # 1. Isolate Voice
            if do_isolate:
                fd, temp_out = tempfile.mkstemp(suffix="_isolated.wav")
                os.close(fd)
                temp_voice_files.append(temp_out)
                
                success = audio_processor.isolate_voice(current_path, temp_out)
                if not success:
                    print("❌ Voice isolation for cloning failed.")
                    return
                current_path = temp_out
                
            # 2. Remove Silence
            if do_silence:
                fd, temp_out = tempfile.mkstemp(suffix="_silence_removed.wav")
                os.close(fd)
                temp_voice_files.append(temp_out)
                
                success = audio_processor.remove_silence(current_path, temp_out)
                if not success:
                    print("❌ Silence removal for cloning failed.")
                    return
                current_path = temp_out
                
            # Use the processed file as the voice clone source
            voice_clone_path = current_path
            print(f"✅ Using processed voice file: {voice_clone_path}")
            
        except Exception as e:
            print(f"❌ Error processing voice clone file: {e}")
            return
    
    # 1. Positional argument
    if args.input_text:
        text = args.input_text
    # 2. Explicit flag
    elif args.text:
        text = args.text
    # 3. Clipboard
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
    # 4. File
    elif args.input_file:
        try:
            with open(args.input_file, 'r') as f:
                text = f.read()
            print(f"Using text from file: {args.input_file}")
        except Exception as e:
            print(f"❌ Failed to read file: {e}")
            return
    # 5. Stdin (Piped input)
    elif not sys.stdin.isatty():
        try:
            text = sys.stdin.read().strip()
            if text:
                print(f"Using text from stdin: {text[:50]}...")
        except Exception:
            pass
            
    # If no text provided but voice clone is present, use default text
    if not text and args.voice_clone:
        text = "This is a sample of the cloned voice using Pocket TTS."
        print(f"ℹ️  No text provided. Using default text: '{text}'")
        
    # Proceed if we have text
    if text:
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
            voice_clone=voice_clone_path
        )
        
        # Cleanup temp voice files
        for f in temp_voice_files:
            if os.path.exists(f):
                try:
                    os.unlink(f)
                except:
                    pass
        
        if success:
            # Play audio by default
            play_audio(output_path)
        else:
            sys.exit(1)
        return

    # If we got here, no text was found.
    if args.output:
         print("❌ Output file specified but no input text provided.")
         return

    print("No input text provided. Use --help for usage.")


if __name__ == "__main__":
    main()
