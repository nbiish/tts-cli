"""
TTS Model implementations.

This module contains implementations of TTS models following the
tiered composition architecture. Each model is implemented as an Atom
that can be composed into higher-level functionality.
"""

from .index_tts_model import IndexTTSModel

__all__ = [
    "IndexTTSModel",
]
