"""
Hybrid TTS model implementation with automatic fallback.

This module provides a hybrid TTS system that uses KittenTTS by default
and automatically falls back to PocketTTS when needed.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger("tts_cli.hybrid")

from ..core.model_registry import BaseTTSModel
from .kitten_tts_model import KittenTTSModel
from .pocket_tts_model import PocketTTSModel


class HybridTTSModel(BaseTTSModel):
    """Hybrid TTS model with automatic fallback from KittenTTS to PocketTTS."""

    # Configuration
    KITTENTTS_MAX_LENGTH = 350  # characters (tested limit: ~420, using 350 for safety)
    POCKETTTS_MAX_LENGTH = 5000  # characters

    # Fallback reason messages
    FALLBACK_MESSAGES = {
        "text_too_long": "Text too long for KittenTTS ({chars} chars), using PocketTTS instead...",
        "voice_cloning": "Voice cloning requested, using PocketTTS...",
        "custom_voice": "Custom voice detected, using PocketTTS...",
        "kitten_failed": "KittenTTS generation failed ({reason}), falling back to PocketTTS...",
        "kitten_unavailable": "KittenTTS unavailable, using PocketTTS...",
        "espeak_missing": "espeak-ng not found, using PocketTTS...",
        "timeout": "KittenTTS timeout, falling back to PocketTTS...",
        "unknown_error": "KittenTTS error, falling back to PocketTTS...",
    }

    def __init__(self, model_name: str = "hybrid-tts"):
        super().__init__(model_name)
        self.kitten_model = KittenTTSModel()
        self.pocket_model = PocketTTSModel()
        self.is_available = True  # Always available (has fallback)

    def generate_speech(self, text: str, voice: Optional[str] = None,
                       output_path: str = "output.wav", **kwargs) -> bool:
        """Generate speech using KittenTTS with automatic PocketTTS fallback."""

        # Check for voice cloning (direct to PocketTTS)
        voice_clone = kwargs.get('voice_clone')
        if voice_clone:
            return self._use_pocket_tts(text, voice_clone, output_path,
                                        "voice_cloning", **kwargs)

        # Check if voice is a custom voice file
        if voice and Path(voice).exists():
            return self._use_pocket_tts(text, voice, output_path,
                                        "custom_voice", **kwargs)

        # Check text length
        if len(text) > self.KITTENTTS_MAX_LENGTH:
            return self._use_pocket_tts(text, voice, output_path,
                                        "text_too_long",
                                        chars=len(text), **kwargs)

        # Try KittenTTS first
        logger.info(f"[HYBRID] Attempting KittenTTS for text ({len(text)} chars)")

        # Check if voice is valid for KittenTTS
        if voice and not self.kitten_model.validate_voice(voice):
            # Voice not available in KittenTTS, use PocketTTS
            logger.info(f"[HYBRID] Voice '{voice}' not in KittenTTS, using PocketTTS")
            return self._use_pocket_tts(text, voice, output_path,
                                        "unknown_error", **kwargs)

        # Attempt KittenTTS generation
        try:
            success = self.kitten_model.generate_speech(text, voice, output_path, **kwargs)
            if success:
                logger.info(f"[HYBRID] KittenTTS generation successful")
                return True
        except Exception as e:
            logger.warning(f"[HYBRID] KittenTTS generation failed: {e}")

        # KittenTTS failed, fall back to PocketTTS
        reason = self._determine_fallback_reason()
        return self._use_pocket_tts(text, voice, output_path, reason, **kwargs)

    def _use_pocket_tts(self, text: str, voice: Optional[str], output_path: str,
                        fallback_reason: str, **kwargs) -> bool:
        """Use PocketTTS with appropriate message."""
        # Format and log fallback message
        message_kwargs = {}
        if fallback_reason == "text_too_long":
            message_kwargs = {"chars": len(text)}

        message = self.FALLBACK_MESSAGES.get(fallback_reason,
                                            self.FALLBACK_MESSAGES["unknown_error"])

        if message_kwargs:
            message = message.format(**message_kwargs)

        logger.info(f"[HYBRID] {message}")
        print(f"ℹ️  {message}")

        # Use PocketTTS
        try:
            success = self.pocket_model.generate_speech(text, voice, output_path, **kwargs)
            if success:
                logger.info(f"[HYBRID] PocketTTS generation successful")
            return success
        except Exception as e:
            logger.error(f"[HYBRID] PocketTTS also failed: {e}")
            return False

    def _determine_fallback_reason(self) -> str:
        """Determine the reason for KittenTTS fallback."""
        # Check if KittenTTS is available
        if not self.kitten_model.is_available:
            return "kitten_unavailable"

        # Check if espeak is available
        if not self.kitten_model._espeak_available:
            return "espeak_missing"

        # Default to generic failure
        return "kitten_failed"

    def list_voices(self) -> List[str]:
        """List all available voices from both models."""
        voices = []

        # Add KittenTTS voices
        voices.extend([f"kitten:{v}" for v in self.kitten_model.list_voices()])

        # Add PocketTTS voices
        voices.extend([f"pocket:{v}" for v in self.pocket_model.list_voices()])

        # Add PocketTTS voices without prefix (for compatibility)
        voices.extend(self.pocket_model.list_voices())

        return voices

    def validate_voice(self, voice: str) -> bool:
        """Validate if a voice is available (either model)."""
        # Check if it's a file path
        if Path(voice).exists():
            return True

        # Check KittenTTS voices
        if self.kitten_model.validate_voice(voice):
            return True

        # Check PocketTTS voices
        if self.pocket_model.validate_voice(voice):
            return True

        return False

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and capabilities."""
        return {
            "name": "hybrid-tts",
            "description": "Hybrid TTS system with KittenTTS default and PocketTTS fallback",
            "capabilities": ["text-to-speech", "voice-cloning", "fast-inference",
                           "automatic-fallback", "cpu-optimized"],
            "languages": ["en"],
            "primary_model": "kitten-tts",
            "fallback_model": "pocket-tts",
            "kitten_voices": len(self.kitten_model.list_voices()),
            "pocket_voices": len(self.pocket_model.list_voices()),
            "max_text_length": self.POCKETTTS_MAX_LENGTH,
            "kitten_max_length": self.KITTENTTS_MAX_LENGTH,
            "version": "1.0.0"
        }

    def get_fallback_stats(self) -> Dict[str, Any]:
        """Get statistics about fallback usage."""
        # This could be expanded to track actual statistics
        return {
            "kitten_available": self.kitten_model.is_available,
            "pocket_available": self.pocket_model.is_available,
            "espeak_available": self.kitten_model._espeak_available,
            "kitten_voices": self.kitten_model.list_voices(),
            "pocket_voices": self.pocket_model.list_voices(),
        }
