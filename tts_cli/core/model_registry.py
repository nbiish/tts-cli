#!/usr/bin/env python3
"""
TTS Model Registry.

This module provides a centralized registry for all TTS models,
managing their availability, capabilities, and implementations.
"""

from typing import Dict, List, Optional, Any
from rich.console import Console
from rich.table import Table
from .environment_manager import MultiEnvironmentManager

# Initialize console
console = Console()

class TTSModelRegistry:
    """
    Centralized registry for all TTS models.
    
    This class manages model registration, availability checking,
    and provides a unified interface for all TTS operations.
    """
    
    def __init__(self):
        """Initialize the model registry."""
        self.models = {}
        self.environment_manager = MultiEnvironmentManager()
        self._register_models()
    
    def _register_models(self):
        """Register all available TTS models."""
        # Working models (confirmed to work)
        self._register_working_models()
        
        # Models pending testing
        self._register_pending_models()
    
    def _register_working_models(self):
        """Register models that are confirmed to work."""
        working_models = {
            "f5-tts": {
                "name": "F5-TTS (SWivid)",
                "description": "F5-TTS with voice cloning capabilities",
                "status": "✅ Ready",
                "voice_cloning": True,
                "platforms": ["mps", "cuda", "cpu"],
                "notes": "High-quality voice cloning, local processing"
            },
            "edge-tts": {
                "name": "Edge TTS (Microsoft)",
                "description": "Microsoft Edge TTS with 322+ voices",
                "status": "✅ Ready",
                "voice_cloning": False,
                "platforms": ["mps", "cuda", "cpu"],
                "notes": "High-quality speech, multiple voice options"
            },
            "dia": {
                "name": "Dia (Nari Labs)",
                "description": "Dialogue generation with speaker tags and non-verbal expressions",
                "status": "✅ Ready",
                "voice_cloning": True,
                "platforms": ["mps", "cuda", "cpu"],
                "notes": "Multi-speaker dialogue, emotion control"
            },
            "kyutai": {
                "name": "Kyutai TTS",
                "description": "Multilingual TTS with ultra-low latency",
                "status": "✅ Ready",
                "voice_cloning": True,
                "platforms": ["mps", "cuda", "cpu"],
                "notes": "220ms end-to-end latency, VCTK voices"
            },
            "kokoro": {
                "name": "Kokoro TTS (Hexgrad)",
                "description": "Ultra-lightweight TTS for resource-constrained environments",
                "status": "✅ Ready",
                "voice_cloning": True,
                "platforms": ["mps", "cuda", "cpu"],
                "notes": "82M parameters, fast processing"
            },
            "higgs-audio-v2": {
                "name": "Higgs Audio v2 (Boson AI)",
                "description": "DualFFN architecture, voice cloning, prosody control",
                "status": "✅ Ready",
                "voice_cloning": True,
                "platforms": ["mps", "cuda", "cpu"],
                "notes": "Cross-platform compatible with automatic device detection"
            }
        }
        
        for model_key, info in working_models.items():
            self.models[model_key] = {
                **info,
                "environment_ready": self.environment_manager.environment_exists(model_key),
                "implementation_status": "ready"
            }
    
    def _register_pending_models(self):
        """Register models that are pending testing or implementation."""
        pending_models = {
            "vibevoice": {
                "name": "VibeVoice (Microsoft)",
                "description": "Long-form conversations, multi-speaker, podcast-ready",
                "status": "🔄 Pending Testing",
                "voice_cloning": True,
                "platforms": ["mps", "cuda", "cpu"],
                "notes": "Package not available on PyPI"
            }
        }
        
        for model_key, info in pending_models.items():
            self.models[model_key] = {
                **info,
                "environment_ready": self.environment_manager.environment_exists(model_key),
                "implementation_status": "pending"
            }
    
    def list_models(self) -> List[str]:
        """Get list of all available model keys."""
        return list(self.models.keys())
    
    def get_model_info(self, model_key: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model."""
        if model_key not in self.models:
            return None
        
        model_info = self.models[model_key].copy()
        
        # Add environment status
        if model_key in self.environment_manager.environments:
            env_status = self.environment_manager.list_environments().get(model_key, {})
            model_info["environment"] = env_status
        
        return model_info
    
    def get_working_models(self) -> List[str]:
        """Get list of models that are confirmed to work."""
        return [
            key for key, info in self.models.items()
            if info["status"] == "✅ Ready"
        ]
    
    def get_pending_models(self) -> List[str]:
        """Get list of models pending testing or implementation."""
        return [
            key for key, info in self.models.items()
            if info["status"] != "✅ Ready"
        ]
    
    def get_models_by_capability(self, capability: str) -> List[str]:
        """Get models that support a specific capability."""
        if capability == "voice_cloning":
            return [
                key for key, info in self.models.items()
                if info.get("voice_cloning", False)
            ]
        elif capability == "platform":
            return [
                key for key, info in self.models.items()
                if info.get("platforms", [])
            ]
        return []
    
    def show_models_table(self) -> None:
        """Display a formatted table of all models."""
        table = Table(title="TTS Models Status")
        
        # Add columns
        table.add_column("Model", style="cyan", no_wrap=True)
        table.add_column("Status", style="bold")
        table.add_column("Description", style="white")
        table.add_column("Voice Cloning", style="green")
        table.add_column("Platforms", style="blue")
        table.add_column("Environment", style="yellow")
        
        # Add rows
        for model_key, info in self.models.items():
            status_style = {
                "✅ Ready": "green",
                "⚠️ Platform Limited": "yellow",
                "🔄 Pending Testing": "blue"
            }.get(info["status"], "white")
            
            voice_cloning = "✅" if info.get("voice_cloning", False) else "❌"
            platforms = ", ".join(info.get("platforms", []))
            environment = "✅ Ready" if info.get("environment_ready", False) else "❌ Not Created"
            
            table.add_row(
                info["name"],
                f"[{status_style}]{info['status']}[/{status_style}]",
                info["description"],
                voice_cloning,
                platforms,
                environment
            )
        
        console.print(table)
    
    def get_model_summary(self) -> Dict[str, Any]:
        """Get a summary of all models."""
        total_models = len(self.models)
        working_models = len(self.get_working_models())
        pending_models = len(self.get_pending_models())
        voice_cloning_models = len(self.get_models_by_capability("voice_cloning"))
        
        return {
            "total_models": total_models,
            "working_models": working_models,
            "pending_models": pending_models,
            "voice_cloning_models": voice_cloning_models,
            "success_rate": f"{(working_models / total_models * 100):.1f}%" if total_models > 0 else "0%"
        }
    
    def update_model_status(self, model_key: str, **updates) -> bool:
        """Update model information."""
        if model_key not in self.models:
            return False
        
        self.models[model_key].update(updates)
        return True
    
    def refresh_environment_status(self) -> None:
        """Refresh environment status for all models."""
        env_statuses = self.environment_manager.list_environments()
        
        for model_key in self.models:
            if model_key in env_statuses:
                self.models[model_key]["environment_ready"] = env_statuses[model_key]["exists"]
    
    def __str__(self) -> str:
        """String representation of the registry."""
        summary = self.get_model_summary()
        return f"TTSModelRegistry({summary['working_models']}/{summary['total_models']} models working)"
    
    def __repr__(self) -> str:
        """Detailed string representation of the registry."""
        return f"{self.__class__.__name__}(models={len(self.models)})"
