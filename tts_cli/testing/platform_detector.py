#!/usr/bin/env python3
"""
Platform Detection Utility.

This module provides platform detection capabilities for our testing-first approach,
helping to identify hardware capabilities and platform-specific optimizations.
"""

import platform
import subprocess
from typing import Dict, List, Optional, Tuple
from rich.console import Console

# Initialize console
console = Console()

class PlatformDetector:
    """
    Detects platform capabilities and hardware for TTS model compatibility.
    
    This class provides comprehensive platform detection to help users
    understand what models will work best on their hardware.
    """
    
    def __init__(self):
        """Initialize the platform detector."""
        self.system_info = self._get_system_info()
        self.gpu_info = self._get_gpu_info()
        self.memory_info = self._get_memory_info()
        self.platform_capabilities = self._analyze_capabilities()
    
    def _get_system_info(self) -> Dict[str, str]:
        """Get basic system information."""
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation()
        }
    
    def _get_gpu_info(self) -> Dict[str, any]:
        """Get GPU information if available."""
        gpu_info = {
            "cuda_available": False,
            "mps_available": False,
            "gpu_count": 0,
            "gpu_names": [],
            "cuda_version": None
        }
        
        # Check for CUDA
        try:
            import torch
            if torch.cuda.is_available():
                gpu_info["cuda_available"] = True
                gpu_info["gpu_count"] = torch.cuda.device_count()
                gpu_info["gpu_names"] = [torch.cuda.get_device_name(i) for i in range(gpu_info["gpu_count"])]
                gpu_info["cuda_version"] = torch.version.cuda
        except ImportError:
            pass
        
        # Check for MPS (Apple Silicon)
        try:
            import torch
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                gpu_info["mps_available"] = True
        except ImportError:
            pass
        
        # Check for other GPU types
        if not gpu_info["cuda_available"] and not gpu_info["mps_available"]:
            # Try to detect other GPU types
            try:
                if platform.system() == "Darwin":  # macOS
                    # Check for Apple Silicon
                    if platform.machine() == "arm64":
                        gpu_info["mps_available"] = True
            except:
                pass
        
        return gpu_info
    
    def _get_memory_info(self) -> Dict[str, any]:
        """Get memory information."""
        memory_info = {
            "total_ram": None,
            "available_ram": None,
            "ram_units": "GB"
        }
        
        try:
            if platform.system() == "Darwin":  # macOS
                # Use system_profiler for macOS
                result = subprocess.run(
                    ["system_profiler", "SPHardwareDataType"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if "Memory:" in line:
                            memory_str = line.split(":")[1].strip()
                            if "GB" in memory_str:
                                memory_info["total_ram"] = float(memory_str.replace("GB", "").strip())
                                memory_info["ram_units"] = "GB"
                            elif "MB" in memory_str:
                                memory_info["total_ram"] = float(memory_str.replace("MB", "").strip()) / 1024
                                memory_info["ram_units"] = "GB"
                            break
            
            elif platform.system() == "Linux":
                # Use /proc/meminfo for Linux
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            kb = int(line.split()[1])
                            memory_info["total_ram"] = kb / (1024 * 1024)  # Convert to GB
                            memory_info["ram_units"] = "GB"
                            break
            
            elif platform.system() == "Windows":
                # Use wmic for Windows
                try:
                    result = subprocess.run(
                        ["wmic", "computersystem", "get", "TotalPhysicalMemory"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        if len(lines) > 1:
                            memory_str = lines[1].strip()
                            if memory_str.isdigit():
                                bytes_val = int(memory_str)
                                memory_info["total_ram"] = bytes_val / (1024 * 1024 * 1024)  # Convert to GB
                                memory_info["ram_units"] = "GB"
                except:
                    pass
                    
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not detect memory info: {e}[/yellow]")
        
        return memory_info
    
    def _analyze_capabilities(self) -> Dict[str, any]:
        """Analyze platform capabilities for TTS models."""
        capabilities = {
            "primary_platform": "cpu",
            "supported_platforms": ["cpu"],
            "recommended_models": [],
            "performance_notes": []
        }
        
        # Determine primary platform
        if self.gpu_info["cuda_available"]:
            capabilities["primary_platform"] = "cuda"
            capabilities["supported_platforms"].append("cuda")
            capabilities["performance_notes"].append("CUDA GPU available for high-performance TTS")
        
        if self.gpu_info["mps_available"]:
            capabilities["primary_platform"] = "mps"
            capabilities["supported_platforms"].append("mps")
            capabilities["performance_notes"].append("Apple Silicon MPS available for optimized TTS")
        
        # Add platform-specific recommendations
        if "cuda" in capabilities["supported_platforms"]:
            capabilities["recommended_models"].extend([
                "f5-tts", "edge-tts", "dia", "kyutai", "kokoro"
            ])
        
        if "mps" in capabilities["supported_platforms"]:
            capabilities["recommended_models"].extend([
                "f5-tts", "edge-tts", "dia", "kyutai", "kokoro"
            ])
        
        # CPU fallback recommendations
        capabilities["recommended_models"].extend([
            "edge-tts", "kyutai", "kokoro"  # Lightweight models for CPU
        ])
        
        # Remove duplicates
        capabilities["recommended_models"] = list(set(capabilities["recommended_models"]))
        
        return capabilities
    
    def get_platform_summary(self) -> Dict[str, any]:
        """Get a comprehensive platform summary."""
        return {
            "system": self.system_info,
            "gpu": self.gpu_info,
            "memory": self.memory_info,
            "capabilities": self.platform_capabilities
        }
    
    def show_platform_info(self) -> None:
        """Display platform information in a formatted way."""
        console.print("\n[bold cyan]🔍 Platform Detection Results[/bold cyan]")
        
        # System Information
        console.print("\n[bold]System Information:[/bold]")
        console.print(f"  OS: {self.system_info['system']} {self.system_info['release']}")
        console.print(f"  Architecture: {self.system_info['machine']}")
        console.print(f"  Processor: {self.system_info['processor']}")
        console.print(f"  Python: {self.system_info['python_version']} ({self.system_info['python_implementation']})")
        
        # GPU Information
        console.print("\n[bold]GPU Capabilities:[/bold]")
        if self.gpu_info["cuda_available"]:
            console.print(f"  CUDA: ✅ Available (Version: {self.gpu_info['cuda_version']})")
            console.print(f"  GPU Count: {self.gpu_info['gpu_count']}")
            for i, name in enumerate(self.gpu_info["gpu_names"]):
                console.print(f"    GPU {i}: {name}")
        else:
            console.print("  CUDA: ❌ Not Available")
        
        if self.gpu_info["mps_available"]:
            console.print("  MPS (Apple Silicon): ✅ Available")
        else:
            console.print("  MPS (Apple Silicon): ❌ Not Available")
        
        # Memory Information
        console.print("\n[bold]Memory:[/bold]")
        if self.memory_info["total_ram"]:
            console.print(f"  Total RAM: {self.memory_info['total_ram']:.1f} {self.memory_info['ram_units']}")
        else:
            console.print("  Total RAM: Could not detect")
        
        # Platform Capabilities
        console.print("\n[bold]TTS Platform Support:[/bold]")
        console.print(f"  Primary Platform: {self.platform_capabilities['primary_platform'].upper()}")
        console.print(f"  Supported Platforms: {', '.join(self.platform_capabilities['supported_platforms']).upper()}")
        
        # Recommendations
        console.print("\n[bold]Recommended Models:[/bold]")
        for model in self.platform_capabilities["recommended_models"]:
            console.print(f"  ✅ {model}")
        
        # Performance Notes
        if self.platform_capabilities["performance_notes"]:
            console.print("\n[bold]Performance Notes:[/bold]")
            for note in self.platform_capabilities["performance_notes"]:
                console.print(f"  💡 {note}")
    
    def get_model_compatibility(self, model_key: str) -> Dict[str, any]:
        """Get compatibility information for a specific model."""
        compatibility = {
            "model": model_key,
            "compatible_platforms": [],
            "performance_rating": "unknown",
            "notes": []
        }
        
        # Check platform compatibility based on model
        if model_key in ["f5-tts", "edge-tts", "dia", "kyutai", "kokoro"]:
            compatibility["compatible_platforms"] = ["mps", "cuda", "cpu"]
            compatibility["performance_rating"] = "high"
            compatibility["notes"].append("Tested and working on all platforms")
        
        elif model_key in ["vibevoice"]:
            # These models have placeholder implementations but may have platform-specific issues
            return {
                "compatible": True,
                "notes": "Placeholder implementation - actual functionality may vary by platform",
                "recommendations": [
                    "Test with actual audio generation",
                    "Verify model file requirements",
                    "Check platform-specific optimizations"
                ]
            }
        
        # Check if user's platform is compatible
        user_platform = self.platform_capabilities["primary_platform"]
        if user_platform in compatibility["compatible_platforms"]:
            compatibility["notes"].append(f"✅ Compatible with your {user_platform.upper()} platform")
        else:
            compatibility["notes"].append(f"⚠️ Limited compatibility with your {user_platform.upper()} platform")
        
        return compatibility
    
    def __str__(self) -> str:
        """String representation of the platform detector."""
        platform = self.platform_capabilities["primary_platform"].upper()
        return f"PlatformDetector({platform})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the platform detector."""
        return f"{self.__class__.__name__}(platform={self.platform_capabilities['primary_platform']})"
