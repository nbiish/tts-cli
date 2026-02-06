"""
Voice Manager - Voice listing and validation system.

This module manages voice information for TTS models including listing,
validation, and metadata management following the tiered composition architecture.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class VoiceInfo:
    """Voice information data class."""
    name: str
    language: str
    gender: str
    description: str
    model: str
    is_available: bool = True


class VoiceManager:
    """Manages voice information for TTS models."""
    
    def __init__(self, voice_library_path: Path = Path(".voice-library")):
        self.voice_library_path = voice_library_path
        self.voice_library_path.mkdir(exist_ok=True)
        self._voice_cache: Dict[str, List[VoiceInfo]] = {}
        self._load_voice_library()
    
    def _load_voice_library(self) -> None:
        """Load voice library from disk."""
        library_file = self.voice_library_path / "voices.json"
        if library_file.exists():
            try:
                with open(library_file, 'r') as f:
                    data = json.load(f)
                    for model, voices in data.items():
                        self._voice_cache[model] = [
                            VoiceInfo(**voice) for voice in voices
                        ]
            except (json.JSONDecodeError, FileNotFoundError):
                pass
    
    def _save_voice_library(self) -> None:
        """Save voice library to disk."""
        library_file = self.voice_library_path / "voices.json"
        data = {}
        for model, voices in self._voice_cache.items():
            data[model] = [voice.__dict__ for voice in voices]
        
        with open(library_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_voice(self, model: str, voice: VoiceInfo) -> None:
        """Add a voice to the library."""
        if model not in self._voice_cache:
            self._voice_cache[model] = []
        
        # Check if voice already exists
        existing_voices = [v for v in self._voice_cache[model] if v.name == voice.name]
        if not existing_voices:
            self._voice_cache[model].append(voice)
            self._save_voice_library()
    
    def get_voices(self, model: str) -> List[VoiceInfo]:
        """Get all voices for a model."""
        return self._voice_cache.get(model, [])
    
    def get_voice(self, model: str, voice_name: str) -> Optional[VoiceInfo]:
        """Get a specific voice by name."""
        voices = self.get_voices(model)
        for voice in voices:
            if voice.name == voice_name:
                return voice
        return None
    
    def validate_voice(self, model: str, voice_name: str) -> bool:
        """Validate if a voice exists and is available."""
        voice = self.get_voice(model, voice_name)
        return voice is not None and voice.is_available
    
    def list_voices(self, model: str) -> List[str]:
        """List voice names for a model."""
        voices = self.get_voices(model)
        return [voice.name for voice in voices if voice.is_available]
    
    def get_voice_info(self, model: str, voice_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed voice information."""
        voice = self.get_voice(model, voice_name)
        if voice:
            return voice.__dict__
        return None
    
    def search_voices(self, model: str, language: Optional[str] = None, 
                     gender: Optional[str] = None) -> List[VoiceInfo]:
        """Search voices by criteria."""
        voices = self.get_voices(model)
        
        if language:
            voices = [v for v in voices if v.language.lower() == language.lower()]
        
        if gender:
            voices = [v for v in voices if v.gender.lower() == gender.lower()]
        
        return voices
    
    def update_voice_availability(self, model: str, voice_name: str, 
                                is_available: bool) -> bool:
        """Update voice availability status."""
        voice = self.get_voice(model, voice_name)
        if voice:
            voice.is_available = is_available
            self._save_voice_library()
            return True
        return False
    
    def remove_voice(self, model: str, voice_name: str) -> bool:
        """Remove a voice from the library."""
        if model in self._voice_cache:
            original_count = len(self._voice_cache[model])
            self._voice_cache[model] = [
                v for v in self._voice_cache[model] if v.name != voice_name
            ]
            if len(self._voice_cache[model]) < original_count:
                self._save_voice_library()
                return True
        return False
    
    def get_voice_statistics(self, model: str) -> Dict[str, Any]:
        """Get voice statistics for a model."""
        voices = self.get_voices(model)
        if not voices:
            return {"total": 0, "available": 0, "languages": 0, "genders": 0}
        
        available = sum(1 for v in voices if v.is_available)
        languages = len(set(v.language for v in voices))
        genders = len(set(v.gender for v in voices))
        
        return {
            "total": len(voices),
            "available": available,
            "languages": languages,
            "genders": genders
        }


# Global voice manager instance
voice_manager = VoiceManager()
