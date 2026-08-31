"""TTS Model implementations.

Each model is an Atom that can be composed into higher-level functionality.

Engine tiers (cold-start, one-shot; no daemon, no model state held between calls):
  - ``PocketTTSModel``: the fast default — Kyutai PocketTTS, zero-shot voice
    cloning, cross-platform CPU (+ MPS/CUDA). Selected by ``pocket-tts`` / ``auto``.
  - ``IndexTTSGGUFModel``: IndexTTS-2.5 Q8 GGUF via audio.cpp (Metal/CUDA/Vulkan/CPU).
    Explicit ``--model index-tts``.
  - ``IndexTTSModel``: full-precision Python IndexTTS-2.5 (MPS/CUDA), the
    highest-quality tier. Selected by ``--quality`` (or ``--model index-tts-quality``).
"""

from .pocket_tts_model import PocketTTSModel
from .index_tts_gguf_model import IndexTTSGGUFModel
from .index_tts_model import IndexTTSModel

__all__ = [
    "PocketTTSModel",
    "IndexTTSGGUFModel",
    "IndexTTSModel",
]
