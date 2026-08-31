"""PocketTTS model implementation for TTS CLI.

This is the **fast default** engine: Kyutai PocketTTS
(https://github.com/kyutai-labs/pocket-tts), an open (MIT) zero-shot
voice-cloning TTS that runs cross-platform on CPU — no accelerator required —
and additionally accelerates on Apple Silicon MPS and CUDA. It is selected via
``--model pocket-tts`` (the default) or ``--model auto`` (alias).

PocketTTS is the fastest open zero-shot-cloning engine in the 2026 on-device
field (Picovoice benchmark: ~1.7s first-audio, streaming). Measured on Apple
Silicon (cold start, one-shot, 166-char input): ~11.6s wall, RTF ~1.1 on the
CPU path — ~3.7x faster cold than IndexTTS-2.5 GGUF (~43s) and ~12x faster
than the full-precision Python IndexTTS-2.5 (~142s), while preserving zero-shot
voice cloning. On Apple Silicon the optional CoreML/ANE path (PocketTTS v2.1,
macOS 26) reaches ~1.8x real-time; this adapter uses the portable Python/torch
path so the same code runs on macOS, Linux, Windows, and WSL.

The engine runs one-shot in a subprocess that exits immediately after writing
the output WAV — no daemon, no warm cache, no model state held in RAM/VRAM
between calls. Every invocation is a cold start; the process releases all
memory on exit.

All user input is passed via stdin as JSON to the runner script (no
``python -c`` with interpolated text) so there is no command-injection surface
(CWE-78).
"""

import json
import os
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger("tts_cli.pocket_tts")

from ..core.model_registry import BaseTTSModel
from ..core.environment_manager import env_manager

# CLI --lang codes mapped to PocketTTS language model names. PocketTTS ships
# European-language models; unmapped codes fall back to english.
LANG_TO_POCKETTTS = {
    "EN": "english",
    "ES": "spanish",
    "IT": "italian",
    "DE": "german",
    "PT": "portuguese",
    "FR": "french_24l",
}
DEFAULT_LANG = "EN"
SUPPORTED_LANGS = tuple(LANG_TO_POCKETTTS.keys())

MAX_TEXT_LENGTH = 5000
GENERATION_TIMEOUT = 600


class PocketTTSModel(BaseTTSModel):
    """PocketTTS (Kyutai) — fast default, zero-shot cloning, cross-platform CPU."""

    def __init__(self, model_name: str = "pocket-tts"):
        super().__init__(model_name)
        # `auto` is an alias for the fast default (pocket-tts). Normalize so the
        # alias resolves the same isolated environment and availability checks.
        self._env_key = "pocket-tts" if model_name in ("auto", "pocket-tts") else model_name
        self.python_executable = env_manager.get_python_executable(self._env_key)
        self._availability_cache: Optional[bool] = None

    def _default_voice_path(self) -> str:
        repo_root = Path(__file__).resolve().parent.parent.parent
        return str(repo_root / "examples" / "default_voice.wav")

    def _resolve_device(self) -> str:
        env_dev = os.environ.get("POCKETTTS_DEVICE", "").strip().lower()
        if env_dev in ("cpu", "mps", "cuda", "xpu"):
            return env_dev
        return "auto"

    def check_availability(self) -> bool:
        if self._availability_cache is not None:
            return self._availability_cache
        self._availability_cache = bool(self.python_executable)
        return self._availability_cache

    def check_dependencies(self) -> tuple[bool, str]:
        if not self.python_executable:
            return False, (
                "PocketTTS environment not found. Create it with: "
                "cli-tts --create-environment pocket-tts"
            )
        return True, "Dependencies OK"

    def generate_speech(self, text: str, voice: Optional[str] = None,
                        output_path: str = "output.wav", **kwargs) -> bool:
        deps_ok, deps_msg = self.check_dependencies()
        if not deps_ok:
            logger.error("PocketTTS dependencies check failed: %s", deps_msg)
            print(f"❌ {deps_msg}")
            return False

        if len(text) > MAX_TEXT_LENGTH:
            logger.warning("Text too long for PocketTTS (%d > %d)", len(text), MAX_TEXT_LENGTH)
            print(f"❌ Text too long ({len(text)} > {MAX_TEXT_LENGTH} chars).")
            return False

        lang = str(kwargs.get("lang") or DEFAULT_LANG).upper()
        language = LANG_TO_POCKETTTS.get(lang, "english")
        if lang not in SUPPORTED_LANGS:
            logger.warning("PocketTTS has no '%s' model; using english.", lang)

        voice_clone = kwargs.get("voice_clone")
        spk_audio_prompt = voice_clone or voice or self._default_voice_path()
        if not Path(spk_audio_prompt).exists():
            print(f"❌ Reference audio not found: {spk_audio_prompt}")
            return False

        return self._generate_in_environment(
            text=text,
            language=language,
            spk_audio_prompt=spk_audio_prompt,
            output_path=output_path,
            device=self._resolve_device(),
            quantize=bool(kwargs.get("quantize", False)),
        )

    def list_voices(self) -> List[str]:
        repo_root = Path(__file__).resolve().parent.parent.parent
        voices_dir = repo_root / "custom_voices"
        if not voices_dir.exists():
            return []
        return sorted(p.name for p in voices_dir.glob("*.wav"))

    def validate_voice(self, voice: str) -> bool:
        return Path(voice).exists()

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "name": "pocket-tts",
            "description": ("PocketTTS (Kyutai): zero-shot voice-cloning TTS, "
                            "cross-platform CPU + MPS/CUDA (fast default)"),
            "capabilities": ["text-to-speech", "voice-cloning", "streaming",
                             "cpu-class", "multilingual"],
            "languages": list(SUPPORTED_LANGS),
            "sample_rate": 24000,
            "max_text_length": MAX_TEXT_LENGTH,
            "version": "3.0",
            "requires_accelerator": False,
            "requires_checkpoints": False,
            "quality_mode": False,
        }

    def _generate_in_environment(self, text: str, language: str,
                                 spk_audio_prompt: str, output_path: str,
                                 device: str, quantize: bool) -> bool:
        if not self.python_executable:
            print("❌ PocketTTS environment is not available.")
            return False

        payload = {
            "language": language,
            "text": text,
            "spk_audio_prompt": spk_audio_prompt,
            "output_path": output_path,
            "device": device,
            "quantize": quantize,
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
            print(f"❌ Failed to start PocketTTS environment: {e}")
            return False

        try:
            stdout, stderr = proc.communicate(
                input=json.dumps(payload), timeout=GENERATION_TIMEOUT
            )
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            print(f"❌ PocketTTS generation timed out after {GENERATION_TIMEOUT}s.")
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
            print("❌ PocketTTS generation failed.")
            return False

        if not Path(output_path).exists():
            print("❌ PocketTTS did not produce an output file.")
            return False

        print(f"PocketTTS: Speech generated successfully to {output_path}")
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

    language = payload["language"]
    text = payload["text"]
    spk_audio_prompt = payload["spk_audio_prompt"]
    output_path = payload["output_path"]
    device = payload["device"]
    quantize = bool(payload.get("quantize", False))

    if not os.path.isfile(spk_audio_prompt):
        print(f"[runner] reference audio not found: {spk_audio_prompt}", file=sys.stderr)
        sys.exit(3)

    try:
        import torch
        from pocket_tts import TTSModel
        import soundfile as sf
        import numpy as np
    except Exception as e:
        print(f"[runner] import failed: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(4)

    if device == "auto":
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = "mps"
        elif torch.cuda.is_available():
            device = "cuda"
        else:
            device = "cpu"
    _log(f"loading PocketTTS (language={language}, device={device}, quantize={quantize})")

    try:
        model = TTSModel.load_model(language=language, quantize=quantize)
        model = model.to(device).eval()
    except Exception as e:
        print(f"[runner] model load failed: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(5)

    _log(f"building voice prompt from {spk_audio_prompt}")
    try:
        state = model.get_state_for_audio_prompt(spk_audio_prompt)
    except Exception as e:
        print(f"[runner] voice prompt failed: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(6)

    _log(f"synthesizing ({len(text)} chars)")
    try:
        with torch.no_grad():
            audio = model.generate_audio(state, text)
    except Exception as e:
        print(f"[runner] inference failed: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(7)

    try:
        arr = audio.detach().cpu().numpy() if hasattr(audio, "detach") else np.asarray(audio)
        sr = int(model.sample_rate) if hasattr(model, "sample_rate") else 24000
        sf.write(output_path, arr, sr)
    except Exception as e:
        print(f"[runner] save failed: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(8)

    _log(f"done -> {output_path}")


if __name__ == "__main__":
    main()
'''
