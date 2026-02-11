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
from .core.model_daemon import is_daemon_running, get_daemon_status, stop_daemon, LOG_PATH as DAEMON_LOG_PATH


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
    parser.add_argument("--set-clone-voice", help="Set a persistent clone voice from a file (saves to custom_voices/). Can be a path or a name in custom_voices.")
    parser.add_argument("--unset-clone-voice", action="store_true", help="Unset the persistent clone voice (does not delete the file)")
    parser.add_argument("--list-clone-voices", action="store_true", help="List available custom clone voices")
    
    # Daemon management
    daemon_group = parser.add_argument_group("Model Daemon")
    daemon_group.add_argument("--daemon-status", action="store_true",
                             help="Show model daemon status (PID tracking, queue depth, loaded state)")
    daemon_group.add_argument("--daemon-stop", action="store_true",
                             help="Stop the model daemon and unload the model from memory")
    daemon_group.add_argument("--daemon-log", nargs="?", const=50, type=int, metavar="LINES",
                             help="Show the last N lines of the daemon log (default: 50)")
    
    args = parser.parse_args()
    
    # Setup models
    setup_models()

    # ---- Daemon management commands ----
    if args.daemon_status:
        if not is_daemon_running():
            print("Model daemon is NOT running.")
            print("It will start automatically on next TTS request.")
        else:
            status = get_daemon_status()
            if status:
                print("Model Daemon Status")
                print("=" * 50)
                print(f"  Daemon PID:      {status.get('daemon_pid', '?')}")
                print(f"  Model loaded:    {'Yes' if status.get('model_loaded') else 'No'}")
                print(f"  Queue depth:     {status.get('queue_depth', 0)}")
                print(f"  Idle timeout:    {status.get('idle_timeout_seconds', '?')}s")
                pids = status.get('active_pids', [])
                if pids:
                    print(f"  Tracked PIDs:    {len(pids)}")
                    for p in pids:
                        print(f"    PID {p['pid']:>8}  requests={p['request_count']}  "
                              f"last_seen={time.strftime('%H:%M:%S', time.localtime(p['last_seen']))}")
                else:
                    print("  Tracked PIDs:    (none)")
            else:
                print("Daemon is running but did not respond to status query.")
        return

    if args.daemon_stop:
        if not is_daemon_running():
            print("Model daemon is not running.")
        else:
            if stop_daemon():
                print("\u2705 Daemon stopped and model unloaded from memory.")
            else:
                print("\u274c Failed to stop daemon.")
        return

    if args.daemon_log is not None:
        if not DAEMON_LOG_PATH.exists():
            print(f"No daemon log found at {DAEMON_LOG_PATH}")
        else:
            import collections
            n = args.daemon_log
            with open(DAEMON_LOG_PATH, "r", encoding="utf-8", errors="replace") as f:
                tail = collections.deque(f, maxlen=n)
            print(f"--- Last {len(tail)} lines of {DAEMON_LOG_PATH} ---")
            for line in tail:
                print(line, end="")
        return

    # Define constants for custom voices
    # Use repository root for storage to ensure persistence and accessibility
    # This allows users to easily drop files into the custom_voices folder in the project
    REPO_ROOT = Path(__file__).resolve().parent.parent
    CUSTOM_VOICES_DIR = REPO_ROOT / "custom_voices"
    ACTIVE_VOICE_FILE = CUSTOM_VOICES_DIR / ".active_voice"

    # Handle list-clone-voices command
    if args.list_clone_voices:
        if not CUSTOM_VOICES_DIR.exists():
            print("No custom voices found.")
            print(f"Directory: {CUSTOM_VOICES_DIR}")
            return
            
        print("Custom Clone Voices:")
        print("=" * 50)
        
        # Get active voice
        active_voice = None
        if ACTIVE_VOICE_FILE.exists():
            try:
                with open(ACTIVE_VOICE_FILE, 'r') as f:
                    active_voice = f.read().strip()
            except:
                pass
        
        voices = sorted(CUSTOM_VOICES_DIR.glob("*.wav"))
        if not voices:
            print("No voice files found.")
        
        for voice in voices:
            name = voice.name
            status = "✅ Active" if name == active_voice else ""
            print(f"{name:30} {status}")
            
        print("\nTo set a voice: tts-cli --set-clone-voice <filename_or_path>")
        return

    # Handle unset-clone-voice command
    if args.unset_clone_voice:
        if ACTIVE_VOICE_FILE.exists():
            try:
                ACTIVE_VOICE_FILE.unlink()
                print("✅ Custom clone voice unset. Reverted to default random voice.")
            except Exception as e:
                print(f"❌ Failed to unset voice: {e}")
        else:
            print("ℹ️  No custom clone voice was currently set.")
        return

    # Handle set-clone-voice command
    if args.set_clone_voice:
        input_voice = args.set_clone_voice
        
        # Ensure custom_voices directory exists
        CUSTOM_VOICES_DIR.mkdir(parents=True, exist_ok=True)
        
        target_name = None
        source_path = None
        
        # Check if input is a name in the custom voices dir
        # Only treat as a name if it's NOT a path (no separators) and exists in the dir
        import os
        is_name_only = os.sep not in input_voice
        potential_path = CUSTOM_VOICES_DIR / input_voice
        
        if is_name_only and potential_path.exists():
            # Use existing voice
            target_name = input_voice
            print(f"ℹ️  Selecting existing custom voice: {target_name}")
            
            # Set as active
            try:
                with open(ACTIVE_VOICE_FILE, 'w') as f:
                    f.write(target_name)
                print(f"✅ Voice set successfully!")
                print("This voice will now be used by default for all generations.")
            except Exception as e:
                print(f"❌ Failed to set active voice: {e}")
            return

        # Treat as file path to import
        if Path(input_voice).exists():
            source_path = Path(input_voice)
            target_name = source_path.name
            print(f"Processing and importing clone voice from: {input_voice}")
        else:
            print(f"❌ Input file or voice name not found: {input_voice}")
            return

        if not audio_processor.check_availability():
             print("❌ Audio processing environment not found. Run: cli-tts --create-environment audio-processing")
             return

        # Define output path
        target_path = CUSTOM_VOICES_DIR / target_name
        
        # Simple copy without processing (user requested to skip auto-cleaning)
        try:
            print(f"Importing voice file: {source_path}")
            shutil.copy2(source_path, target_path)
            
            print(f"✅ Clone voice imported successfully! Saved to: {target_path}")
            
            # Set as active
            try:
                with open(ACTIVE_VOICE_FILE, 'w') as f:
                    f.write(target_name)
                print(f"✅ Voice set as active!")
                print("This voice will now be used by default for all generations.")
            except Exception as e:
                print(f"❌ Failed to set active voice: {e}")
                
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
    
    # Define constants for custom voices
    REPO_ROOT = Path(__file__).resolve().parent.parent
    CUSTOM_VOICES_DIR = REPO_ROOT / "custom_voices"
    ACTIVE_VOICE_FILE = CUSTOM_VOICES_DIR / ".active_voice"
    
    # If no explicit voice or clone is set, check for a default custom voice
    if not args.voice and not voice_clone_path:
        if ACTIVE_VOICE_FILE.exists():
            try:
                with open(ACTIVE_VOICE_FILE, 'r') as f:
                    active_voice_name = f.read().strip()
                
                if active_voice_name:
                    voice_path = CUSTOM_VOICES_DIR / active_voice_name
                    if voice_path.exists():
                        voice_clone_path = str(voice_path)
                        print(f"ℹ️  Using custom clone voice: {active_voice_name}")
            except:
                pass

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
