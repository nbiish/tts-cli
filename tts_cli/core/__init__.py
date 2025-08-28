"""
Core Module - TTS CLI Core Functionality

Core components for the TTS CLI tool including environment management,
model registry, and TTS management.

Author: Nbiish Waabanimii-Kinawaabakizi
Date: 2025
Version: 2.1
"""

from .environment_manager import MultiEnvironmentManager
from .model_registry import ModelRegistry

__all__ = ["MultiEnvironmentManager", "ModelRegistry"]
