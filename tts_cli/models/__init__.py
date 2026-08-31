"""
TTS Model implementations.

This module contains implementations of various TTS models following the
tiered composition architecture. Each model is implemented as an Atom
that can be composed into higher-level functionality.
"""

from .pocket_tts_model import PocketTTSModel
from .index_tts_model import IndexTTSModel

__all__ = [
    "PocketTTSModel",
    "IndexTTSModel",
]
