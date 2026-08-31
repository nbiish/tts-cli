"""
IndexTTS-2.5 GGUF model implementation for TTS CLI.

This is the **fast default** engine: IndexTTS-2.5 quantized to Q8 and run through
``audiocpp_cli`` (audio.cpp, a pure-C++ ggml runtime). It is **system-agnostic**:
audio.cpp supports ``metal`` (macOS), ``cuda``/``hip`` (NVIDIA/AMD on
Linux/Windows), ``vulkan`` (cross-platform GPU), and ``cpu`` (everywhere). The
adapter auto-detects the best available backend on the host (override with the
``AUDIOCPP_BACKEND`` env var) and passes it to ``audiocpp_cli``.

It is selected via ``--model index-tts`` (the default) or ``--model auto``
(an alias). The full-precision Python IndexTTS-2.5 path is available via
``--model index-tts --quality`` for higher-quality output at the cost of speed.

Both engines run one-shot in a subprocess that exits immediately after writing the
output WAV — no daemon, no warm cache, and no model state held in RAM/VRAM
between calls. Every invocation is a cold start; the process releases all memory
on exit.

Benchmark on Apple Silicon (same 155-char prompt, same reference voice):
  - GGUF Q8 via audio.cpp (Metal):  ~43s  cold, RTF ~5.1  (default, fast)
  - Python IndexTTS-2.5 (MPS):     ~142s cold, RTF ~17.2 (--quality, full dtype)

All user input is passed as discrete argv elements to ``subprocess.run`` with
``shell=False`` (CWE-78 safe — no shell interpolation). Text is passed via
``--text``; for very long inputs the caller chunks first (the CLI already splits
long text upstream).
"""

import os
import shutil
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger("tts_cli.index_tts_gguf")

from ..core.model_registry import BaseTTSModel

# Languages supported by IndexTTS-2.5 (audio.cpp uses lowercase codes).
SUPPORTED_LANGS = ("ZH", "EN", "JA", "ES", "AR")
DEFAULT_LANG = "EN"

# Soft text length limit. audio.cpp enforces its own; keep a sane upper bound.
MAX_TEXT_LENGTH = 5000

# Subprocess hard timeout (seconds). Cold load + Metal kernel compile + inference
# can take a minute on first run; allow generous headroom.
GENERATION_TIMEOUT = 240


class IndexTTSGGUFModel(BaseTTSModel):
    """IndexTTS-2.5 GGUF (Q8) via audio.cpp — the fast default engine."""

    def __init__(self, model_name: str = "index-tts"):
        super().__init__(model_name)
        # `auto` is an alias for `index-tts`; normalize so the alias resolves the
        # same GGUF file and availability checks.
        self._env_key = "index-tts" if model_name == "auto" else model_name
        self._audiocpp = shutil.which("audiocpp_cli")
        self._gguf_path = self._resolve_gguf()
        # Cache the (relatively expensive) backend probe so repeated
        # check_availability() calls during a CLI session stay cheap.
        self._availability_cache: Optional[bool] = None
        self._backend_cache: Optional[str] = None

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_gguf() -> Optional[Path]:
        """Locate the IndexTTS-2.5 Q8 GGUF file.

        Order of precedence:
          1. ``INDEX_TTS_GGUF`` env var (absolute path to the .gguf).
          2. ``models-gguf/IndexTTS2.5-GGUF/index-tts2_5-q8_0.gguf`` at the
             project root.
        """
        env_gguf = os.environ.get("INDEX_TTS_GGUF")
        if env_gguf:
            p = Path(env_gguf).expanduser()
            if p.is_file():
                return p
            logger.warning("INDEX_TTS_GGUF=%s set but file not found", env_gguf)

        current = Path(__file__).resolve().parent
        while current != current.parent:
            if (current / "pyproject.toml").exists():
                candidate = current / "models-gguf" / "IndexTTS2.5-GGUF" / "index-tts2_5-q8_0.gguf"
                if candidate.is_file():
                    return candidate
                return None
            current = current.parent
        return None

    # Backend preference order (most capable first). audio.cpp supports all of
    # these; we pick the first one the host actually exposes via --list-devices.
    _BACKEND_PREF = ("metal", "cuda", "hip", "vulkan", "cpu")

    def _detect_backend(self) -> Optional[str]:
        """Probe audiocpp_cli for the best available backend on this host.

        ``audiocpp_cli --list-devices`` prints the backend devices. We parse it
        for the backends audio.cpp was built with, then pick the most capable one
        in preference order (metal > cuda > hip > vulkan > cpu). The model is
        NOT loaded here (keeps the probe cheap and avoids holding VRAM).

        Override: set the ``AUDIOCPP_BACKEND`` env var to force a backend
        (e.g. ``cpu`` for a portable, no-GPU fallback) — it is used verbatim if
        ``audiocpp_cli`` accepts it, else we fall back to detection.
        """
        if self._availability_cache is not None and self._backend_cache is not None:
            return self._backend_cache
        if not self._audiocpp:
            self._availability_cache = False
            self._backend_cache = None
            return None

        env_backend = os.environ.get("AUDIOCPP_BACKEND", "").strip().lower()
        try:
            proc = subprocess.run(
                [self._audiocpp, "--list-devices"],
                capture_output=True, text=True, timeout=20, check=False,
            )
            out = (proc.stdout + proc.stderr).lower()
            available = [b for b in self._BACKEND_PREF if b in out]
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            logger.debug("audiocpp device probe failed: %s", e)
            self._availability_cache = False
            self._backend_cache = None
            return None

        # Honor an explicit override if it's among what the binary exposes; else
        # fall through to auto-pick so a bad env var never silently forces CPU.
        if env_backend and (env_backend in available or env_backend == "best"):
            chosen = env_backend
        elif available:
            chosen = available[0]
        else:
            self._availability_cache = False
            self._backend_cache = None
            return None

        self._availability_cache = True
        self._backend_cache = chosen
        return chosen

    # ------------------------------------------------------------------
    # BaseTTSModel interface
    # ------------------------------------------------------------------

    def check_availability(self) -> bool:
        """Available when audiocpp_cli + the GGUF file + any usable backend are present."""
        if not self._audiocpp:
            return False
        if not self._gguf_path:
            return False
        return self._detect_backend() is not None

    def check_dependencies(self) -> tuple[bool, str]:
        """Return (ok, message) with actionable, OS-appropriate install hints."""
        if not self._audiocpp:
            return False, (
                "audiocpp_cli not found on PATH. Install audio.cpp:\n"
                "  macOS  : brew tap 0xshug0/audio-cpp && brew trust 0xshug0/audio-cpp && brew install audio-cpp\n"
                "  Linux  : build from source (see https://github.com/0xShug0/audio-cpp) with -DGGML_CUDA=ON or -DGGML_VULKAN=ON\n"
                "  Windows: build from source with CUDA/Vulkan, or use the CPU backend"
            )
        if not self._gguf_path:
            return False, (
                "IndexTTS-2.5 GGUF not found. Download the Q8 package with:\n"
                "  hf download audio-cpp/audio.cpp-gguf "
                "IndexTTS2.5-GGUF/index-tts2_5-q8_0.gguf --local-dir=models-gguf\n"
                "or set INDEX_TTS_GGUF to an existing .gguf path."
            )
        backend = self._detect_backend()
        if not backend:
            return False, (
                "No audio.cpp backend detected. Build audio.cpp with at least one "
                "of: Metal (macOS), CUDA/HIP (NVIDIA/AMD), Vulkan, or CPU. "
                "Set AUDIOCPP_BACKEND=cpu to force the portable CPU fallback."
            )
        return True, f"Dependencies OK (backend: {backend})"

    def generate_speech(self, text: str, voice: Optional[str] = None,
                        output_path: str = "output.wav", **kwargs) -> bool:
        """Generate speech from text using IndexTTS-2.5 GGUF via audio.cpp.

        ``voice`` (or ``kwargs['voice_clone']``) is the reference audio path for
        zero-shot voice cloning. When no reference is provided, audio.cpp's own
        default prompt is used.
        """
        deps_ok, deps_msg = self.check_dependencies()
        if not deps_ok:
            logger.error("IndexTTS GGUF dependencies check failed: %s", deps_msg)
            print(f"❌ {deps_msg}")
            return False

        if len(text) > MAX_TEXT_LENGTH:
            logger.warning("Text too long for IndexTTS GGUF (%d > %d)", len(text), MAX_TEXT_LENGTH)
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
            text=text, lang=lang, spk_audio_prompt=spk_audio_prompt,
            output_path=output_path,
        )

    def list_voices(self) -> List[str]:
        """IndexTTS has no fixed voice catalog — any reference WAV is a 'voice'."""
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
            "description": "IndexTTS-2.5 GGUF (Q8) via audio.cpp — fast default (auto backend: metal/cuda/vulkan/cpu)",
            "capabilities": ["text-to-speech", "voice-cloning", "multilingual",
                             "gpu-class", "quantized"],
            "languages": list(SUPPORTED_LANGS),
            "sample_rate": 22050,
            "max_text_length": MAX_TEXT_LENGTH,
            "version": "2.5-q8",
            "requires_accelerator": True,
            "requires_checkpoints": True,
            "gguf_path": str(self._gguf_path) if self._gguf_path else None,
            "quality_mode": False,
        }

    # ------------------------------------------------------------------
    # Isolated-environment execution
    # ------------------------------------------------------------------

    def _generate_in_environment(self, text: str, lang: str,
                                 spk_audio_prompt: Optional[str],
                                 output_path: str) -> bool:
        """Run IndexTTS-2.5 GGUF via audiocpp_cli in a one-shot subprocess.

        The process loads the model, synthesizes, writes the WAV, and exits —
        releasing all RAM/VRAM on exit (no daemon, no warm cache). All user
        values are discrete argv elements with ``shell=False`` (no injection).
        """
        if not self._audiocpp:
            print("❌ audiocpp_cli is not available.")
            return False

        backend = self._detect_backend()
        if not backend:
            print("❌ No audio.cpp backend available. Set AUDIOCPP_BACKEND=cpu for the portable fallback.")
            return False

        cmd = [
            self._audiocpp,
            "--task", "tts",
            "--family", "index_tts2",
            "--model", str(self._gguf_path),
            "--backend", backend,
            "--language", lang.lower(),
            "--text", text,
            "--out", output_path,
        ]
        if spk_audio_prompt:
            cmd += ["--voice-ref", spk_audio_prompt]

        try:
            logger.info("IndexTTS GGUF: invoking audiocpp_cli (cold start, exits after)")
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=GENERATION_TIMEOUT,
                check=False,
            )
        except subprocess.TimeoutExpired:
            print(f"❌ IndexTTS GGUF generation timed out after {GENERATION_TIMEOUT}s.")
            return False
        except (FileNotFoundError, OSError) as e:
            print(f"❌ Failed to start audiocpp_cli: {e}")
            return False

        if proc.stderr:
            for line in proc.stderr.splitlines():
                # audio.cpp logs progress to stderr; surface only errors/last line.
                logger.debug("audiocpp: %s", line)
        if proc.returncode != 0:
            tail = proc.stderr.strip().splitlines()[-3:] if proc.stderr else []
            print("❌ IndexTTS GGUF generation failed.")
            for line in tail:
                print(f"   {line}")
            return False

        if not Path(output_path).exists():
            print("❌ IndexTTS GGUF did not produce an output file.")
            return False

        print(f"IndexTTS GGUF: Speech generated successfully to {output_path}")
        return True
