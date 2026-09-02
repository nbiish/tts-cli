"""MOSS-TTS-Nano model implementation for TTS CLI.

MOSS-TTS-Nano (https://github.com/OpenMOSS/MOSS-TTS-Nano) is a tiny autoregressive
TTS model (100M LLM + 20M Cat Audio Tokenizer) running 48 kHz stereo zero-shot
speech synthesis on CPU using onnxruntime.

It supports:
  - High-fidelity studio voice cloning from short reference audio clips.
  - Built-in calibrated reference voices (e.g. `en_calm_female`).
  - Text normalization with Markdown stripping and technical acronym pacing.
  - Multi-language support (English, Chinese, Japanese, etc.).
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger("tts_cli.moss_tts")

from ..core.model_registry import BaseTTSModel
from ..core.environment_manager import env_manager
from ..core.normalizer import normalize_text_for_speech

DEFAULT_MODEL_NAME = "moss-tts-nano"
DEFAULT_VOICE = "en_calm_female"
BUILT_IN_VOICES = ("en_calm_female", "en_conversational_female")

MAX_TEXT_LENGTH = 5000
GENERATION_TIMEOUT = 300


def _resolve_bundled_voice_path(voice_name: str | Path | None) -> Path:
    """Resolve a voice identifier or path to an existing reference audio file."""
    # Find project root
    project_root = Path(__file__).resolve().parent.parent.parent
    voices_dir = project_root / "assets" / "voices"

    if not voice_name:
        default_path = voices_dir / "en_calm_female.wav"
        if default_path.exists():
            return default_path

    voice_str = str(voice_name)
    direct_path = Path(voice_str).expanduser().resolve()
    if direct_path.is_file():
        return direct_path

    # Check assets/voices/
    candidate = voices_dir / f"{voice_str}.wav"
    if candidate.is_file():
        return candidate

    candidate_direct = voices_dir / voice_str
    if candidate_direct.is_file():
        return candidate_direct

    # Fallback to default
    fallback = voices_dir / "en_calm_female.wav"
    if fallback.is_file():
        return fallback

    return direct_path


class MossTTSModel(BaseTTSModel):
    """MOSS-TTS-Nano — 48 kHz stereo zero-shot speech synthesis ONNX CPU model."""

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME):
        super().__init__(model_name)
        self._env_key = "moss-tts"
        self.python_executable = env_manager.get_python_executable(self._env_key)
        self._availability_cache: Optional[bool] = None

    def check_availability(self) -> bool:
        if self._availability_cache is not None:
            return self._availability_cache
        self.python_executable = env_manager.get_python_executable(self._env_key)
        self._availability_cache = bool(self.python_executable)
        return self._availability_cache

    def check_dependencies(self) -> tuple[bool, str]:
        if not self.python_executable:
            return False, f"Missing Python environment for '{self._env_key}'. Run: tts-cli env create {self._env_key}"
        return True, "Environment ready"

    def get_supported_voices(self) -> List[str]:
        return list(BUILT_IN_VOICES)

    def list_voices(self) -> List[str]:
        return list(BUILT_IN_VOICES)

    def validate_voice(self, voice: str) -> bool:
        if voice in BUILT_IN_VOICES:
            return True
        path = Path(voice).expanduser().resolve()
        return path.is_file()

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "name": self.model_name,
            "sample_rate": 48000,
            "channels": 2,
            "supports_voice_cloning": True,
            "supports_speed_control": True,
            "default_voice": DEFAULT_VOICE,
        }

    def generate_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        output_path: str = "output.wav",
        **kwargs: Any,
    ) -> bool:
        """Generate speech using MOSS-TTS-Nano ONNX CPU runtime."""
        speed = float(kwargs.get("speed", 1.0))
        if not text or not text.strip():
            logger.error("MOSS-TTS: Empty text provided")
            return False

        if len(text) > MAX_TEXT_LENGTH:
            logger.error(
                "MOSS-TTS: Text length %d exceeds maximum allowed %d",
                len(text),
                MAX_TEXT_LENGTH,
            )
            return False

        if not self.check_availability():
            logger.error(
                "MOSS-TTS environment '%s' is not available. Run: tts-cli env create %s",
                self._env_key,
                self._env_key,
            )
            return False

        chosen_voice_path = _resolve_bundled_voice_path(voice or DEFAULT_VOICE)
        target_output = Path(output_path) if output_path else Path("output.wav")
        target_output.parent.mkdir(parents=True, exist_ok=True)

        clean_text = normalize_text_for_speech(text)

        payload = {
            "text": clean_text,
            "prompt_audio_path": str(chosen_voice_path),
            "output_path": str(target_output.resolve()),
            "speed": float(speed),
        }

        project_root = Path(__file__).resolve().parent.parent.parent
        models_dir = Path.home() / ".tts-cli" / "models"

        runner_script = f"""
import sys
import json
from pathlib import Path

sys.path.insert(0, {str(project_root)!r})

from tts_cli.core.onnx_tts_runtime import OnnxTtsRuntime

def run():
    payload = json.loads(sys.stdin.read())
    text = payload["text"]
    prompt_audio = payload["prompt_audio_path"]
    out_path = payload["output_path"]

    models_dir = Path({str(models_dir)!r})
    runtime = OnnxTtsRuntime(model_dir=models_dir, thread_count=4)
    res = runtime.synthesize(
        text=text,
        prompt_audio_path=prompt_audio,
        output_audio_path=out_path,
        sample_mode="fixed",
        enable_wetext=False,
        enable_normalize_tts_text=True,
    )
    print(f"MOSS-TTS: Generated {{out_path}}")

if __name__ == "__main__":
    run()
"""

        try:
            cmd = [str(self.python_executable), "-c", runner_script]
            input_bytes = json.dumps(payload).encode("utf-8")
            result = subprocess.run(
                cmd,
                input=input_bytes,
                capture_output=True,
                check=False,
                timeout=GENERATION_TIMEOUT,
            )

            if result.returncode != 0:
                logger.error(
                    "MOSS-TTS execution failed (rc=%d):\nstderr: %s\nstdout: %s",
                    result.returncode,
                    result.stderr.decode("utf-8", errors="replace"),
                    result.stdout.decode("utf-8", errors="replace"),
                )
                return False

            if not target_output.exists() or target_output.stat().st_size == 0:
                logger.error("MOSS-TTS: Output file was not created or is empty: %s", target_output)
                return False

            logger.info("MOSS-TTS: Speech generated successfully to %s", target_output)
            return True

        except subprocess.TimeoutExpired:
            logger.error("MOSS-TTS: Generation timed out after %ds", GENERATION_TIMEOUT)
            return False
        except Exception as exc:
            logger.error("MOSS-TTS: Unexpected error during generation: %s", exc)
            return False
