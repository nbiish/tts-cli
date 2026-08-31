"""TTS Model implementations.

Each model is an Atom that can be composed into higher-level functionality.

Engine tiers (cold-start, one-shot; no daemon, no model state held between calls):
  - ``PocketTTSModel``: Kyutai PocketTTS, zero-shot voice cloning, cross-platform
    CPU (+ MPS/CUDA). Fast default. Selected by ``pocket-tts`` / ``auto``.
  - ``KittenTTSModel``: ultra-lightweight CPU ONNX TTS, fixed built-in voices.
    Variants: ``kitten-tts-nano`` (15M int8), ``kitten-tts-mini`` (80M).
  - ``IndexTTSGGUFModel``: IndexTTS-2.5 Q8 GGUF via audio.cpp (Metal/CUDA/Vulkan/CPU).
    Explicit ``--model index-tts``.
  - ``IndexTTSModel``: full-precision Python IndexTTS-2.5 (MPS/CUDA), the
    highest-quality tier. Selected by ``--quality`` (or ``--model index-tts-quality``).
"""

from .pocket_tts_model import PocketTTSModel
from .kitten_tts_model import KittenTTSModel
from .index_tts_gguf_model import IndexTTSGGUFModel
from .index_tts_model import IndexTTSModel

__all__ = [
    "PocketTTSModel",
    "KittenTTSModel",
    "IndexTTSGGUFModel",
    "IndexTTSModel",
]
