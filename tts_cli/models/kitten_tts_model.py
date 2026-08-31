"""KittenTTS model implementation for TTS CLI.

KittenTTS (https://github.com/KittenML/KittenTTS) is an ultra-lightweight
ONNX-based TTS that runs on CPU — no accelerator required — making it the most
portable engine in the stack (smallest footprint, fastest cold load). It is
exposed in two variants:

  - ``kitten-tts-nano``: the 15M / 25MB int8 model (fastest cold load ~7.9s,
    RTF ~0.47 on Apple Silicon CPU).
  - ``kitten-tts-mini``: the 80M / 80MB model (cold ~9.5s, RTF ~0.66).

KittenTTS uses 8 FIXED built-in voices (expr-voice-2..5 m/f) — it does NOT do
zero-shot voice cloning. ``--voice`` for this engine selects a built-in voice
name rather than a reference audio path.

The engine runs one-shot in a subprocess that exits immediately after writing
the output WAV — no daemon, no warm cache, no model state held in RAM between
calls. All user input is passed via stdin as JSON (CWE-78 safe).
"""

import json
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger("tts_cli.kitten_tts")

from ..core.model_registry import BaseTTSModel
from ..core.environment_manager import env_manager

# HF repo ids for each variant.
VARIANT_TO_REPO = {
    "kitten-tts-nano": "KittenML/kitten-tts-nano-0.8-int8",
    "kitten-tts-mini": "KittenML/kitten-tts-mini-0.8",
}
DEFAULT_VARIANT = "kitten-tts-nano"
DEFAULT_VOICE = "expr-voice-5-m"
BUILT_IN_VOICES = (
    "expr-voice-2-m", "expr-voice-2-f",
    "expr-voice-3-m", "expr-voice-3-f",
    "expr-voice-4-m", "expr-voice-4-f",
    "expr-voice-5-m", "expr-voice-5-f",
)

MAX_TEXT_LENGTH = 5000
GENERATION_TIMEOUT = 300


class KittenTTSModel(BaseTTSModel):
    """KittenTTS — ultra-lightweight CPU ONNX TTS with fixed built-in voices."""

    def __init__(self, model_name: str = "kitten-tts-nano"):
        super().__init__(model_name)
        # Both variants share one isolated env ("kitten-tts") and differ only
        # by the HF repo id passed to the runner. Normalize the env key.
        self._env_key = "kitten-tts"
        self._variant = model_name if model_name in VARIANT_TO_REPO else DEFAULT_VARIANT
        self.python_executable = env_manager.get_python_executable(self._env_key)
        self._availability_cache: Optional[bool] = None

    def check_availability(self) -> bool:
        if self._availability_cache is not None:
            return self._availability_cache
        self._availability_cache = bool(self.python_executable)
        return self._availability_cache

    def check_dependencies(self) -> tuple[bool, str]:
        if not self.python_executable:
            return False, (
                "KittenTTS environment not found. Create it with: "
                "cli-tts --create-environment kitten-tts"
            )
        return True, "Dependencies OK"

    def generate_speech(self, text: str, voice: Optional[str] = None,
                        output_path: str = "output.wav", **kwargs) -> bool:
        deps_ok, deps_msg = self.check_dependencies()
        if not deps_ok:
            logger.error("KittenTTS dependencies check failed: %s", deps_msg)
            print(f"❌ {deps_msg}")
            return False

        if len(text) > MAX_TEXT_LENGTH:
            print(f"❌ Text too long ({len(text)} > {MAX_TEXT_LENGTH} chars).")
            return False

        # `voice` for KittenTTS is a built-in voice name (not a path). Validate
        # it; fall back to the default if absent or unrecognized.
        chosen_voice = voice or DEFAULT_VOICE
        if chosen_voice not in BUILT_IN_VOICES:
            if voice:
                logger.warning("Unknown KittenTTS voice '%s'; using %s", voice, DEFAULT_VOICE)
            chosen_voice = DEFAULT_VOICE

        speed = float(kwargs.get("speed", 1.0))
        return self._generate_in_environment(
            text=text,
            repo_id=VARIANT_TO_REPO[self._variant],
            voice=chosen_voice,
            speed=speed,
            output_path=output_path,
        )

    def list_voices(self) -> List[str]:
        return list(BUILT_IN_VOICES)

    def validate_voice(self, voice: str) -> bool:
        return voice in BUILT_IN_VOICES

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "name": self._variant,
            "description": (f"KittenTTS {self._variant} — ultra-lightweight CPU "
                            "ONNX TTS, fixed built-in voices"),
            "capabilities": ["text-to-speech", "cpu-class", "fixed-voices"],
            "languages": ["EN"],
            "sample_rate": 24000,
            "max_text_length": MAX_TEXT_LENGTH,
            "version": "0.8",
            "requires_accelerator": False,
            "requires_checkpoints": False,
            "voices": list(BUILT_IN_VOICES),
            "quality_mode": False,
        }

    def _generate_in_environment(self, text: str, repo_id: str, voice: str,
                                 speed: float, output_path: str) -> bool:
        if not self.python_executable:
            print("❌ KittenTTS environment is not available.")
            return False

        payload = {
            "repo_id": repo_id,
            "text": text,
            "voice": voice,
            "speed": speed,
            "output_path": output_path,
        }

        try:
            proc = subprocess.Popen(
                [str(self.python_executable), "-c", self._runner_script()],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except OSError as e:
            print(f"❌ Failed to start KittenTTS environment: {e}")
            return False

        try:
            stdout, stderr = proc.communicate(
                input=json.dumps(payload), timeout=GENERATION_TIMEOUT
            )
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            print(f"❌ KittenTTS generation timed out after {GENERATION_TIMEOUT}s.")
            return False

        if stdout:
            for line in stdout.splitlines():
                if line.startswith("[runner] "):
                    print(line[len("[runner] "):])
                else:
                    logger.info(line)
        if stderr:
            for line in stderr.splitlines():
                logger.error(line)

        if proc.returncode != 0:
            print("❌ KittenTTS generation failed.")
            return False

        if not Path(output_path).exists():
            print("❌ KittenTTS did not produce an output file.")
            return False

        print(f"KittenTTS: Speech generated successfully to {output_path}")
        return True

    @staticmethod
    def _runner_script() -> str:
        return r'''
import json
import os
import sys
import traceback


def _log(msg):
    print(f"[runner] {msg}", flush=True)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception as e:
        print(f"[runner] failed to read JSON payload: {e}", file=sys.stderr)
        sys.exit(2)

    repo_id = payload["repo_id"]
    text = payload["text"]
    voice = payload["voice"]
    speed = float(payload.get("speed", 1.0))
    output_path = payload["output_path"]

    try:
        from kittentts import KittenTTS
    except Exception as e:
        print(f"[runner] kittentts import failed: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(4)

    _log(f"loading KittenTTS ({repo_id}, voice={voice})")
    try:
        tts = KittenTTS(model_name=repo_id)
    except Exception as e:
        print(f"[runner] model load failed: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(5)

    _log(f"synthesizing ({len(text)} chars)")
    try:
        tts.generate_to_file(text, output_path, voice=voice, speed=speed,
                              sample_rate=24000)
    except Exception as e:
        print(f"[runner] inference failed: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(7)

    _log(f"done -> {output_path}")


if __name__ == "__main__":
    main()
'''
