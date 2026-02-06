"""
Model Registry - Dynamic model loading and registration system.

This module provides a registry system for managing TTS models with dynamic loading
and registration capabilities following the tiered composition architecture.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Type, Any
import importlib
import sys
from pathlib import Path


class BaseTTSModel(ABC):
    """Base class for all TTS models following the Atom pattern."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.is_available = False
        self.environment_path: Optional[Path] = None
    
    @abstractmethod
    def generate_speech(self, text: str, voice: Optional[str] = None, 
                       output_path: str = "output.wav", **kwargs) -> bool:
        """Generate speech from text using the TTS model."""
        pass
    
    @abstractmethod
    def list_voices(self) -> List[str]:
        """List available voices for this model."""
        pass
    
    @abstractmethod
    def validate_voice(self, voice: str) -> bool:
        """Validate if a voice is available for this model."""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and capabilities."""
        pass
    
    def check_availability(self) -> bool:
        """Check if the model is available and properly configured."""
        return self.is_available


class ModelRegistry:
    """Registry for managing TTS models following the Molecule pattern."""
    
    def __init__(self):
        self._models: Dict[str, Type[BaseTTSModel]] = {}
        self._instances: Dict[str, BaseTTSModel] = {}
    
    def register_model(self, name: str, model_class: Type[BaseTTSModel]) -> None:
        """Register a TTS model class."""
        self._models[name] = model_class
    
    def get_model(self, name: str) -> Optional[BaseTTSModel]:
        """Get a model instance by name."""
        if name not in self._instances:
            if name in self._models:
                self._instances[name] = self._models[name](name)
            else:
                return None
        return self._instances[name]
    
    def list_models(self) -> List[str]:
        """List all registered model names."""
        return list(self._models.keys())
    
    def get_available_models(self) -> List[str]:
        """Get list of models that are currently available."""
        available = []
        for name in self._models:
            model = self.get_model(name)
            if model and model.check_availability():
                available.append(name)
        return available
    
    def load_model_dynamically(self, model_name: str) -> bool:
        """Dynamically load a model from its module."""
        try:
            module_name = f"tts_cli.models.{model_name.replace('-', '_')}_model"
            module = importlib.import_module(module_name)
            
            # Look for a model class (convention: {ModelName}Model)
            class_name = f"{model_name.replace('-', '_').title().replace('_', '')}Model"
            
            if hasattr(module, class_name):
                model_class = getattr(module, class_name)
                self.register_model(model_name, model_class)
                return True
            else:
                print(f"Class {class_name} not found in module {module_name}")
                return False
        except (ImportError, AttributeError) as e:
            print(f"Failed to load model {model_name}: {e}")
            return False
    
    def register_all_models(self) -> None:
        """Register all available TTS models."""
        models = [
            "pocket-tts"
        ]
        
        for model_name in models:
            self.load_model_dynamically(model_name)


# Global registry instance
model_registry = ModelRegistry()
