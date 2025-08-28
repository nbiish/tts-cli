#!/usr/bin/env python3
"""
Environment Manager Module - Isolated UV Environment Management

Manages isolated UV environments for each TTS model to prevent dependency conflicts.
Each TTS model gets its own isolated environment with model-specific packages.

Author: Nbiish Waabanimii-Kinawaabakizi
Date: 2025
Version: 2.1
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from rich.console import Console

# Initialize console for rich output
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
            "dia": {
                "packages": ["transformers[torch]", "torch", "soundfile"],
                "python_version": "3.12",
                "description": "Dia dialogue generation TTS using transformers"
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
                    if model_key == "dia":
                        # Install transformers main branch for Dia
                        console.print(f"[cyan]📥 Installing transformers main branch for {model_key}...[/cyan]")
                        main_result = subprocess.run(
                            ["uv", "pip", "install", "--python", str(python_path), "git+https://github.com/huggingface/transformers.git"],
                            cwd=env_path,
                            capture_output=True,
                            text=True
                        )
                        if main_result.returncode != 0:
                            console.print(f"[red]❌ Failed to install transformers main branch: {main_result.stderr}[/red]")
                            return False
                    elif model_key == "kyutai":
                        # Install moshi_mlx for Kyutai
                        console.print(f"[cyan]📥 Installing moshi_mlx for {model_key}...[/cyan]")
                        mlx_result = subprocess.run(
                            ["uv", "pip", "install", "--python", str(python_path), "moshi_mlx"],
                            cwd=env_path,
                            capture_output=True,
                            text=True
                        )
                        if mlx_result.returncode != 0:
                            console.print(f"[red]❌ Failed to install moshi_mlx: {mlx_result.stderr}[/red]")
                            return False
                    elif model_key == "kokoro":
                        # Install kokoro package for Kokoro
                        console.print(f"[cyan]📥 Installing kokoro package for {model_key}...[/cyan]")
                        kokoro_result = subprocess.run(
                            ["uv", "pip", "install", "--python", str(python_path), "kokoro>=0.9.2", "soundfile"],
                            cwd=env_path,
                            capture_output=True,
                            text=True
                        )
                        if kokoro_result.returncode != 0:
                            console.print(f"[red]❌ Failed to install kokoro: {kokoro_result.stderr}[/red]")
                            return False
                    else:
                        console.print(f"[red]❌ Failed to install {package} from any source[/red]")
                        return False
            
            # Execute post-install commands if specified
            if "post_install_commands" in env_config:
                console.print(f"[cyan]🔧 Running post-install commands for {model_key}...[/cyan]")
                for command in env_config["post_install_commands"]:
                    console.print(f"[cyan]➤ {command}[/cyan]")
                    
                    # Execute in the environment's context
                    post_result = subprocess.run(
                        command,
                        shell=True,
                        cwd=env_path,
                        capture_output=True,
                        text=True,
                        env={**os.environ, "VIRTUAL_ENV": str(env_path / ".venv"), "PATH": f"{env_path / '.venv' / 'bin'}:{os.environ.get('PATH', '')}"}
                    )
                    
                    if post_result.returncode != 0:
                        console.print(f"[yellow]⚠️ Post-install command failed: {command}[/yellow]")
                        console.print(f"[yellow]Error: {post_result.stderr}[/yellow]")
                        # Continue with other commands rather than failing completely
                    else:
                        console.print(f"[green]✅ Post-install command successful: {command}[/green]")
            
            console.print(f"[green]✅ Environment for {model_key} created successfully![/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Error creating environment for {model_key}: {e}[/red]")
            return False
    
    def cleanup_environment(self, model_key: str) -> bool:
        """Remove an environment for a specific model."""
        if model_key not in self.environments:
            console.print(f"[red]❌ Unknown model: {model_key}[/red]")
            return False
        
        env_path = self.get_environment_path(model_key)
        
        if not env_path.exists():
            console.print(f"[yellow]⚠️ Environment for {model_key} does not exist[/yellow]")
            return True
        
        try:
            console.print(f"[cyan]🧹 Cleaning up environment for {model_key}...[/cyan]")
            shutil.rmtree(env_path)
            console.print(f"[green]✅ Environment for {model_key} removed successfully[/green]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Error removing environment for {model_key}: {e}[/red]")
            return False
    
    def cleanup_all_environments(self) -> bool:
        """Remove all environments."""
        try:
            console.print("[cyan]🧹 Cleaning up all environments...[/cyan]")
            if self.base_dir.exists():
                shutil.rmtree(self.base_dir)
                self.base_dir.mkdir(exist_ok=True)
            console.print("[green]✅ All environments removed successfully[/green]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Error removing all environments: {e}[/red]")
            return False
    
    def list_environments(self) -> Dict[str, Dict[str, Any]]:
        """List all available environments and their status."""
        env_status = {}
        
        for model_key, config in self.environments.items():
            env_path = self.get_environment_path(model_key)
            exists = self.environment_exists(model_key)
            
            env_status[model_key] = {
                "status": "✅ Ready" if exists else "❌ Not Created",
                "path": str(env_path),
                "packages": config["packages"],
                "description": config["description"]
            }
        
        return env_status
    
    def get_python_path(self, model_key: str) -> Optional[Path]:
        """Get the Python executable path for a specific model's environment."""
        if not self.environment_exists(model_key):
            return None
        
        env_path = self.get_environment_path(model_key)
        python_path = env_path / ".venv" / "bin" / "python"
        
        if not python_path.exists():
            # Try Windows path format
            python_path = env_path / ".venv" / "Scripts" / "python.exe"
        
        return python_path if python_path.exists() else None
    
    def run_in_environment(self, model_key: str, command: List[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
        """Run a command in a specific model's isolated environment."""
        python_path = self.get_python_path(model_key)
        if not python_path:
            raise ValueError(f"Environment for {model_key} does not exist")
        
        env_path = self.get_environment_path(model_key)
        env = {
            **os.environ,
            "VIRTUAL_ENV": str(env_path / ".venv"),
            "PATH": f"{env_path / '.venv' / 'bin'}:{os.environ.get('PATH', '')}"
        }
        
        return subprocess.run(
            command,
            env=env,
            cwd=cwd or env_path,
            capture_output=True,
            text=True
        )
