#!/usr/bin/env python3
"""
Model Registry Module - TTS Model Information and Capabilities

Centralized registry of all available TTS models with their specifications,
capabilities, and implementation status.

Author: Nbiish Waabanimii-Kinawaabakizi
Date: 2025
Version: 2.1
"""

from typing import Dict, Any, List, Optional
import torch

class ModelRegistry:
    """
    Centralized registry of all available TTS models with their specifications,
    capabilities, and implementation status.
    """
    
    def __init__(self):
        self.models = {
            "f5-tts": {
                "name": "F5-TTS (SWivid)",
                "model_id": "SWivid/F5-TTS",
                "description": "High-quality speech generation with flow matching and voice cloning",
                "requirements": "Python 3.8+, PyTorch 2.0+, moderate VRAM",
                "capabilities": ["High quality", "Voice cloning", "Flow matching", "Local processing"],
                "status": "✅ Implemented",
                "voice_cloning": True,
                "voice_cloning_quality": "✅ High quality - produces good audio",
                "performance": "48.11s (Slow)",
                "platforms": ["CUDA", "MPS", "CPU"],
                "github": "https://github.com/SWivid/F5-TTS",
                "huggingface": "https://huggingface.co/SWivid/F5-TTS"
            },
            "edge-tts": {
                "name": "Edge TTS (Microsoft)",
                "model_id": "edge-tts",
                "description": "Microsoft Edge's high-quality TTS with 322+ voices across multiple languages",
                "requirements": "Internet connection, Python 3.7+",
                "capabilities": ["High quality", "Multiple voices", "Multi-language", "Fast generation"],
                "status": "✅ Implemented",
                "voice_cloning": False,
                "voice_cloning_quality": "❌ Not supported",
                "performance": "1.62s (Fastest)",
                "platforms": ["All platforms"],
                "github": None,
                "huggingface": None
            },
            "dia": {
                "name": "Dia (Nari Labs)",
                "model_id": "nari-labs/Dia-1.6B-0626",
                "description": "Ultra-realistic dialogue generation in one pass with voice cloning (FIXED - now optimized)",
                "requirements": "Python 3.8+, PyTorch 2.0+, transformers main branch",
                "capabilities": ["Dialogue generation", "Voice cloning", "Emotion control", "Non-verbal sounds"],
                "status": "✅ Implemented (Optimized)",
                "voice_cloning": True,
                "voice_cloning_quality": "⚠️ Poor quality - produces bad audio",
                "performance": "51.31s (Much Improved)",
                "platforms": ["CUDA", "MPS", "CPU"],
                "github": "https://github.com/nari-labs/dia",
                "huggingface": "https://huggingface.co/nari-labs/Dia-1.6B-0626"
            },
            "kyutai": {
                "name": "Kyutai TTS",
                "model_id": "kyutai/tts-1.6b-en_fr",
                "description": "1.6B parameters, multilingual (English/French), ultra-low latency (220ms)",
                "requirements": "Python 3.8+, moshi_mlx package, voice repository",
                "capabilities": ["Multilingual", "Ultra-low latency", "Multi-speaker", "Voice cloning"],
                "status": "✅ Implemented",
                "voice_cloning": True,
                "voice_cloning_quality": "⚠️ Poor quality - produces bad audio",
                "performance": "16.52s (Moderate)",
                "platforms": ["CUDA", "MPS", "CPU"],
                "github": "https://github.com/kyutai-labs/delayed-streams-modeling",
                "huggingface": "https://huggingface.co/kyutai/tts-1.6b-en_fr"
            },
            "kokoro": {
                "name": "Kokoro (Hexgrad)",
                "model_id": "hexgrad/Kokoro-82M",
                "description": "82M parameters, ultra-lightweight, fast processing for resource-constrained environments",
                "requirements": "Python 3.8+, kokoro package, minimal VRAM",
                "capabilities": ["Ultra-lightweight", "Fast processing", "Basic voice cloning", "Cost-effective"],
                "status": "✅ Implemented",
                "voice_cloning": True,
                "voice_cloning_quality": "⚠️ Poor quality - produces bad audio",
                "performance": "10.28s (Very Fast)",
                "platforms": ["CUDA", "MPS", "CPU"],
                "github": "https://github.com/hexgrad/kokoro",
                "huggingface": "https://huggingface.co/hexgrad/Kokoro-82M"
            },
            "vibevoice": {
                "name": "VibeVoice (Microsoft)",
                "model_id": "microsoft/VibeVoice-1.5B",
                "description": "1.5B parameters, long-form conversational TTS, multi-speaker support (up to 4 speakers)",
                "requirements": "Python 3.8+, PyTorch 2.0+, transformers library",
                "capabilities": ["Long-form generation", "Multi-speaker", "Natural dialogue", "Podcast-ready"],
                "status": "❌ Apple Silicon compatibility issues",
                "voice_cloning": True,
                "voice_cloning_quality": "❓ Unknown - not tested due to compatibility issues",
                "performance": "6.47s (Broken)",
                "platforms": ["CUDA", "CPU"],
                "github": "https://github.com/microsoft/VibeVoice",
                "huggingface": "https://huggingface.co/microsoft/VibeVoice-1.5B"
            }
        }
        
        self.current_model = None
        self.device = self._get_device()
    
    def _get_device(self) -> str:
        """Get the best available device for TTS generation."""
        if torch.cuda.is_available():
            device = "cuda"
        elif torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"
        
        return device
    
    def list_models(self) -> List[str]:
        """List available model keys."""
        return list(self.models.keys())
    
    def get_model_info(self, model_key: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model."""
        return self.models.get(model_key)
    
    def get_models_by_capability(self, capability: str) -> List[str]:
        """Get models that support a specific capability."""
        return [
            model_key for model_key, model_info in self.models.items()
            if capability in model_info.get("capabilities", [])
        ]
    
    def get_models_by_platform(self, platform: str) -> List[str]:
        """Get models that support a specific platform."""
        return [
            model_key for model_key, model_info in self.models.items()
            if platform in model_info.get("platforms", [])
        ]
    
    def get_voice_cloning_models(self) -> List[str]:
        """Get models that support voice cloning."""
        return [
            model_key for model_key, model_info in self.models.items()
            if model_info.get("voice_cloning", False)
        ]
    
    def get_device_compatible_models(self) -> List[str]:
        """Get models compatible with the current device."""
        return self.get_models_by_platform(self.device)
    
    def get_model_status_summary(self) -> Dict[str, Any]:
        """Get a summary of all model statuses."""
        total_models = len(self.models)
        implemented_models = len([m for m in self.models.values() if m["status"] == "✅ Implemented"])
        voice_cloning_models = len(self.get_voice_cloning_models())
        device_compatible_models = len(self.get_device_compatible_models())
        
        return {
            "total_models": total_models,
            "implemented_models": implemented_models,
            "voice_cloning_models": voice_cloning_models,
            "device_compatible_models": device_compatible_models,
            "current_device": self.device.upper(),
            "implementation_rate": f"{(implemented_models/total_models)*100:.1f}%"
        }
    
    def search_models(self, query: str) -> List[str]:
        """Search models by name, description, or capabilities."""
        query_lower = query.lower()
        matching_models = []
        
        for model_key, model_info in self.models.items():
            # Search in name
            if query_lower in model_info["name"].lower():
                matching_models.append(model_key)
                continue
            
            # Search in description
            if query_lower in model_info["description"].lower():
                matching_models.append(model_key)
                continue
            
            # Search in capabilities
            if any(query_lower in cap.lower() for cap in model_info["capabilities"]):
                matching_models.append(model_key)
                continue
        
        return matching_models
    
    def get_model_comparison(self, model_keys: List[str]) -> Dict[str, Any]:
        """Get a detailed comparison of specified models."""
        comparison = {}
        
        for model_key in model_keys:
            if model_key in self.models:
                model_info = self.models[model_key]
                comparison[model_key] = {
                    "name": model_info["name"],
                    "description": model_info["description"],
                    "capabilities": model_info["capabilities"],
                    "voice_cloning": model_info["voice_cloning"],
                    "platforms": model_info["platforms"],
                    "status": model_info["status"]
                }
        
        return comparison
