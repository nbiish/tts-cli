"""
Kitten TTS model implementation for TTS CLI.

This module provides the Kitten TTS model implementation, a fast
CPU-optimized TTS system with 8 built-in expressive voices.
"""

import os
import sys
import time
import signal
from pathlib import Path
from typing import List, Dict, Any, Optional
import subprocess
import logging

logger = logging.getLogger("tts_cli.kitten_tts")

from ..core.model_registry import BaseTTSModel
from ..core.environment_manager import env_manager


class TimeoutError(Exception):
    """Exception raised when generation times out."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Generation timed out")


class KittenTTSModel(BaseTTSModel):
    """Kitten TTS model implementation."""

    # Available voices in KittenTTS
    _available_voices = [
        "expr-voice-2-m",
        "expr-voice-2-f",
        "expr-voice-3-m",
        "expr-voice-3-f",
        "expr-voice-4-m",
        "expr-voice-4-f",
        "expr-voice-5-m",
        "expr-voice-5-f",
    ]

    # Configuration
    DEFAULT_TIMEOUT = 60  # seconds
    MAX_TEXT_LENGTH = 350  # characters - soft limit for KittenTTS
    # Note: Actual limit tested at ~420 chars, using 350 for safety margin
    MODEL_LOAD_TIMEOUT = 30  # seconds

    def __init__(self, model_name: str = "kitten-tts"):
        super().__init__(model_name)
        self.python_executable = env_manager.get_python_executable(model_name)
        self.is_available = self.python_executable is not None

        # Check for espeak-ng library
        self._espeak_library = self._find_espeak_library()
        self._espeak_available = self._espeak_library is not None

    def _find_espeak_library(self) -> Optional[str]:
        """Find the espeak-ng library on the system."""
        # Check environment variable first
        env_lib = os.environ.get('PHONEMIZER_ESPEAK_LIBRARY')
        if env_lib and Path(env_lib).exists():
            return env_lib

        # Try common library paths
        common_paths = [
            "/opt/homebrew/lib/libespeak-ng.dylib",  # macOS Homebrew
            "/usr/local/lib/libespeak-ng.dylib",     # macOS Homebrew (old)
            "/usr/lib/x86_64-linux-gnu/libespeak-ng.so.1",  # Linux
            "C:\\Program Files\\eSpeak NG\\libespeak-ng.dll",  # Windows
        ]

        for path in common_paths:
            if Path(path).exists():
                return path

        return None

    def check_dependencies(self) -> tuple[bool, str]:
        """Check if all dependencies are available."""
        if not self._espeak_available:
            return False, (
                "espeak-ng library not found. Install with: brew install espeak-ng\n"
                "Set PHONEMIZER_ESPEAK_LIBRARY environment variable if installed in custom location."
            )

        if not self.is_available:
            return False, "KittenTTS environment not found. Create with: cli-tts --create-environment kitten-tts"

        return True, "Dependencies OK"

    def generate_speech(self, text: str, voice: Optional[str] = None,
                       output_path: str = "output.wav", **kwargs) -> bool:
        """Generate speech from text using Kitten TTS."""
        # Check dependencies
        deps_ok, deps_msg = self.check_dependencies()
        if not deps_ok:
            logger.error(f"KittenTTS dependencies check failed: {deps_msg}")
            return False

        # Check text length
        if len(text) > self.MAX_TEXT_LENGTH:
            logger.warning(f"Text too long for KittenTTS ({len(text)} > {self.MAX_TEXT_LENGTH})")
            return False

        # Use default voice if none specified
        if not voice:
            voice = "expr-voice-2-m"
            logger.info(f"No voice specified. Using default: {voice}")

        # Validate voice
        if voice not in self._available_voices:
            logger.warning(f"Unknown voice: {voice}. Available: {self._available_voices}")
            return False

        # Try in-process generation first
        try:
            return self._generate_in_process(text, voice, output_path)
        except ImportError:
            logger.info("KittenTTS not available in current process, trying isolated environment...")
            return self._generate_in_environment(text, voice, output_path)

    def _generate_in_process(self, text: str, voice: str, output_path: str) -> bool:
        """Generate speech in the current process with timeout."""
        try:
            from kittentts import KittenTTS
            import soundfile as sf
            import numpy as np
        except ImportError as e:
            logger.error(f"Failed to import KittenTTS: {e}")
            return False

        # Set up environment variable for espeak
        if self._espeak_library:
            os.environ['PHONEMIZER_ESPEAK_LIBRARY'] = self._espeak_library

        logger.info(f"Initializing KittenTTS with voice: {voice}")

        # Load model with timeout
        def load_model():
            return KittenTTS()

        model = self._run_with_timeout(load_model, self.MODEL_LOAD_TIMEOUT, "Model load")

        if model is None:
            return False

        # Generate audio with timeout
        def generate_audio():
            return model.generate(text, voice=voice)

        audio = self._run_with_timeout(generate_audio, self.DEFAULT_TIMEOUT, "Generation")

        if audio is None:
            return False

        # Save audio
        try:
            sf.write(output_path, audio, 24000)
            logger.info(f"KittenTTS: Speech generated successfully to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save audio: {e}")
            return False

    def _run_with_timeout(self, func, timeout: int, operation: str):
        """Run a function with a timeout."""
        # Set signal handler for timeout
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)

        try:
            signal.alarm(timeout)
            result = func()
            signal.alarm(0)  # Cancel alarm
            return result
        except TimeoutError:
            logger.error(f"{operation} timed out after {timeout} seconds")
            return None
        except Exception as e:
            logger.error(f"{operation} failed: {e}")
            return None
        finally:
            signal.signal(signal.SIGALRM, old_handler)

    def _generate_in_environment(self, text: str, voice: str, output_path: str) -> bool:
        """Generate speech in isolated environment."""
        if not self.python_executable:
            logger.error("No Python executable available for isolated environment")
            return False

        script_content = self._create_generation_script(text, voice, output_path)

        # Run with timeout using subprocess
        try:
            proc = subprocess.Popen(
                [str(self.python_executable), "-c", script_content],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            try:
                stdout, stderr = proc.wait(timeout=self.DEFAULT_TIMEOUT + 10)
                if stdout:
                    logger.info(stdout)
                if stderr:
                    logger.error(stderr)

                return proc.returncode == 0
            except subprocess.TimeoutExpired:
                proc.kill()
                logger.error(f"Generation in isolated environment timed out")
                return False

        except Exception as e:
            logger.error(f"Failed to run in isolated environment: {e}")
            return False

    def list_voices(self) -> List[str]:
        """List available voices for this model."""
        return self._available_voices.copy()

    def validate_voice(self, voice: str) -> bool:
        """Validate if a voice is available for this model."""
        return voice in self._available_voices

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and capabilities."""
        return {
            "name": "kitten-tts",
            "description": "Fast CPU-optimized TTS model with 8 expressive voices",
            "capabilities": ["text-to-speech", "fast-inference", "cpu-optimized"],
            "languages": ["en"],
            "sample_rate": 24000,
            "voices": len(self._available_voices),
            "max_text_length": self.MAX_TEXT_LENGTH,
            "timeout": self.DEFAULT_TIMEOUT,
            "espeak_required": True,
            "version": "0.1.0"
        }

    def _create_generation_script(self, text: str, voice: str, output_path: str) -> str:
        """Create a script for Kitten TTS generation."""
        escaped_text = text.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'").replace('\n', '\\n').replace('\r', '\\r')

        espeak_lib = self._espeak_library or ""

        return f'''
import os
import sys
import signal

# Set espeak library path
if "{espeak_lib}":
    os.environ['PHONEMIZER_ESPEAK_LIBRARY'] = "{espeak_lib}"

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

def run_with_timeout(func, timeout, operation):
    import signal
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    try:
        signal.alarm(timeout)
        result = func()
        signal.alarm(0)
        return result
    except TimeoutError:
        print(f"{{operation}} timed out after {{timeout}} seconds", file=sys.stderr)
        return None
    finally:
        signal.signal(signal.SIGALRM, old_handler)

def generate():
    try:
        from kittentts import KittenTTS
        import soundfile as sf
        import numpy as np
    except ImportError as e:
        print(f"Error: {{e}}", file=sys.stderr)
        sys.exit(1)

    text = "{escaped_text}"
    output_path = "{output_path}"
    voice = "{voice}"

    print(f"Loading KittenTTS model...")

    def load_model():
        return KittenTTS()

    model = run_with_timeout(load_model, {self.MODEL_LOAD_TIMEOUT}, "Model load")
    if model is None:
        sys.exit(1)

    print(f"Generating audio for text: {{text[:50]}}...")

    def generate_audio():
        return model.generate(text, voice=voice)

    audio = run_with_timeout(generate_audio, {self.DEFAULT_TIMEOUT}, "Generation")
    if audio is None:
        sys.exit(1)

    print(f"Saving to {{output_path}}...")
    sf.write(output_path, audio, 24000)
    print("Done.")

if __name__ == "__main__":
    generate()
'''
