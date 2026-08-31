#!/usr/bin/env python3
"""
TTS CLI - Main command-line interface.

This module provides the main CLI interface for the TTS tool following
the tiered composition architecture as a Matter component.
"""

import argparse
import os
import sys
import subprocess
import shutil
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import pyperclip

from .core.model_registry import model_registry
from .core.environment_manager import env_manager
from .core.audio_processor import audio_processor
from .models.kitten_tts_model import KittenTTSModel


def setup_models() -> None:
    """Register all available TTS models.

    Single engine, one-shot (subprocess exits immediately after writing the
    output WAV — no daemon, no warm cache, no model state held in RAM/VRAM):
      - ``kitten-tts-nano`` / ``auto`` (default): KittenTTS nano int8 (15M) —
        ultra-lightweight CPU ONNX TTS with fixed built-in voices. The fastest
        engine on this machine (cold ~7.9s, RTF ~0.47) and the most portable
        (CPU-only, no accelerator, cross-platform macOS/Linux/Windows/WSL).
    """
    model_registry.register_model("kitten-tts-nano", KittenTTSModel)     # sole engine (CPU, fixed voices, 15M int8)
    model_registry.register_model("auto", KittenTTSModel)                # alias for kitten-tts-nano


# --- Default-model selection (user-configurable; `auto` resolves to this) ---
DEFAULT_MODEL_FALLBACK = "kitten-tts-nano"
# Selectable engines for --set-default / --list.
SELECTABLE_MODELS = (
    "kitten-tts-nano",
)

# Canonical remote — printed as the single concise "not installed" hint so any
# agent/operator can recover in one glance.
TTS_CLI_REMOTE = "https://github.com/nbiish/tts-cli"


def _not_installed_hint(reason: str = "tts-cli not installed") -> None:
    """Print the single, concise not-installed notice pointing at the remote.

    Used everywhere the engine can't run (env missing, model unavailable, model
    not registered). One line, one link — the remote README has full setup.
    """
    print(f"❌ {reason} → {TTS_CLI_REMOTE}")


def _default_model_file() -> Path:
    """User-level config file storing the configured default model name."""
    return Path.home() / ".tts-cli" / "default_model"


def get_default_model() -> str:
    """Resolve the configured default model.

    Precedence: ``TTS_CLI_DEFAULT_MODEL`` env var, then the user config file,
    then the built-in fallback (``pocket-tts``). The value is validated against
    the selectable engine list; an invalid stored value falls back silently.
    """
    env_val = os.environ.get("TTS_CLI_DEFAULT_MODEL", "").strip().lower()
    if env_val in SELECTABLE_MODELS:
        return env_val
    cfg = _default_model_file()
    if cfg.is_file():
        try:
            val = cfg.read_text(encoding="utf-8").strip().lower()
            if val in SELECTABLE_MODELS:
                return val
        except OSError:
            pass
    return DEFAULT_MODEL_FALLBACK


def set_default_model(model_name: str) -> bool:
    """Persist the user's chosen default model. Returns False on bad input."""
    name = (model_name or "").strip().lower()
    if name not in SELECTABLE_MODELS:
        print(f"❌ Unknown model: {model_name!r}. Choose from: {', '.join(SELECTABLE_MODELS)}")
        return False
    cfg = _default_model_file()
    try:
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text(name, encoding="utf-8")
    except OSError as e:
        print(f"❌ Failed to write default model config: {e}")
        return False
    print(f"✅ Default TTS model set to '{name}'. `auto` now uses it.")
    print("Run `cli-tts --list` to see status, or generate with: cli-tts --prompt \"...\"")
    return True


def create_environment(model_name: str) -> bool:
    """Create environment for a specific model."""
    model_configs = {
        # KittenTTS: the sole engine — ultra-lightweight CPU ONNX TTS (fixed
        # voices). Installed from the GitHub release wheel (not on PyPI). Pulls
        # onnxruntime + spaCy for text preprocessing.
        "kitten-tts": [
            "kittentts @ https://github.com/KittenML/KittenTTS/releases/download/0.8.1/kittentts-0.8.1-py3-none-any.whl",
            "onnxruntime",
            "numpy",
            "soundfile",
        ],
        "audio-processing": [
            "demucs",
            "torch",
            "torchaudio",
            "numpy",
            "soundfile"
        ],
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
    
    any_unavailable = False
    models = model_registry.list_models()
    for model_name in models:
        model = model_registry.get_model(model_name)
        if model:
            info = model.get_model_info()
            available = model.check_availability()
            status = "✅ Available" if available else "❌ Not Available"
            if not available:
                any_unavailable = True
            print(f"{model_name:15} | {status:15} | {info['description']}")
        else:
            print(f"{model_name:15} | ❌ Not Loaded")
            any_unavailable = True

    if any_unavailable:
        _not_installed_hint("tts-cli not ready")


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
        _not_installed_hint(f"tts-cli env '{model_name}' missing (run: cli-tts --create-environment kitten-tts)")
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
        _not_installed_hint(f"tts-cli model '{model_name}' not registered")
        return
    
    if not model.check_availability():
        _not_installed_hint("tts-cli engine not available")
        return
    
    print(f"✅ Model {model_name} is available and ready to use")


def _extract_suggestion(text: str) -> Optional[str]:
    """Extract the "Next step: <suggestion>" segment from a spoken summary.

    Matches the last occurrence of "Next step:" (case-insensitive) and returns
    everything after it, stripped. Returns None if the marker is absent.
    """
    if not text:
        return None
    lower = text.lower()
    idx = lower.rfind("next step:")
    if idx == -1:
        return None
    # Move past the marker and any following whitespace/colon.
    suggestion = text[idx + len("next step:"):].lstrip().lstrip(":").strip()
    return suggestion or None


def _log_to_agents_tts_comms(text: str, model_name: str, voice: Optional[str],
                            output_path: str, **kwargs) -> None:
    """Append only the suggestion portion of the spoken text to AGENTS-TTS-COMMS.txt.

    The transcript is a token/context-economical ledger: it stores ONLY the
    "Next step: <suggestion>" part of each call (the hardened-engineer
    recommendation), not the concise summary. This keeps the file small for
    cross-agent ingestion while preserving the actionable next-step history.
    One line per call, ISO-8601 timestamped, with model/lang/voice. Tracked in
    git alongside AGENTS.md. If no "Next step:" segment is present, nothing is
    written (the call had no suggestion to record).
    """
    try:
        # Extract the suggestion: everything after the last "Next step:" marker
        # (case-insensitive). The spoken format is "<summary>. Next step: <sug>".
        suggestion = _extract_suggestion(text)
        if not suggestion:
            return  # no suggestion to record; skip silently

        repo_root = Path(__file__).resolve().parent.parent
        comms_path = repo_root / "AGENTS-TTS-COMMS.txt"
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        lang = kwargs.get("lang") or "EN"
        voice_ref = voice or "(default)"
        # Cap the suggestion length to keep the ledger compact.
        safe_suggestion = suggestion if len(suggestion) <= 1000 else suggestion[:1000] + " …[truncated]"
        block = (
            f"\n## {ts} | model={model_name} | lang={lang} | voice={voice_ref}\n"
            f"{safe_suggestion}\n"
        )
        with open(comms_path, "a", encoding="utf-8") as f:
            f.write(block)
    except OSError:
        # Logging must never break generation; swallow write errors silently.
        pass


def generate_speech(text: str, model_name: str, voice: Optional[str], 
                   output_path: str, **kwargs) -> bool:
    """Generate speech from text."""
    model = model_registry.get_model(model_name)
    if not model:
        _not_installed_hint(f"tts-cli model '{model_name}' not registered")
        return False

    if not model.check_availability():
        _not_installed_hint("tts-cli engine not ready (run: cli-tts --create-environment kitten-tts)")
        return False

    print(f"Generating speech with {model_name}...")
    success = model.generate_speech(text, voice, output_path, **kwargs)
    
    if success:
        print(f"✅ Speech generated successfully: {output_path}")
        _log_to_agents_tts_comms(text, model_name, voice, output_path, **kwargs)
    else:
        print("❌ Failed to generate speech")
    
    return success


def list_voices(model_name: str) -> None:
    """List voices for a specific model."""
    model = model_registry.get_model(model_name)
    if not model:
        _not_installed_hint(f"tts-cli model '{model_name}' not registered")
        return
    
    if not model.check_availability():
        _not_installed_hint("tts-cli engine not available")
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
            lang = "General"
        
        if lang not in voice_groups:
            voice_groups[lang] = []
        voice_groups[lang].append(voice)
    
    for lang, voice_list in sorted(voice_groups.items()):
        print(f"\n{lang}:")
        for voice in sorted(voice_list):
            print(f"  - {voice}")


def play_audio(file_path: str, speed: float = 1.2) -> None:
    """Play audio file using system default player at the given speed."""
    print(f"Playing audio: {file_path} (speed: {speed}x)")
    try:
        system = platform.system()
        if system == "Darwin":  # macOS
            subprocess.run(["afplay", "--rate", str(speed), file_path], check=True)
        elif system == "Linux":
            # Use ffplay for speed control if available, else fall back
            if shutil.which("ffplay"):
                subprocess.run(
                    ["ffplay", "-nodisp", "-autoexit",
                     "-af", f"atempo={speed}", file_path],
                    check=True,
                )
            elif shutil.which("aplay"):
                subprocess.run(["aplay", file_path], check=True)
            elif shutil.which("paplay"):
                subprocess.run(["paplay", file_path], check=True)
            else:
                print("❌ No audio player found (ffplay/aplay/paplay)")
        elif system == "Windows":
            # Use PowerShell to play sound (no native speed control)
            subprocess.run(["powershell", "-c", f"(New-Object Media.SoundPlayer '{file_path}').PlaySync()"], check=True)
        else:
            print(f"❌ Unsupported platform for audio playback: {system}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to play audio: {e}")
    except Exception as e:
        print(f"❌ Error playing audio: {e}")


def get_cached_output_path(retention_limit: int = 5) -> str:
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
  cli-tts --clipboard --output speech.wav
  cli-tts --text "Hi" --voice ref.wav --lang EN
  cli-tts --text "Long text..." --voice-clone my_voice.wav --lang ZH
  cli-tts --create-environment index-tts
  cli-tts --list-models
  cli-tts --list-voices --model index-tts
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
    parser.add_argument("--model", default="auto",
                       help="TTS model to use: auto (default = kitten-tts-nano) or kitten-tts-nano")
    parser.add_argument("--voice", help="Built-in KittenTTS voice name (e.g. expr-voice-5-m). Default: expr-voice-5-m. Use --list-voices to see all.")
    parser.add_argument("--lang", default=None,
                       help="(Kept for compatibility; KittenTTS is English-only. Default: EN)")
    parser.add_argument("--output", help="Output audio file path")
    # Streamlined agent entry: -p/--prompt is an alias for --text (the summary
    # + expert suggestion spoken aloud). Lets agents call one flag without
    # extra prompting; the configured default model is used automatically.
    parser.add_argument("-p", "--prompt", dest="prompt_text",
                       help="Text to speak (agent-friendly alias for --text). Use: cli-tts --prompt \"<summary>. Next step: <suggestion>\"")

    # Environment management
    parser.add_argument("--create-environment", help="Create environment for model")
    parser.add_argument("--cleanup-environment", help="Remove environment for model")
    parser.add_argument("--cleanup-all-environments", action="store_true",
                       help="Remove all environments")

    # Information commands
    parser.add_argument("--list", action="store_true",
                       help="List available models and their status (alias: --list-models)")
    parser.add_argument("--list-models", action="store_true",
                       help="List available models and their status")
    parser.add_argument("--set-default", metavar="MODEL",
                       help="Set the default TTS model for `auto` (persists to ~/.tts-cli/default_model). Choose: kitten-tts-nano")
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
    
    args = parser.parse_args()
    
    # Setup models
    setup_models()

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
    if args.list or args.list_models:
        list_models()
        return

    if args.set_default:
        ok = set_default_model(args.set_default)
        sys.exit(0 if ok else 1)

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
    # 2. Explicit flag (--prompt is the agent-friendly alias for --text)
    elif args.text or args.prompt_text:
        text = args.text or args.prompt_text
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
        text = "This is a sample of the cloned voice using IndexTTS."
        print(f"ℹ️  No text provided. Using default text: '{text}'")
        
    # Proceed if we have text
    if text:
        # Determine output path
        output_path = args.output
        if not output_path:
            output_path = get_cached_output_path()
        
        # Resolve the effective model. `auto` resolves to the user-configured
        # default (see --set-default, fallback kitten-tts-nano).
        effective_model = args.model
        if effective_model == "auto":
            effective_model = get_default_model()

        # Generate speech
        success = generate_speech(
            text=text,
            model_name=effective_model,
            voice=args.voice,
            output_path=output_path,
            voice_clone=voice_clone_path,
            lang=args.lang
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
