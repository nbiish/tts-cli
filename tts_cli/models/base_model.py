#!/usr/bin/env python3
"""
Base Model Interface - TTS Model Implementation Contract

Defines the interface that all TTS models must implement to ensure
consistent behavior and integration with the CLI system.

Author: Nbiish Waabanimii-Kinawaabakizi
Date: 2025
Version: 2.1
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pathlib import Path
import numpy as np

class BaseTTSModel(ABC):
    """
    Abstract base class for all TTS model implementations.
    
    This class defines the contract that all TTS models must follow
    to ensure consistent integration with the CLI system.
    """
    
    def __init__(self, model_key: str, model_info: Dict[str, Any]):
        """
        Initialize the base TTS model.
        
        Args:
            model_key: Unique identifier for the model
            model_info: Model information from the registry
        """
        self.model_key = model_key
        self.model_info = model_info
        self.is_loaded = False
        self.device = None
        self.model = None
        self.tokenizer = None
    
    @abstractmethod
    def load_model(self) -> bool:
        """
        Load the TTS model into memory.
        
        Returns:
            True if model loaded successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def generate_speech(self, text: str, voice_clone_path: Optional[str] = None, **kwargs) -> Optional[np.ndarray]:
        """
        Generate speech from text input.
        
        Args:
            text: Text to convert to speech
            voice_clone_path: Optional path to reference audio for voice cloning
            **kwargs: Additional model-specific parameters
            
        Returns:
            Audio data as numpy array, or None if generation failed
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported audio output formats.
        
        Returns:
            List of supported format strings (e.g., ['wav', 'mp3'])
        """
        pass
    
    @abstractmethod
    def get_model_requirements(self) -> Dict[str, Any]:
        """
        Get model requirements and capabilities.
        
        Returns:
            Dictionary containing model requirements, capabilities, and limitations
        """
        pass
    
    def is_voice_cloning_supported(self) -> bool:
        """
        Check if this model supports voice cloning.
        
        Returns:
            True if voice cloning is supported, False otherwise
        """
        return self.model_info.get("voice_cloning", False)
    
    def get_model_name(self) -> str:
        """
        Get the human-readable name of the model.
        
        Returns:
            Model name string
        """
        return self.model_info.get("name", self.model_key)
    
    def get_model_description(self) -> str:
        """
        Get the model description.
        
        Returns:
            Model description string
        """
        return self.model_info.get("description", "")
    
    def get_model_status(self) -> str:
        """
        Get the current status of the model.
        
        Returns:
            Model status string
        """
        return self.model_info.get("status", "Unknown")
    
    def is_platform_compatible(self, platform: str) -> bool:
        """
        Check if the model is compatible with a specific platform.
        
        Args:
            platform: Platform identifier (e.g., 'CUDA', 'MPS', 'CPU')
            
        Returns:
            True if platform is supported, False otherwise
        """
        supported_platforms = self.model_info.get("platforms", [])
        return platform in supported_platforms
    
    def validate_input(self, text: str) -> bool:
        """
        Validate input text for the model.
        
        Args:
            text: Text to validate
            
        Returns:
            True if text is valid, False otherwise
        """
        if not text or not text.strip():
            return False
        
        # Basic validation - can be overridden by subclasses
        return True
    
    def validate_voice_clone_file(self, voice_clone_path: str) -> bool:
        """
        Validate voice cloning reference file.
        
        Args:
            voice_clone_path: Path to reference audio file
            
        Returns:
            True if file is valid, False otherwise
        """
        if not voice_clone_path:
            return False
        
        file_path = Path(voice_clone_path)
        if not file_path.exists():
            return False
        
        # Check if it's an audio file
        audio_extensions = {'.wav', '.mp3', '.flac', '.m4a', '.ogg'}
        return file_path.suffix.lower() in audio_extensions
    
    def get_generation_parameters(self) -> Dict[str, Any]:
        """
        Get default generation parameters for the model.
        
        Returns:
            Dictionary of default parameters
        """
        return {
            "sample_rate": 22050,
            "format": "wav",
            "quality": "high"
        }
    
    def cleanup(self) -> None:
        """
        Clean up model resources.
        
        This method should be called when the model is no longer needed
        to free up memory and resources.
        """
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
    
    def get_error_message(self, error: Exception) -> str:
        """
        Get a user-friendly error message for a given exception.
        
        Args:
            error: The exception that occurred
            
        Returns:
            User-friendly error message
        """
        error_type = type(error).__name__
        error_msg = str(error)
        
        # Common error patterns and their user-friendly messages
        if "CUDA" in error_msg and "MPS" in str(self.device):
            return f"Model {self.get_model_name()} requires CUDA GPU but you're using Apple Silicon (MPS). Try using a different model or cloud compute."
        elif "out of memory" in error_msg.lower():
            return f"Model {self.get_model_name()} ran out of memory. Try using a smaller model or reducing input length."
        elif "not found" in error_msg.lower():
            return f"Model files for {self.get_model_name()} not found. Please check your installation."
        else:
            return f"Error with {self.get_model_name()}: {error_msg}"
    
    def __str__(self) -> str:
        """String representation of the model."""
        return f"{self.__class__.__name__}({self.model_key})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the model."""
        return f"{self.__class__.__name__}(model_key='{self.model_key}', loaded={self.is_loaded})"
