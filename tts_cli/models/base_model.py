#!/usr/bin/env python3
"""
Base TTS Model Interface.

This module defines the abstract base class that all TTS models
must implement, ensuring consistent behavior across different models.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union
import numpy as np
from pathlib import Path

class BaseTTSModel(ABC):
    """
    Abstract base class for all TTS models.
    
    This class defines the interface that all TTS models must implement,
    ensuring consistent behavior and capabilities across different models.
    """
    
    def __init__(self, model_key: str, name: str, description: str):
        """
        Initialize the base TTS model.
        
        Args:
            model_key: Unique identifier for the model
            name: Human-readable name for the model
            description: Description of the model's capabilities
        """
        self.model_key = model_key
        self.name = name
        self.description = description
        self.supports_voice_cloning = False
        self.voice_cloning_requirements = {}
        self.platform_compatibility = {
            "mps": False,  # Apple Silicon
            "cuda": False, # NVIDIA GPU
            "cpu": False   # CPU only
        }
        self.performance_characteristics = {
            "typical_generation_time": None,  # seconds
            "memory_usage": None,            # MB/GB
            "sample_rate": None,             # Hz
            "audio_quality": None            # subjective rating
        }
    
    @abstractmethod
    def generate_speech(self, text: str, voice_clone_path: Optional[str] = None, **kwargs) -> Optional[np.ndarray]:
        """
        Generate speech from text.
        
        Args:
            text: Text to convert to speech
            voice_clone_path: Optional path to reference audio for voice cloning
            **kwargs: Additional model-specific parameters
            
        Returns:
            Audio data as numpy array, or None if generation failed
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the model is available and ready to use.
        
        Returns:
            True if the model is available, False otherwise
        """
        pass
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get comprehensive information about the model.
        
        Returns:
            Dictionary containing model information
        """
        return {
            "model_key": self.model_key,
            "name": self.name,
            "description": self.description,
            "supports_voice_cloning": self.supports_voice_cloning,
            "voice_cloning_requirements": self.voice_cloning_requirements,
            "platform_compatibility": self.platform_compatibility,
            "performance_characteristics": self.performance_characteristics,
            "is_available": self.is_available()
        }
    
    def validate_voice_clone_input(self, voice_clone_path: str) -> tuple[bool, str]:
        """
        Validate voice cloning input requirements.
        
        Args:
            voice_clone_path: Path to the reference audio file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.supports_voice_cloning:
            return False, "This model does not support voice cloning"
        
        if not voice_clone_path:
            return False, "Voice clone path is required for voice cloning"
        
        path = Path(voice_clone_path)
        if not path.exists():
            return False, f"Voice clone file not found: {voice_clone_path}"
        
        # Check file format
        if path.suffix.lower() not in ['.wav', '.mp3', '.flac', '.m4a']:
            return False, f"Unsupported audio format: {path.suffix}"
        
        # Check file size (basic validation)
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > 100:  # 100MB limit
            return False, f"Voice clone file too large: {file_size_mb:.1f}MB (max 100MB)"
        
        return True, ""
    
    def get_platform_compatibility(self) -> Dict[str, bool]:
        """
        Get platform compatibility information.
        
        Returns:
            Dictionary mapping platform names to compatibility status
        """
        return self.platform_compatibility.copy()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance characteristics.
        
        Returns:
            Dictionary containing performance metrics
        """
        return self.performance_characteristics.copy()
    
    def __str__(self) -> str:
        """String representation of the model."""
        return f"{self.name} ({self.model_key})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the model."""
        return f"{self.__class__.__name__}(model_key='{self.model_key}', name='{self.name}')"
