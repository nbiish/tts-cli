"""MOSS-TTS-Nano model implementation for TTS CLI.

MOSS-TTS-Nano (https://github.com/OpenMOSS/MOSS-TTS-Nano) is a tiny autoregressive
TTS model (100M LLM + 20M Cat Audio Tokenizer) running 48 kHz stereo zero-shot
speech synthesis on CPU using onnxruntime.

It supports:
  - High-fidelity studio voice cloning from short reference audio clips.
  - Built-in calibrated reference voices (e.g. `en_narrator`).
  - Text normalization with Markdown stripping and technical acronym pacing.
  - Post-generation WAV speedup (1.8x) and peak audio normalization.
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
DEFAULT_VOICE = "en_narrator"
BUILT_IN_VOICES = ("en_narrator", "en_conversational_female")

MAX_TEXT_LENGTH = 5000
GENERATION_TIMEOUT = 300

# Post-generation speedup factor applied to raw MOSS-TTS output WAV.
# MOSS-TTS generates at native pace; we speed up the result to match
# the heard rate used by KittenTTS (1.8x) for consistent pacing.
MOSS_OUTPUT_SPEED = 1.8

# Maximum allowed reference audio duration in seconds.
# Prevents denial-of-service in the tokenizer decoder from oversized clips.
MAX_REFERENCE_DURATION_SECS = 30.0


def _resolve_bundled_voice_path(voice_name: str | Path | None) -> Path:
    """Resolve a voice identifier or path to an existing reference audio file."""
    # Find project root
    project_root = Path(__file__).resolve().parent.parent.parent
    voices_dir = project_root / "assets" / "voices"

    if not voice_name:
        default_path = voices_dir / "en_narrator.wav"
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
    fallback = voices_dir / "en_narrator.wav"
    if fallback.is_file():
        return fallback

    return direct_path


def _speedup_and_normalize_wav(wav_path: Path, speed: float) -> bool:
    """Time-stretch a WAV file by *speed* without pitch change and normalize.

    Uses ``ffmpeg`` with the ``atempo`` filter (WSOLA-based time-stretching
    that preserves pitch) and ``loudnorm`` (EBU R128 broadcast loudness
    normalization).  This avoids the chipmunk effect caused by sample
    decimation / resampling approaches.

    Falls back to peak-only normalization via numpy/soundfile when ffmpeg
    is not available.

    The file is overwritten in-place on success.
    Returns True on success, False on error (original file left intact).
    """
    import shutil
    import tempfile

    wav_str = str(wav_path)

    # --- Try ffmpeg (best quality: WSOLA time-stretch + EBU R128 loudnorm) ---
    ffmpeg_bin = shutil.which("ffmpeg")
    if ffmpeg_bin:
        try:
            fd, tmp_out = tempfile.mkstemp(suffix=".wav")
            import os
            os.close(fd)

            # Build the audio filter chain.
            # atempo supports 0.5–100.0; for speed > 2.0 chain multiple.
            filters: list[str] = []
            if speed != 1.0 and speed > 0:
                remaining = speed
                while remaining > 2.0:
                    filters.append("atempo=2.0")
                    remaining /= 2.0
                if remaining != 1.0:
                    filters.append(f"atempo={remaining:.4f}")

            # EBU R128 loudness normalization (-16 LUFS integrated, -1 dBTP)
            filters.append("loudnorm=I=-16:TP=-1:LRA=11")

            af = ",".join(filters)
            cmd = [
                ffmpeg_bin, "-y", "-i", wav_str,
                "-af", af,
                "-ar", "48000",   # preserve 48 kHz
                "-ac", "2",       # preserve stereo
                tmp_out,
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                check=False,
                timeout=60,
            )
            if result.returncode == 0 and Path(tmp_out).stat().st_size > 0:
                shutil.move(tmp_out, wav_str)
                return True
            else:
                logger.warning(
                    "ffmpeg post-processing failed (rc=%d), trying fallback: %s",
                    result.returncode,
                    result.stderr.decode("utf-8", errors="replace")[:200],
                )
                os.unlink(tmp_out)
        except Exception as exc:
            logger.warning("ffmpeg post-processing error, trying fallback: %s", exc)

    # --- Fallback: peak-normalize only (no tempo change to avoid pitch shift) ---
    try:
        import soundfile as sf
        import numpy as np

        data, sr = sf.read(wav_str, dtype="float32")
        peak = np.max(np.abs(data))
        if peak > 0:
            target_peak = 10 ** (-1.0 / 20.0)  # -1 dBFS ≈ 0.891
            data = data * (target_peak / peak)
            np.clip(data, -1.0, 1.0, out=data)
        sf.write(wav_str, data, sr)
        if speed != 1.0:
            logger.warning(
                "MOSS-TTS: ffmpeg not available — output is peak-normalized "
                "but NOT sped up (install ffmpeg for tempo change without pitch shift)"
            )
        return True
    except Exception as exc:
        logger.warning("MOSS-TTS: WAV post-processing failed (output left as-is): %s", exc)
        return False


ALLOWED_AUDIO_EXTENSIONS = {".wav", ".flac", ".ogg", ".mp3", ".m4a"}
MAX_REFERENCE_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB max


def _check_reference_duration(audio_path: Path, max_secs: float) -> bool:
    """Validate that reference audio file format, size, and duration are within safe bounds.

    Prevents denial-of-service through oversized reference clips or unhandled formats
    that would cause excessive tokenizer/decoder computation or memory exhaustion.
    """
    if not audio_path.exists() or not audio_path.is_file():
        logger.error("MOSS-TTS: Reference audio file does not exist: %s", audio_path)
        return False

    # Check extension
    if audio_path.suffix.lower() not in ALLOWED_AUDIO_EXTENSIONS:
        logger.error(
            "MOSS-TTS: Unsupported audio format '%s' for reference audio: %s (allowed: %s)",
            audio_path.suffix, audio_path, ", ".join(sorted(ALLOWED_AUDIO_EXTENSIONS))
        )
        return False

    # Check file size bound
    try:
        file_size = audio_path.stat().st_size
        if file_size > MAX_REFERENCE_FILE_SIZE_BYTES:
            logger.error(
                "MOSS-TTS: Reference audio file size (%d bytes) exceeds maximum limit (%d bytes): %s",
                file_size, MAX_REFERENCE_FILE_SIZE_BYTES, audio_path
            )
            return False
    except Exception as exc:
        logger.warning("MOSS-TTS: Could not verify file size for %s: %s", audio_path, exc)

    try:
        import soundfile as sf
        info = sf.info(str(audio_path))
        if info.duration > max_secs:
            logger.error(
                "MOSS-TTS: Reference audio %.1fs exceeds maximum %.1fs: %s",
                info.duration, max_secs, audio_path,
            )
            return False
        return True
    except Exception as exc:
        logger.warning("MOSS-TTS: Could not validate reference audio duration: %s", exc)
        # Fail open for bundled voices (they are trusted)
        return True


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
            "output_speed": MOSS_OUTPUT_SPEED,
        }

    def generate_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        output_path: str = "output.wav",
        **kwargs: Any,
    ) -> bool:
        """Generate speech using MOSS-TTS-Nano ONNX CPU runtime.

        After raw generation the output WAV is sped up by MOSS_OUTPUT_SPEED
        (default 1.8x) and peak-normalized to -1 dBFS.
        """
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

        # Security: validate reference audio duration
        if not _check_reference_duration(chosen_voice_path, MAX_REFERENCE_DURATION_SECS):
            return False

        target_output = Path(output_path) if output_path else Path("output.wav")
        target_output.parent.mkdir(parents=True, exist_ok=True)

        clean_text = normalize_text_for_speech(text)

        payload = {
            "text": clean_text,
            "prompt_audio_path": str(chosen_voice_path),
            "output_path": str(target_output.resolve()),
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

            # Post-process: speedup + peak normalize
            _speedup_and_normalize_wav(target_output, MOSS_OUTPUT_SPEED)

            logger.info("MOSS-TTS: Speech generated successfully to %s", target_output)
            return True

        except subprocess.TimeoutExpired:
            logger.error("MOSS-TTS: Generation timed out after %ds", GENERATION_TIMEOUT)
            return False
        except Exception as exc:
            logger.error("MOSS-TTS: Unexpected error during generation: %s", exc)
            return False
