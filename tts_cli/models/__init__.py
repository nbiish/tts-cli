"""TTS Model implementations.

Each model is an Atom that can be composed into higher-level functionality.

Single engine (cold-start, one-shot; no daemon, no model state held between calls):
  - ``KittenTTSModel``: KittenTTS nano int8 (15M) — ultra-lightweight CPU ONNX TTS
    with fixed built-in voices. The fastest engine on this machine (cold ~7.9s,
    RTF ~0.47) and the most portable (CPU-only, no accelerator, cross-platform).
    Selected by ``kitten-tts-nano`` / ``auto``.
"""

from .kitten_tts_model import KittenTTSModel

__all__ = [
    "KittenTTSModel",
]
