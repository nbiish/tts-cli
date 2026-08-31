"""
IndexTTS model implementation for TTS CLI.

This module provides the IndexTTS-2.5 model implementation — an industrial-level
zero-shot text-to-speech system with voice cloning, emotion control, speaking-speed
control, and multilingual support (ZH / EN / JA / ES / AR).

IndexTTS is the sole TTS engine for this CLI. It requires an accelerator
(CUDA, MPS, or XPU) and model checkpoints downloaded separately. It is selected via
``--model index-tts`` (or ``--model auto``, which is an alias). When the environment
or checkpoints are missing it reports unavailable with an actionable message.

Because IndexTTS requires Python ``>=3.10,<3.12`` while this project targets
``>=3.12``, the engine runs in an isolated ``uv`` environment pinned to Python 3.11.
The adapter communicates with it via subprocess, passing all user input through stdin
as JSON to avoid command injection (no ``python -c`` with interpolated text).
"""

import json
import os
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger("tts_cli.index_tts")

from ..core.model_registry import BaseTTSModel
from ..core.environment_manager import env_manager


# Languages supported by IndexTTS-2.5 (multilingual).
SUPPORTED_LANGS = ("ZH", "EN", "JA", "ES", "AR")
DEFAULT_LANG = "EN"

# Soft text length limit (characters). IndexTTS chunks internally, but we keep a sane
# upper bound to avoid pathological single-segment loads on low-VRAM cards.
MAX_TEXT_LENGTH = 5000

# Subprocess hard timeout (seconds). IndexTTS model load + inference can be slow on
# CPU/MPS; allow generous headroom.
GENERATION_TIMEOUT = 600


class IndexTTSModel(BaseTTSModel):
    """IndexTTS-2.5 model implementation (opt-in, GPU/MPS class)."""

    def __init__(self, model_name: str = "index-tts"):
        super().__init__(model_name)
        # `auto` is an alias for `index-tts`; normalize the env-lookup key so the
        # alias resolves the same isolated environment and checkpoints.
        self._env_key = "index-tts" if model_name == "auto" else model_name
        self.python_executable = env_manager.get_python_executable(self._env_key)
        self._model_dir = self._resolve_model_dir()
        # Cache the (relatively expensive) accelerator probe so repeated
        # check_availability() calls during a CLI session stay cheap.
        self._availability_cache: Optional[bool] = None

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_model_dir() -> Optional[Path]:
        """Locate the IndexTTS checkpoints directory.

        Order of precedence:
          1. ``INDEX_TTS_MODEL_DIR`` env var (absolute path).
          2. ``checkpoints/`` at the project root (IndexTTS default layout,
             must contain ``config.yaml``).
        """
        env_dir = os.environ.get("INDEX_TTS_MODEL_DIR")
        if env_dir:
            p = Path(env_dir).expanduser()
            if (p / "config.yaml").exists():
                return p
            logger.warning(
                "INDEX_TTS_MODEL_DIR=%s set but config.yaml not found there", env_dir
            )

        # Project root: walk up from this file to find pyproject.toml.
        current = Path(__file__).resolve().parent
        while current != current.parent:
            if (current / "pyproject.toml").exists():
                candidate = current / "checkpoints"
                if (candidate / "config.yaml").exists():
                    return candidate
                return None  # project root found, but no checkpoints
            current = current.parent
        return None

    def _has_accelerator(self) -> bool:
        """Probe the isolated env for an accelerator (cuda/mps/xpu).

        Runs a tiny snippet in the isolated environment so we never import torch
        in the host (Python 3.12) process, which may not have torch installed.
        Result is cached on the instance.
        """
        if self._availability_cache is not None:
            return self._availability_cache

        if not self.python_executable:
            self._availability_cache = False
            return False

        probe = (
            "import sys\n"
            "try:\n"
            "    import torch\n"
            "    ok = bool(torch.cuda.is_available()\n"
            "              or (hasattr(torch.backends, 'mps') and torch.backends.mps.is_available())\n"
            "              or (hasattr(torch, 'xpu') and torch.xpu.is_available()))\n"
            "except Exception:\n"
            "    ok = False\n"
            "sys.stdout.write('1' if ok else '0')\n"
        )
        try:
            proc = subprocess.run(
                [str(self.python_executable), "-c", probe],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            self._availability_cache = proc.returncode == 0 and proc.stdout.strip() == "1"
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            logger.debug("accelerator probe failed: %s", e)
            self._availability_cache = False
        return self._availability_cache

    # ------------------------------------------------------------------
    # BaseTTSModel interface
    # ------------------------------------------------------------------

    def check_availability(self) -> bool:
        """Available only when env + checkpoints + accelerator are all present.

        When any of these is missing, ``generate_speech`` reports the specific
        gap with an actionable install hint instead of crashing.
        """
        if not self.python_executable:
            return False
        if not self._model_dir:
            return False
        return self._has_accelerator()

    def check_dependencies(self) -> tuple[bool, str]:
        """Return (ok, message) with actionable install hints."""
        if not self.python_executable:
            return False, (
                "IndexTTS environment not found. Create it with: "
                "cli-tts --create-environment index-tts"
            )
        if not self._model_dir:
            return False, (
                "IndexTTS checkpoints not found. Download IndexTTS-2.5 with:\n"
                "  hf download IndexTeam/IndexTTS-2.5 --local-dir=checkpoints\n"
                "or set INDEX_TTS_MODEL_DIR to an existing checkpoint directory."
            )
        if not self._has_accelerator():
            return False, (
                "No accelerator detected (CUDA/MPS/XPU). IndexTTS-2.5 requires an "
                "accelerator (Apple Silicon MPS is supported). Create the env and "
                "download checkpoints, then re-run on a machine with MPS/CUDA/XPU."
            )
        return True, "Dependencies OK"

    def generate_speech(self, text: str, voice: Optional[str] = None,
                       output_path: str = "output.wav", **kwargs) -> bool:
        """Generate speech from text using IndexTTS-2.5.

        ``voice`` (or ``kwargs['voice_clone']``) is treated as the reference audio
        path for zero-shot voice cloning — IndexTTS's core capability. When no
        reference is provided, IndexTTS's own default prompt is used.
        """
        deps_ok, deps_msg = self.check_dependencies()
        if not deps_ok:
            logger.error("IndexTTS dependencies check failed: %s", deps_msg)
            print(f"❌ {deps_msg}")
            return False

        if len(text) > MAX_TEXT_LENGTH:
            logger.warning("Text too long for IndexTTS (%d > %d)", len(text), MAX_TEXT_LENGTH)
            print(f"❌ Text too long ({len(text)} > {MAX_TEXT_LENGTH} chars).")
            return False

        lang = str(kwargs.get("lang") or DEFAULT_LANG).upper()
        if lang not in SUPPORTED_LANGS:
            logger.warning("Unsupported lang '%s'; falling back to %s", lang, DEFAULT_LANG)
            lang = DEFAULT_LANG

        # Reference audio: explicit voice_clone wins, then --voice (a path).
        voice_clone = kwargs.get("voice_clone")
        spk_audio_prompt = voice_clone or voice or None
        if spk_audio_prompt and not Path(spk_audio_prompt).exists():
            print(f"❌ Reference audio not found: {spk_audio_prompt}")
            return False

        return self._generate_in_environment(
            text=text,
            lang=lang,
            spk_audio_prompt=spk_audio_prompt,
            output_path=output_path,
            use_bf16=bool(kwargs.get("use_bf16", True)),
            use_qwen_emo=bool(kwargs.get("use_qwen_emo", False)),
            emo_alpha=kwargs.get("emo_alpha"),
            emo_audio_prompt=kwargs.get("emo_audio_prompt"),
            duration_factor=kwargs.get("duration_factor"),
        )

    def list_voices(self) -> List[str]:
        """IndexTTS has no fixed voice catalog — any reference WAV is a 'voice'.

        We surface the project's ``custom_voices/`` directory contents so
        ``--list-voices --model index-tts`` is still useful.
        """
        repo_root = Path(__file__).resolve().parent.parent.parent
        voices_dir = repo_root / "custom_voices"
        if not voices_dir.exists():
            return []
        return sorted(p.name for p in voices_dir.glob("*.wav"))

    def validate_voice(self, voice: str) -> bool:
        """A 'voice' for IndexTTS is any existing audio file path."""
        return Path(voice).exists()

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "name": "index-tts",
            "description": "IndexTTS-2.5: zero-shot multilingual voice-cloning TTS (GPU/MPS)",
            "capabilities": ["text-to-speech", "voice-cloning", "emotion-control",
                             "speed-control", "pronunciation-control", "multilingual",
                             "gpu-class"],
            "languages": list(SUPPORTED_LANGS),
            "sample_rate": 22050,
            "max_text_length": MAX_TEXT_LENGTH,
            "version": "2.5",
            "requires_accelerator": True,
            "requires_checkpoints": True,
            "model_dir": str(self._model_dir) if self._model_dir else None,
        }

    # ------------------------------------------------------------------
    # Isolated-environment execution
    # ------------------------------------------------------------------

    def _generate_in_environment(self, text: str, lang: str,
                                 spk_audio_prompt: Optional[str], output_path: str,
                                 use_bf16: bool, use_qwen_emo: bool,
                                 emo_alpha: Optional[float],
                                 emo_audio_prompt: Optional[str],
                                 duration_factor: Optional[float]) -> bool:
        """Run IndexTTS in its isolated Python 3.11 uv environment.

        All user-controlled values are passed via stdin as JSON; the runner script
        reads them from stdin so no interpolation into the command line is needed
        (CWE-78 / command-injection safe).
        """
        if not self.python_executable:
            print("❌ IndexTTS environment is not available.")
            return False

        runner = self._runner_script()
        payload = {
            "cfg_path": str(self._model_dir / "config.yaml"),
            "model_dir": str(self._model_dir),
            "text": text,
            "lang": lang,
            "spk_audio_prompt": spk_audio_prompt,
            "output_path": output_path,
            "use_bf16": use_bf16,
            "use_qwen_emo": use_qwen_emo,
            "emo_alpha": emo_alpha,
            "emo_audio_prompt": emo_audio_prompt,
            "duration_factor": duration_factor,
        }

        try:
            proc = subprocess.Popen(
                [str(self.python_executable), "-c", runner],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except OSError as e:
            print(f"❌ Failed to start IndexTTS environment: {e}")
            return False

        try:
            stdout, stderr = proc.communicate(
                input=json.dumps(payload), timeout=GENERATION_TIMEOUT
            )
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            print(f"❌ IndexTTS generation timed out after {GENERATION_TIMEOUT}s.")
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
            print("❌ IndexTTS generation failed.")
            return False

        if not Path(output_path).exists():
            print("❌ IndexTTS did not produce an output file.")
            return False

        print(f"IndexTTS: Speech generated successfully to {output_path}")
        return True

    @staticmethod
    def _runner_script() -> str:
        """Return the Python runner executed inside the isolated env.

        It reads a JSON payload from stdin and calls ``indextts.infer_v2_5.IndexTTS2``.
        Kept as a plain string (no f-string) so no host value is ever interpolated
        into the code — everything comes from the JSON payload at runtime.
        """
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

    cfg_path = payload["cfg_path"]
    model_dir = payload["model_dir"]
    text = payload["text"]
    lang = payload["lang"]
    spk_audio_prompt = payload.get("spk_audio_prompt")
    output_path = payload["output_path"]
    use_bf16 = bool(payload.get("use_bf16", True))
    use_qwen_emo = bool(payload.get("use_qwen_emo", False))

    infer_kwargs = {}
    if payload.get("emo_alpha") is not None:
        infer_kwargs["emo_alpha"] = float(payload["emo_alpha"])
    if payload.get("emo_audio_prompt"):
        infer_kwargs["emo_audio_prompt"] = payload["emo_audio_prompt"]
    if payload.get("duration_factor") is not None:
        infer_kwargs["duration_factor"] = float(payload["duration_factor"])

    if spk_audio_prompt and not os.path.isfile(spk_audio_prompt):
        print(f"[runner] reference audio not found: {spk_audio_prompt}", file=sys.stderr)
        sys.exit(3)

    try:
        from indextts.infer_v2_5 import IndexTTS2
    except Exception as e:
        print(f"[runner] indextts import failed: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(4)

    _log(f"loading IndexTTS-2.5 (model_dir={model_dir}, bf16={use_bf16})")
    try:
        tts = IndexTTS2(
            cfg_path=cfg_path,
            model_dir=model_dir,
            use_bf16=use_bf16,
            use_qwen_emo=use_qwen_emo,
        )
    except Exception as e:
        print(f"[runner] model load failed: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(5)

    # IndexTTS requires a speaker reference for zero-shot cloning. If none was
    # supplied, use the bundled example prompt (downloaded on first WebUI run).
    if not spk_audio_prompt:
        examples = [
            os.path.join(model_dir, "..", "examples", "voice_01.wav"),
            os.path.join("examples", "voice_01.wav"),
        ]
        for cand in examples:
            if os.path.isfile(cand):
                spk_audio_prompt = cand
                break
        if not spk_audio_prompt:
            print("[runner] no reference audio and no bundled example voice_01.wav; "
                  "pass --voice <wav> or --voice-clone <wav>.", file=sys.stderr)
            sys.exit(6)

    _log(f"synthesizing ({len(text)} chars, lang={lang})")
    try:
        tts.infer(
            spk_audio_prompt=spk_audio_prompt,
            text=text,
            lang=lang,
            output_path=output_path,
            verbose=True,
            **infer_kwargs,
        )
    except Exception as e:
        print(f"[runner] inference failed: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(7)

    _log(f"done -> {output_path}")


if __name__ == "__main__":
    main()
'''
