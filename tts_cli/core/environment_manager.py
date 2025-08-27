#!/usr/bin/env python3
"""
MultiEnvironmentManager - Manages isolated UV environments for TTS models.

This module provides isolated environment management to prevent dependency
conflicts between different TTS models.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
from rich.console import Console
import shutil

# Initialize console
console = Console()

class MultiEnvironmentManager:
    """
    Manages isolated UV environments for each TTS model to prevent dependency conflicts.
    
    Each TTS model gets its own isolated environment with model-specific packages,
    preventing issues like protobuf version conflicts between different models.
    """
    
    def __init__(self, base_dir: str = ".model-envs"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.environments = {
            "f5-tts": {
                "packages": ["f5-tts"],
                "python_version": "3.12",
                "description": "F5-TTS with voice cloning capabilities"
            },
            "edge-tts": {
                "packages": ["edge-tts"],
                "python_version": "3.12",
                "description": "Microsoft Edge TTS with 322+ voices"
            },
            "higgs-audio-v2": {
                "packages": ["boson-multimodal"],
                "python_version": "3.12",
                "description": "Higgs Audio v2 with DualFFN architecture"
            },
            "dia": {
                "packages": ["transformers[torch]", "torch", "soundfile"],
                "python_version": "3.12",
                "description": "Dia dialogue generation TTS using transformers"
            },
            "thinksound": {
                "packages": ["transformers[torch]", "torch", "soundfile", "librosa"],
                "python_version": "3.10",  # ThinkSound requires Python 3.10
                "description": "ThinkSound MLLM integration using transformers"
            },
            "kyutai": {
                "packages": ["moshi_mlx"],
                "python_version": "3.12",
                "description": "Kyutai TTS with streaming support"
            },
            "kokoro": {
                "packages": ["kokoro", "soundfile", "numpy", "torch"],
                "python_version": "3.12",
                "description": "Kokoro lightweight TTS"
            },
            "vibevoice": {
                "packages": ["transformers[torch]", "torch", "soundfile", "librosa"],
                "python_version": "3.12",
                "description": "VibeVoice long-form conversational TTS using transformers"
            }
        }
    
    def get_environment_path(self, model_key: str) -> Path:
        """Get the path to the environment for a specific model."""
        return self.base_dir / f"{model_key}-env"
    
    def environment_exists(self, model_key: str) -> bool:
        """Check if an environment exists for a specific model."""
        env_path = self.get_environment_path(model_key)
        return env_path.exists() and (env_path / ".venv").exists()
    
    def create_environment(self, model_key: str) -> bool:
        """Create a new isolated UV environment for a specific model."""
        if model_key not in self.environments:
            console.print(f"[red]❌ Unknown model: {model_key}[/red]")
            return False
        
        env_config = self.environments[model_key]
        env_path = self.get_environment_path(model_key)
        
        try:
            console.print(f"[cyan]🔧 Creating isolated environment for {model_key}...[/cyan]")
            console.print(f"[cyan]📦 Packages: {', '.join(env_config['packages'])}[/cyan]")
            console.print(f"[cyan]🐍 Python: {env_config['python_version']}[/cyan]")
            
            # Create environment directory
            env_path.mkdir(exist_ok=True)
            
            # Create UV environment
            result = subprocess.run(
                ["uv", "venv", "--python", f"python{env_config['python_version']}", ".venv"],
                cwd=env_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                console.print(f"[red]❌ Failed to create UV environment: {result.stderr}[/red]")
                return False
            
            # Verify the environment was created and Python executable exists
            python_path = env_path.absolute() / ".venv" / "bin" / "python"
            if not python_path.exists():
                # Try Windows path format
                python_path = env_path.absolute() / ".venv" / "Scripts" / "python.exe"
            
            if not python_path.exists():
                console.print(f"[red]❌ UV environment creation failed - Python executable not found at {python_path}[/red]")
                console.print(f"[red]UV output: {result.stdout}[/red]")
                console.print(f"[red]UV error: {result.stderr}[/red]")
                return False
            
            console.print(f"[green]✅ UV environment created successfully with Python at {python_path}[/green]")
            
            # Install packages in the isolated environment
            for package in env_config["packages"]:
                console.print(f"[cyan]📥 Installing {package} in isolated environment...[/cyan]")
                
                # Use UV to install packages in the environment
                install_result = subprocess.run(
                    ["uv", "pip", "install", "--python", str(python_path), package],
                    cwd=env_path,
                    capture_output=True,
                    text=True
                )
                
                if install_result.returncode != 0:
                    console.print(f"[yellow]⚠️ PyPI installation failed for {package}, trying alternative sources...[/yellow]")
                    
                    # Try alternative installation methods based on model
                    if model_key == "higgs-audio-v2" and package == "boson-multimodal":
                        # Install from GitHub for Higgs Audio v2
                        self._install_higgs_from_github(env_path)
                    elif model_key == "thinksound" and package == "thinksound":
                        # Install ThinkSound with conda dependencies
                        self._install_thinksound_with_conda(env_path)
                    else:
                        console.print(f"[red]❌ Failed to install {package} from any source[/red]")
                        return False
            
            console.print(f"[green]✅ Isolated environment created successfully for {model_key}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Error creating environment for {model_key}: {e}[/red]")
            return False
    
    def _install_higgs_from_github(self, env_path: Path):
        """Install Higgs Audio v2 from GitHub repository."""
        try:
            # Clone and install from GitHub
            subprocess.run(
                ["git", "clone", "https://github.com/boson-ai/higgs-audio.git", "higgs-audio"],
                cwd=env_path,
                check=True
            )
            
            python_path = env_path.absolute() / ".venv" / "bin" / "python"
            if not python_path.exists():
                python_path = env_path.absolute() / ".venv" / "Scripts" / "python.exe"
            
            subprocess.run(
                ["uv", "pip", "install", "--python", str(python_path), "-r", "higgs-audio/requirements.txt"],
                cwd=env_path,
                check=True
            )
            
            subprocess.run(
                ["uv", "pip", "install", "--python", str(python_path), "-e", "higgs-audio"],
                cwd=env_path,
                check=True
            )
            
            console.print("[green]✅ Higgs Audio v2 installed from GitHub[/green]")
            
        except subprocess.CalledProcessError as e:
            console.print(f"[red]❌ Failed to install Higgs Audio v2 from GitHub: {e}[/red]")
            raise
    
    def _install_thinksound_with_conda(self, env_path: Path):
        """Install ThinkSound with conda dependencies."""
        try:
            python_path = env_path.absolute() / ".venv" / "bin" / "python"
            if not python_path.exists():
                python_path = env_path.absolute() / ".venv" / "Scripts" / "python.exe"
            
            # Install ThinkSound package
            subprocess.run(
                ["uv", "pip", "install", "--python", str(python_path), "thinksound"],
                cwd=env_path,
                check=True
            )
            
            # Note: FFmpeg <7 requirement would need to be handled separately
            # as it's a system dependency, not a Python package
            console.print("[green]✅ ThinkSound installed (FFmpeg <7 may be required)[/green]")
            
        except subprocess.CalledProcessError as e:
            console.print(f"[red]❌ Failed to install ThinkSound: {e}[/red]")
            raise
    
    def get_environment_python(self, model_key: str) -> Optional[str]:
        """Get the Python executable path for a specific model's environment."""
        if not self.environment_exists(model_key):
            if not self.create_environment(model_key):
                return None
        
        env_path = self.get_environment_path(model_key)
        python_path = env_path / ".venv" / "bin" / "python"
        
        if not python_path.exists():
            # Try Windows path
            python_path = env_path / ".venv" / "Scripts" / "python.exe"
        
        if python_path.exists():
            return str(python_path)
        
        return None
    
    def run_in_environment(self, model_key: str, script_content: str, **kwargs) -> Optional[Any]:
        """Run a Python script in the isolated environment for a specific model."""
        python_path = self.get_environment_python(model_key)
        if not python_path:
            return None
        
        try:
            # Create temporary script file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(script_content)
                script_path = f.name
            
            try:
                # Run script in isolated environment
                result = subprocess.run(
                    [python_path, script_path],
                    capture_output=True,
                    text=True,
                    **kwargs
                )
                
                if result.returncode == 0:
                    return result.stdout
                else:
                    console.print(f"[red]❌ Script execution failed: {result.stderr}[/red]")
                    return None
                    
            finally:
                # Clean up temporary script
                try:
                    os.unlink(script_path)
                except:
                    pass
                    
        except Exception as e:
            console.print(f"[red]❌ Error running script in {model_key} environment: {e}[/red]")
            return None
    
    def list_environments(self) -> Dict[str, Dict[str, Any]]:
        """List all available environments and their status."""
        status = {}
        for model_key, config in self.environments.items():
            env_path = self.get_environment_path(model_key)
            exists = self.environment_exists(model_key)
            python_path = self.get_environment_python(model_key) if exists else None
            
            status_text = "✅ Ready" if exists else "❌ Not Created"
            description = config["description"]
            
            status[model_key] = {
                "exists": exists,
                "path": str(env_path),
                "python_path": python_path,
                "packages": config["packages"],
                "description": description,
                "status": status_text
            }
        
        return status
    
    def cleanup_environment(self, model_key: str) -> bool:
        """Remove a specific model's environment."""
        if model_key not in self.environments:
            console.print(f"[red]❌ Unknown model: {model_key}[/red]")
            return False
        
        env_path = self.get_environment_path(model_key)
        if not env_path.exists():
            console.print(f"[yellow]⚠️ Environment for {model_key} does not exist[/yellow]")
            return True
        
        try:
            shutil.rmtree(env_path)
            console.print(f"[green]✅ Environment for {model_key} removed successfully[/green]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Failed to remove environment for {model_key}: {e}[/red]")
            return False
    
    def cleanup_all_environments(self) -> bool:
        """Remove all model environments."""
        try:
            if self.base_dir.exists():
                shutil.rmtree(self.base_dir)
                self.base_dir.mkdir(exist_ok=True)
                console.print("[green]✅ All environments removed successfully[/green]")
                return True
            else:
                console.print("[yellow]⚠️ No environments exist to clean up[/yellow]")
                return True
        except Exception as e:
            console.print(f"[red]❌ Failed to remove all environments: {e}[/red]")
            return False
