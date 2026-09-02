"""TTS Model implementations.

Each model is an Atom that can be composed into higher-level functionality.

Engines (cold-start, one-shot; no daemon, no model state held between calls):
  - ``KittenTTSModel``: KittenTTS nano int8 (15M) — ultra-lightweight CPU ONNX TTS
    with fixed built-in voices. Primary default engine (``auto`` resolves to it;
    fastest cold load, RTF ~0.47).
  - ``MossTTSModel``: MOSS-TTS-Nano (100M+20M) — 48 kHz stereo zero-shot voice cloning
    and speech synthesis ONNX CPU model. Secondary, opt-in cloning engine.
"""

from .kitten_tts_model import KittenTTSModel
from .moss_tts_model import MossTTSModel

__all__ = [
    "KittenTTSModel",
    "MossTTSModel",
]
