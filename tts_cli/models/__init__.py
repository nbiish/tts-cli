"""
TTS Model implementations.

This module contains implementations of TTS models following the
tiered composition architecture. Each model is implemented as an Atom
that can be composed into higher-level functionality.

IndexTTS-2.5 is the sole engine family, exposed in two tiers:
  - ``IndexTTSGGUFModel``: the fast default (Q8 GGUF via audio.cpp on Metal).
  - ``IndexTTSModel``: the full-precision Python path (MPS), selected by --quality.
"""

from .index_tts_gguf_model import IndexTTSGGUFModel
from .index_tts_model import IndexTTSModel

__all__ = [
    "IndexTTSGGUFModel",
    "IndexTTSModel",
]
