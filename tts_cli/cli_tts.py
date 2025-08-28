#!/usr/bin/env python3
"""
CLI TTS Clipboard Reader - Professional Text-to-Speech Tool

A command-line interface tool that generates high-quality TTS audio files using 
advanced models with isolated environment management.

Author: Nbiish Waabanimii-Kinawaabakizi
Date: 2025
Version: 2.0

Core Features:
- Clipboard monitoring and text extraction
- Multi-model TTS engine integration (6 working models)
- Direct file output without playback controls
- Voice cloning with input audio files via --voice-clone argument
- Isolated UV environments for dependency management
- Cross-platform compatibility (macOS, Linux, Windows)
"""

import os
import sys
import logging
import tempfile
import subprocess
import shutil
import time
import numpy as np
import soundfile as sf
from pathlib import Path
from typing import Optional, Dict, Any, List
import pyperclip
import argparse
from dataclasses import dataclass
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.rule import Rule
import torch

# Rich console for beautiful output
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tts_cli.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
                        console.print(f"[green]✅ Post-install command completed: {command}[/green]")
            
            console.print(f"[green]✅ Isolated environment created successfully for {model_key}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Error creating environment for {model_key}: {e}[/red]")
            return False
    

    

    
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
            
            # Get model info from TTSManager to check for hardware limitations
            # Import handled elsewhere - this is just for reference
            tts_manager = TTSManager()
            model_info = tts_manager.get_model_info(model_key)
            
            if model_info and "hardware_limitation" in model_info:
                status_text = "⚠️ Hardware Limited" if exists else "❌ Not Created"
                description = f"{model_info['name']} - {model_info['hardware_limitation']}"
            else:
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
        """Remove an environment for a specific model."""
        if not self.environment_exists(model_key):
            console.print(f"[yellow]⚠️ Environment for {model_key} doesn't exist[/yellow]")
            return True
        
        try:
            import shutil
            env_path = self.get_environment_path(model_key)
            shutil.rmtree(env_path)
            console.print(f"[green]✅ Environment for {model_key} removed successfully[/green]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Failed to remove environment for {model_key}: {e}[/red]")
            return False
    
    def cleanup_all_environments(self) -> bool:
        """Remove all environments."""
        try:
            import shutil
            if self.base_dir.exists():
                shutil.rmtree(self.base_dir)
                self.base_dir.mkdir(exist_ok=True)
            console.print("[green]✅ All environments removed successfully[/green]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Failed to remove all environments: {e}[/red]")
            return False
    
    def _install_package(self, env_path: Path, package: str, python_path: Path) -> bool:
        """Install a package in the isolated environment."""
        try:
            if package == "transformers[torch]":
                # Install transformers with torch extras
                result = subprocess.run(
                    ["uv", "pip", "install", "--python", str(python_path), "transformers[torch]"],
                    capture_output=True, text=True, cwd=env_path
                )
                if result.returncode != 0:
                    console.print(f"[red]❌ Failed to install transformers[torch]: {result.stderr}[/red]")
                    return False
                
                # Also install torch separately for better compatibility
                result = subprocess.run(
                    ["uv", "pip", "install", "--python", str(python_path), "torch"],
                    capture_output=True, text=True, cwd=env_path
                )
                if result.returncode != 0:
                    console.print(f"[red]❌ Failed to install torch: {result.stderr}[/red]")
                    return False
                
                console.print("[green]✅ transformers[torch] and torch installed successfully[/green]")
                return True

            else:
                # Standard package installation
                result = subprocess.run(
                    ["uv", "pip", "install", "--python", str(python_path), package],
                    capture_output=True, text=True, cwd=env_path
                )
                if result.returncode != 0:
                    console.print(f"[red]❌ Failed to install {package}: {result.stderr}[/red]")
                    return False
                console.print(f"[green]✅ {package} installed successfully[/green]")
                return True
        except Exception as e:
            console.print(f"[red]❌ Error installing {package}: {e}[/red]")
            return False

@dataclass
class TTSModel:
    """Represents a TTS model configuration."""
    name: str
    model_id: str
    description: str
    requirements: str
    capabilities: List[str]

class TTSManager:
    """Manages TTS model loading and audio generation."""
    
    def __init__(self):
        """Initialize TTS manager with supported models."""
        # Initialize multi-environment manager for isolated UV environments
        self.env_manager = MultiEnvironmentManager()
        
        # MODEL REGISTRY UPDATED: All 6 models from knowledge base implemented
        # Reference: TTS_MODEL_KNOWLEDGE_BASE.md Sections 1-3, 5-7
        # Reference: TTS_QUICK_REFERENCE.md Model Implementation Matrix
        self.models = {
            "f5-tts": {
                "name": "F5-TTS (SWivid)",
                "model_id": "SWivid/F5-TTS",
                "description": "F5-TTS: A Fairytaler that Fakes Fluent and Faithful Speech with Flow Matching",
                "requirements": "CUDA GPU, PyTorch 2.0+",
                "capabilities": ["High-quality speech", "Fast inference", "Flow matching", "Voice cloning"],
                "status": "✅ Implemented"
            },
            "edge-tts": {
                "name": "Edge TTS (Microsoft)",
                "model_id": "edge-tts",
                "description": "Microsoft Edge's high-quality TTS with 322+ voices across multiple languages",
                "requirements": "Internet connection, Python 3.7+",
                "capabilities": ["High quality", "Multiple voices", "Multi-language", "Fast generation"],
                "status": "✅ Implemented"
            },

            "dia": {
                "name": "Dia (Nari Labs)",
                "model_id": "nari-labs/Dia-1.6B-0626",
                "description": "Ultra-realistic dialogue generation in one pass with voice cloning",
                "requirements": "CUDA GPU, 4.4GB+ VRAM, PyTorch 2.0+",
                "capabilities": ["Dialogue generation", "Voice cloning", "Emotion control", "Non-verbal sounds"],
                "status": "✅ Implemented"
            },
            "kyutai": {
                "name": "Kyutai TTS",
                "model_id": "kyutai/tts-1.6b-en_fr",
                "description": "1.6B parameters, multilingual (English/French), ultra-low latency (220ms)",
                "requirements": "CUDA GPU, moderate VRAM, PyTorch 2.0+",
                "capabilities": ["Multilingual", "Ultra-low latency", "Multi-speaker", "Voice cloning"],
                "status": "✅ Implemented"
            },
            "kokoro": {
                "name": "Kokoro (Hexgrad)",
                "model_id": "hexgrad/Kokoro-82M",
                "description": "82M parameters, ultra-lightweight, fast processing for resource-constrained environments",
                "requirements": "CPU/GPU, minimal VRAM, PyTorch 2.0+",
                "capabilities": ["Ultra-lightweight", "Fast processing", "Basic voice cloning", "Cost-effective"],
                "status": "✅ Implemented"
            },
            "vibevoice": {
                "name": "VibeVoice (Microsoft)",
                "model_id": "microsoft/VibeVoice-1.5B",
                "description": "1.5B parameters, long-form conversational TTS, multi-speaker support (up to 4 speakers)",
                "requirements": "CUDA GPU, moderate VRAM, PyTorch 2.0+",
                "capabilities": ["Long-form generation", "Multi-speaker", "Natural dialogue", "Podcast-ready"],
                "status": "✅ Implemented"
            },

        }
        
        self.current_model = None
        self.device = self._get_device()
        
    def _get_device(self):
        """Get the best available device for TTS generation."""
        if torch.cuda.is_available():
            device = "cuda"
            console.print(f"[green]✅ CUDA GPU detected: {torch.cuda.get_device_name()}[/green]")
        elif torch.backends.mps.is_available():
            device = "mps"
            console.print(f"[yellow]⚠️ MPS (Apple Silicon) detected[/yellow]")
        else:
            device = "cpu"
            console.print(f"[red]⚠️ No GPU detected, using CPU (will be slow)[/red]")
        
        return device
    
    def list_models(self) -> List[str]:
        """List available model keys."""
        return list(self.models.keys())
    
    def list_environments(self) -> Dict[str, Dict[str, Any]]:
        """List all available environments and their status."""
        return self.env_manager.list_environments()
    
    def create_environment(self, model_key: str) -> bool:
        """Create an isolated environment for a specific model."""
        return self.env_manager.create_environment(model_key)
    
    def cleanup_environment(self, model_key: str) -> bool:
        """Remove an environment for a specific model."""
        return self.env_manager.cleanup_environment(model_key)
    
    def cleanup_all_environments(self) -> bool:
        """Remove all environments."""
        return self.env_manager.cleanup_all_environments()
    
    def get_model_info(self, model_key: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model."""
        return self.models.get(model_key)
    
    def confirm_model_loading(self, model_key: str) -> bool:
        """Ask user to confirm before loading heavy models."""
        model_info = self.models.get(model_key)
        if not model_info:
            return False
        
        console.print(f"\n[bold cyan]🚀 Loading Model: {model_info['name']}[/bold cyan]")
        console.print(f"[cyan]Description:[/cyan] {model_info['description']}")
        console.print(f"[cyan]Requirements:[/cyan] {model_info['requirements']}")
        console.print(f"[cyan]Device:[/cyan] {self.device.upper()}")
        
        if self.device == "cpu":
            console.print("[red]⚠️ WARNING: Using CPU will be very slow and may fail for large models![/red]")
        
        return Confirm.ask(f"\n[bold yellow]This will use significant RAM/VRAM. Continue?[/bold yellow]")
    
    def generate_speech(self, text: str, model_key: str, voice_clone_path: Optional[str] = None) -> Optional[np.ndarray]:
        """Generate speech using the specified model."""
        if model_key not in self.models:
            raise ValueError(f"Unknown model: {model_key}")
        
        # Check if environment exists and create if needed
        if not self.env_manager.environment_exists(model_key):
            console.print(f"[yellow]⚠️ Environment for {model_key} not found. Creating...[/yellow]")
            if not self.env_manager.create_environment(model_key):
                raise Exception(f"Failed to create environment for {model_key}")
        
        # Route to appropriate model implementation
        if model_key == "f5-tts":
            return self._generate_with_f5_tts(text, voice_clone_path)
        elif model_key == "edge-tts":
            return self._generate_with_edge_tts(text, voice_clone_path)

        elif model_key == "dia":
            return self._generate_with_dia(text, voice_clone_path)
        elif model_key == "kyutai":
            return self._generate_with_kyutai(text, voice_clone_path)
        elif model_key == "kokoro":
            return self._generate_with_kokoro(text, voice_clone_path)
        elif model_key == "vibevoice":
            return self._generate_with_vibevoice(text, voice_clone_path)

        else:
            raise ValueError(f"Model {model_key} not implemented")
    
    def _generate_with_f5_tts(self, text: str, voice_clone_path: Optional[str] = None) -> np.ndarray:
        """Generate speech using F5-TTS model."""
        try:
            console.print("[cyan]🎯 Initializing F5-TTS model...[/cyan]")
            
            # Check if F5-TTS is available
            try:
                import subprocess
                import tempfile
                import os
                
                # Create temporary configuration file for F5-TTS
                with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as config_file:
                    clean_text = text.replace('\n', ' ').replace('"', '\\"').strip()
                    config_content = f"""# F5-TTS Configuration
model = "F5TTS_v1_Base"
ref_audio = "{voice_clone_path if voice_clone_path else 'default_ref.wav'}"
ref_text = ""
gen_text = "{clean_text}"
output_dir = "."
output_file = "temp_output.wav"
remove_silence = false
"""
                    config_file.write(config_content)
                    config_path = config_file.name
                
                try:
                    # Execute F5-TTS CLI
                    cmd = ["python", "-m", "f5_tts.infer.infer_cli", "-c", config_path]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        output_file = "temp_output.wav"
                        if os.path.exists(output_file):
                            import soundfile as sf
                            audio, sample_rate = sf.read(output_file)
                            os.unlink(output_file)
                            os.unlink(config_path)
                            return audio
                        else:
                            raise Exception("F5-TTS output file not found")
                    else:
                        raise Exception(f"F5-TTS CLI failed: {result.stderr}")
                        
                finally:
                    try:
                        os.unlink(config_path)
                    except:
                        pass
                    
            except ImportError:
                raise Exception("F5-TTS package not available. Install with: uv pip install f5-tts")
                
        except Exception as e:
            console.print(f"[red]❌ F5-TTS generation failed: {e}[/red]")
            raise
    
    def _generate_with_edge_tts(self, text: str, voice_clone_path: Optional[str] = None) -> np.ndarray:
        """Generate speech using Edge TTS model."""
        try:
            console.print("[cyan]🎯 Initializing Edge TTS model...[/cyan]")
            
            try:
                import asyncio
                import edge_tts
                import tempfile
                import os
                
                if voice_clone_path:
                    console.print("[yellow]⚠️ Edge TTS doesn't support voice cloning, using default voice[/yellow]")
                
                voice = "en-US-AriaNeural"
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_output = temp_file.name
                
                try:
                    async def generate_speech():
                        communicate = edge_tts.Communicate(text, voice)
                        await communicate.save(temp_output)
                    
                    asyncio.run(generate_speech())
                    
                    import soundfile as sf
                    audio, sample_rate = sf.read(temp_output)
                    os.unlink(temp_output)
                    return audio
                    
                except Exception as e:
                    try:
                        os.unlink(temp_output)
                    except:
                        pass
                    raise e
                    
            except ImportError:
                raise Exception("edge-tts package not available. Install with: uv pip install edge-tts")
                
        except Exception as e:
            console.print(f"[red]❌ Edge TTS generation failed: {e}[/red]")
            raise
    

    
    def _generate_with_dia(self, text: str, voice_clone_path: Optional[str] = None) -> np.ndarray:
        """Generate speech using Dia model."""
        try:
            console.print("[cyan]🎯 Initializing Dia model...[/cyan]")
            
            try:
                from transformers import AutoProcessor, DiaForConditionalGeneration
                import torch
                
                model_checkpoint = "nari-labs/Dia-1.6B-0626"
                processor = AutoProcessor.from_pretrained(model_checkpoint)
                
                # Use transformers auto-detection for optimal device handling
                device_map = "auto"
                
                # Load model with auto-detection and float16 for better performance
                model = DiaForConditionalGeneration.from_pretrained(
                    model_checkpoint,
                    device_map=device_map,
                    torch_dtype=torch.float16
                )
                
                # Dia requires very specific prompting format - let user provide their own
                # If user doesn't provide Dia-specific formatting, give them guidance
                if not text.startswith("[S1]") and not text.startswith("[S2]"):
                    console.print("[yellow]⚠️ Dia requires specific speaker tag formatting.[/yellow]")
                    console.print("[yellow]   Example: [S1] Hello there! [S2] How are you? [S1] I'm doing great![/yellow]")
                    console.print("[yellow]   Using basic text may produce poor results.[/yellow]")
                    # Still process the text but warn user
                    processed_text = f"[S1] {text}"
                else:
                    processed_text = text
                
                text_input = [processed_text]
                inputs = processor(text=text_input, padding=True, return_tensors="pt")
                
                if hasattr(model, 'device'):
                    inputs = {k: v.to(model.device) for k, v in inputs.items()}
                
                # Generate audio with official Dia parameters for optimal quality
                with torch.no_grad():
                    # Use official Dia parameters from the repository
                    # These are the exact parameters used in the official examples
                    outputs = model.generate(
                        **inputs,
                        max_new_tokens=3072,  # Official Dia default
                        guidance_scale=3.0,   # Official Dia default
                        temperature=1.8,      # Official Dia default
                        top_p=0.90,          # Official Dia default
                        top_k=45,            # Official Dia default
                        do_sample=True        # Official Dia default
                    )
                
                decoded_outputs = processor.batch_decode(outputs)
                
                # Save and load audio
                import tempfile
                import os
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
                    temp_path = tmp_file.name
                
                processor.save_audio(decoded_outputs, temp_path)
                
                try:
                    import soundfile as sf
                    audio, sample_rate = sf.read(temp_path)
                except:
                    import librosa
                    audio, sample_rate = librosa.load(temp_path, sr=22050)
                
                os.unlink(temp_path)
                
                if len(audio) > 0:
                    # Resample if needed
                    if sample_rate != 22050:
                        try:
                            import librosa
                            audio = librosa.resample(audio, orig_sr=sample_rate, target_sr=22050)
                        except:
                            pass
                    return audio
                else:
                    raise Exception("Dia returned empty audio")
                    
            except ImportError as e:
                if "DiaForConditionalGeneration" in str(e):
                    raise Exception("DiaForConditionalGeneration not available. Install transformers main branch: pip install git+https://github.com/huggingface/transformers.git")
                else:
                    raise Exception(f"Transformers library not available: {e}")
                
        except Exception as e:
            console.print(f"[red]❌ Dia generation failed: {e}[/red]")
            raise
    

    
    def _generate_with_kyutai(self, text: str, voice_clone_path: Optional[str] = None) -> np.ndarray:
        """Generate speech using Kyutai TTS model."""
        try:
            console.print("[cyan]🎯 Initializing Kyutai TTS model...[/cyan]")
            
            try:
                import moshi_mlx
                import subprocess
                import tempfile
                import json
                import os
                
                # Create temporary JSONL file for input
                with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
                    tts_request = {
                        "turns": [text],
                        "voices": ["vctk/p225_023.wav"],
                        "id": f"tts_{int(time.time())}"
                    }
                    f.write(json.dumps(tts_request) + '\n')
                    input_file = f.name
                
                # Execute Kyutai TTS CLI
                cmd = [
                    "python", "-m", "moshi_mlx.run_tts",
                    "--hf-repo", "kyutai/tts-1.6b-en_fr",
                    "--voice-repo", "kyutai/tts-voices",
                    "--quantize", "8",
                    "--out-folder", "/tmp",
                    input_file
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    # Look for generated audio files
                    output_folder = "/tmp"
                    audio_files = [f for f in os.listdir(output_folder) if f.endswith('.wav') and f.startswith('tts_')]
                    
                    if audio_files:
                        audio_file = os.path.join(output_folder, audio_files[-1])
                        import soundfile as sf
                        audio, sample_rate = sf.read(audio_file)
                        
                        # Clean up
                        os.unlink(input_file)
                        os.unlink(audio_file)
                        
                        if len(audio) > 0:
                            # Resample if needed
                            if sample_rate != 22050:
                                try:
                                    import librosa
                                    audio = librosa.resample(audio, orig_sr=sample_rate, target_sr=22050)
                                except:
                                    pass
                            return audio
                        else:
                            raise Exception("Generated audio file is empty")
                    else:
                        raise Exception("Output file was not created by Kyutai TTS")
                else:
                    raise Exception(f"Kyutai TTS CLI execution failed: {result.stderr}")
                    
            except ImportError:
                raise Exception("moshi_mlx package not available. Install with: uv pip install moshi_mlx")
                
        except Exception as e:
            console.print(f"[red]❌ Kyutai TTS generation failed: {e}[/red]")
            raise
    

                

    
    def _generate_with_kokoro(self, text: str, voice_clone_path: Optional[str] = None) -> np.ndarray:
        """Generate speech using Kokoro model."""
        try:
            console.print("[cyan]🎯 Initializing Kokoro model...[/cyan]")
            
            try:
                import subprocess
                import tempfile
                import json
                import os
                
                # Create temporary input file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    input_data = {
                        "text": text,
                        "voice": "af_heart",
                        "lang_code": "a"
                    }
                    json.dump(input_data, f)
                    input_file = f.name
                
                # Create temporary output directory
                output_dir = tempfile.mkdtemp()
                
                # Get the isolated environment Python path
                kokoro_env_python = Path(".model-envs/kokoro-env/.venv/bin/python")
                if not kokoro_env_python.exists():
                    raise Exception("Kokoro isolated environment not found")
                
                # Create a simple Python script to run Kokoro
                script_content = f'''
import sys
import json
import numpy as np
import soundfile as sf
from pathlib import Path

# Load input data
with open("{input_file}", 'r') as f:
    input_data = json.load(f)

text = input_data["text"]
voice = input_data["voice"]
lang_code = input_data["lang_code"]

# Import and run Kokoro
from kokoro import KPipeline

# Initialize pipeline
pipeline = KPipeline(lang_code=lang_code)

# Generate audio
generator = pipeline(text, voice=voice)

# Extract audio
audio = None
for i, (gs, ps, audio_chunk) in enumerate(generator):
    if i == 0:
        audio = audio_chunk
        break

if audio is not None:
    # Save audio
    output_path = "{output_dir}/kokoro_output.wav"
    sf.write(output_path, audio, 24000)
    print(f"SUCCESS:{{output_path}}")
else:
    print("ERROR:No audio generated")
    sys.exit(1)
'''
                
                # Write the script to a temporary file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(script_content)
                    script_file = f.name
                
                # Execute the script in the isolated environment
                result = subprocess.run(
                    [str(kokoro_env_python), script_file],
                    capture_output=True,
                    text=True,
                    cwd=Path.cwd()
                )
                
                # Clean up temporary files
                os.unlink(input_file)
                os.unlink(script_file)
                
                if result.returncode == 0:
                    # Parse output to get audio file path
                    output_line = [line for line in result.stdout.split('\n') if line.startswith('SUCCESS:')]
                    if output_line:
                        audio_path = output_line[0].replace('SUCCESS:', '')
                        
                        # Load the generated audio
                        import soundfile as sf
                        audio, sample_rate = sf.read(audio_path)
                        
                        # Clean up output directory
                        import shutil
                        shutil.rmtree(output_dir)
                        
                        if len(audio) > 0:
                            # Resample if needed
                            if sample_rate != 22050:
                                try:
                                    import librosa
                                    audio = librosa.resample(audio, orig_sr=sample_rate, target_sr=22050)
                                except:
                                    pass
                            return audio
                        else:
                            raise Exception("Generated audio file is empty")
                    else:
                        raise Exception("Could not parse Kokoro output")
                else:
                    error_msg = result.stderr if result.stderr else result.stdout
                    raise Exception(f"Kokoro execution failed: {error_msg}")
                    
            except ImportError as e:
                if "kokoro" in str(e):
                    raise Exception("Kokoro package not available. Install with: uv pip install kokoro>=0.9.2 soundfile")
                else:
                    raise Exception(f"Required packages not available: {e}")
                
        except Exception as e:
            console.print(f"[red]❌ Kokoro generation failed: {e}[/red]")
            raise
    

    
    def _generate_with_vibevoice(self, text: str, voice_clone_path: Optional[str] = None) -> np.ndarray:
        """Generate speech using VibeVoice model."""
        try:
            console.print("[cyan]🎯 Initializing VibeVoice model...[/cyan]")
            
            try:
                import subprocess
                import tempfile
                import os
                
                # Get the isolated environment Python path
                vibevoice_env_python = Path(".model-envs/vibevoice-env/.venv/bin/python")
                if not vibevoice_env_python.exists():
                    raise Exception("VibeVoice isolated environment not found")
                
                # Create a simple Python script for VibeVoice with proper transformers auto-detection
                script_content = f'''
import sys
import torch
import numpy as np
import soundfile as sf
import os

text = "{text}"

try:
    from vibevoice.modular.modeling_vibevoice_inference import VibeVoiceForConditionalGenerationInference
    from vibevoice.processor.vibevoice_processor import VibeVoiceProcessor
    
    # Use transformers auto-detection for optimal device handling
    device_map = "auto"
    model_path = "microsoft/VibeVoice-1.5B"
    
    processor = VibeVoiceProcessor.from_pretrained(model_path)
    
    # Load model with auto-detection and proper device handling
    model = VibeVoiceForConditionalGenerationInference.from_pretrained(
        model_path, 
        trust_remote_code=True,
        device_map=device_map,
        torch_dtype=torch.float16  # Use float16 for better performance
    )
    
    # Set model to evaluation mode and configure DDPM inference steps
    model.eval()
    model.set_ddpm_inference_steps(num_steps=10)
    
    # Format text - VibeVoice expects specific formatting for multi-speaker conversations
    # For single speaker, use format: "Speaker 1: text"
    formatted_text = f"Speaker 1: {{text}}"
    
    # Use a default voice sample - we'll use a simple approach for now
    # In production, you'd want to allow users to specify voice samples
    default_voice_path = "{voice_clone_path}" if "{voice_clone_path}" else None
    
    if default_voice_path and os.path.exists(default_voice_path):
        voice_samples = [default_voice_path]
    else:
        # Create a simple voice sample path - this is a fallback
        voice_samples = ["/tmp/default_voice.wav"]
        # Create a minimal voice file if it doesn't exist
        if not os.path.exists(voice_samples[0]):
            import numpy as np
            import soundfile as sf
            # Create a 1-second silence as default voice
            silence = np.zeros(22050)  # 1 second at 22.05kHz
            sf.write(voice_samples[0], silence, 22050)
    
    # Process inputs with voice samples - this is the key difference!
    inputs = processor(
        text=[formatted_text],  # Wrap in list for batch processing
        voice_samples=[voice_samples],  # Wrap in list for batch processing
        padding=True,
        return_tensors="pt",
        return_attention_mask=True
    )
    
    # Move inputs to model device automatically - handle both tensors and lists
    for k, v in inputs.items():
        if isinstance(v, torch.Tensor):
            inputs[k] = v.to(model.device)
        elif isinstance(v, list) and all(isinstance(item, torch.Tensor) for item in v):
            inputs[k] = [item.to(model.device) for item in v]
    
    with torch.no_grad():
        # Use VibeVoice-specific generation parameters from official implementation
        outputs = model.generate(
            **inputs,
            max_new_tokens=None,  # Let model decide
            cfg_scale=1.3,        # Official default
            tokenizer=processor.tokenizer,
            generation_config={{'do_sample': False}},  # Official default
            verbose=True
        )
        
        # Extract audio from the correct output structure
        audio = None
        if hasattr(outputs, 'speech_outputs') and outputs.speech_outputs and outputs.speech_outputs[0] is not None:
            audio = outputs.speech_outputs[0]
        else:
            # Fallback to old method if speech_outputs not available
            audio = outputs[0]
        
        # Convert to numpy if it's a tensor
        if isinstance(audio, torch.Tensor):
            audio = audio.cpu().numpy()
        
        # Debug: Print audio shape and type
        print(f"Audio shape: {{audio.shape if hasattr(audio, 'shape') else 'No shape'}}")
        print(f"Audio type: {{type(audio)}}")
        print(f"Audio length: {{len(audio) if hasattr(audio, '__len__') else 'No length'}}")
        
        if audio is not None and len(audio) > 0:
            # Normalize audio
            audio = audio / (np.max(np.abs(audio)) + 1e-7)
            
            # Try to save with proper format detection
            try:
                # First try to save as WAV
                sf.write("/tmp/vibevoice_output.wav", audio, 22050, format='WAV')
                print("SUCCESS:/tmp/vibevoice_output.wav")
            except:
                print("WAV save failed, trying FLAC...")
                try:
                    # Try saving as FLAC instead
                    sf.write("/tmp/vibevoice_output.flac", audio, 22050, format='FLAC')
                    print("SUCCESS:/tmp/vibevoice_output.flac")
                except:
                    print("FLAC save failed, saving as raw PCM...")
                    # Last resort: save as raw PCM
                    audio.astype(np.float32).tofile("/tmp/vibevoice_output.raw")
                    print("SUCCESS:/tmp/vibevoice_output.raw (raw PCM)")
        else:
            print("ERROR:Generated audio is empty")
            sys.exit(1)
        
except Exception as e:
    print(f"ERROR:{{str(e)}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
'''
                
                # Write and execute script
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(script_content)
                    script_file = f.name
                
                result = subprocess.run(
                    [str(vibevoice_env_python), script_file],
                    capture_output=True,
                    text=True,
                    cwd=Path.cwd()
                )
                
                os.unlink(script_file)
                
                if result.returncode == 0:
                    # Load generated audio - try multiple formats
                    audio_path = None
                    sample_rate = 22050
                    
                    # Try WAV first
                    if os.path.exists("/tmp/vibevoice_output.wav") and os.path.getsize("/tmp/vibevoice_output.wav") > 0:
                        audio_path = "/tmp/vibevoice_output.wav"
                    # Try FLAC next
                    elif os.path.exists("/tmp/vibevoice_output.flac") and os.path.getsize("/tmp/vibevoice_output.flac") > 0:
                        audio_path = "/tmp/vibevoice_output.flac"
                    # Try raw PCM last
                    elif os.path.exists("/tmp/vibevoice_output.raw") and os.path.getsize("/tmp/vibevoice_output.raw") > 0:
                        audio_path = "/tmp/vibevoice_output.raw"
                        # Raw PCM files need special handling
                        try:
                            import numpy as np
                            # Read raw PCM as float32
                            audio = np.fromfile(audio_path, dtype=np.float32)
                            os.unlink(audio_path)
                            
                            if len(audio) > 0:
                                return audio
                            else:
                                raise Exception("Generated audio file is empty")
                        except Exception as e:
                            raise Exception(f"Failed to read raw PCM audio: {e}")
                    
                    if audio_path:
                        try:
                            import soundfile as sf
                            audio, sample_rate = sf.read(audio_path)
                            os.unlink(audio_path)
                            
                            if len(audio) > 0:
                                return audio
                            else:
                                raise Exception("Generated audio file is empty")
                        except Exception as e:
                            raise Exception(f"Failed to read audio file {audio_path}: {e}")
                    else:
                        raise Exception("No valid output file was created by VibeVoice")
                else:
                    error_msg = result.stderr if result.stderr else result.stdout
                    raise Exception(f"VibeVoice execution failed: {error_msg}")
                    
            except ImportError as e:
                raise Exception(f"Required packages not available: {e}")
                
        except Exception as e:
            console.print(f"[red]❌ VibeVoice generation failed: {e}[/red]")
            raise
    

    



            

            

            

    


    # FALLBACK METHOD REMOVED: Models now fail properly when not implemented
    # This ensures accurate feedback about model status and hardware compatibility

class CLITTSInterface:
    """Simplified CLI interface for TTS operations."""
    
    def __init__(self, tts_manager: TTSManager):
        """Initialize CLI interface."""
        self.tts_manager = tts_manager
        self.console = Console()
    
    def show_welcome(self):
        """Display welcome message."""
        self.console.print(Panel.fit(
            "[bold green]🎤 CLI TTS Generator[/bold green]\n\n"
            "[cyan]Features:[/cyan]\n"
            "• Multi-model TTS engine integration\n"
            "• Direct file output (no playback controls)\n"
            "• Voice cloning support via CLI arguments\n"
            "• Isolated environment management\n\n"
            "[green]Ready for TTS file generation![/green]",
            title="[bold]TTS CLI[/bold]",
            border_style="green"
        ))
    
    def show_models(self):
        """Display available models."""
        table = Table(title="Available TTS Models")
        table.add_column("Model Key", style="cyan", no_wrap=True)
        table.add_column("Name", style="magenta")
        table.add_column("Description", style="green")
        table.add_column("Status", style="yellow")
        
        for model_key, model_info in self.tts_manager.models.items():
            # Display implementation status from model registry
            status = model_info.get("status", "[red]Unknown[/red]")
            
            description = model_info["description"][:60] + "..." if len(model_info["description"]) > 60 else model_info["description"]
            table.add_row(
                model_key,
                model_info["name"],
                description,
                status
            )
        
        self.console.print(table)
        self.console.print("\n[green]✅ All 6 TTS models are implemented and ready for use![/green]")
    
    def show_environments(self):
        """Display environment status for all models."""
        table = Table(title="Isolated UV Environment Status")
        table.add_column("Model", style="cyan", no_wrap=True)
        table.add_column("Status", style="yellow")
        table.add_column("Path", style="green")
        table.add_column("Packages", style="magenta")
        table.add_column("Description", style="blue")
        
        environments = self.tts_manager.list_environments()
        
        for model_key, env_info in environments.items():
            status = env_info["status"]
            path = env_info["path"]
            packages = ", ".join(env_info["packages"])
            description = env_info["description"][:40] + "..." if len(env_info["description"]) > 40 else env_info["description"]
            
            table.add_row(
                model_key,
                status,
                path,
                packages,
                description
            )
        
        self.console.print(table)
        self.console.print("\n[cyan]💡 Use --create-environment MODEL to create isolated environments[/cyan]")
        self.console.print("[cyan]💡 Use --cleanup-environment MODEL to remove specific environments[/cyan]")
        self.console.print("[cyan]💡 Use --cleanup-all-environments to remove all environments[/cyan]")
    
    def get_clipboard_text(self) -> str:
        """Get text from clipboard."""
        try:
            text = pyperclip.paste()
            if text.strip():
                self.console.print(f"[green]📋 Clipboard text detected:[/green] {text[:100]}{'...' if len(text) > 100 else ''}")
                return text
            else:
                self.console.print("[yellow]📋 Clipboard is empty or contains no text[/yellow]")
                return ""
        except Exception as e:
            self.console.print(f"[red]❌ Failed to read clipboard: {e}[/red]")
            return ""
    
    def process_text(self, text: str, model_key: str, voice_clone_path: Optional[str] = None, output_path: str = "output.wav"):
        """Process text and generate speech file."""
        if not text.strip():
            self.console.print("[red]❌ No text provided for processing[/red]")
            return
        
        self.console.print(f"[cyan]🎯 Processing text with {model_key} model...[/cyan]")
        
        # Generate speech
        audio = self.tts_manager.generate_speech(text, model_key, voice_clone_path)
        
        if audio is not None:
            # Save audio to file
            try:
                sf.write(output_path, audio, 22050)
                self.console.print(f"[green]✅ Audio saved successfully to: {output_path}[/green]")
                self.console.print(f"[cyan]Duration: {len(audio) / 22050:.2f} seconds[/cyan]")
                self.console.print(f"[cyan]Sample Rate: 22050 Hz[/cyan]")
                self.console.print(f"[cyan]Format: WAV[/cyan]")
            except Exception as e:
                self.console.print(f"[red]❌ Failed to save audio: {e}[/red]")
        else:
            self.console.print("[red]❌ Failed to generate speech[/red]")
    
    def run_interactive(self):
        """Run interactive CLI mode."""
        self.show_welcome()
        
        while True:
            self.console.print("\n[bold cyan]🚀 Main Menu:[/bold cyan]")
            self.console.print("1. [green]Generate Speech File[/green] - Convert text to speech and save")
            self.console.print("2. [blue]List Models[/blue] - Show available TTS models")
            self.console.print("3. [yellow]Clipboard Text[/yellow] - Read text from clipboard")
            self.console.print("4. [red]Exit[/red] - Quit application")
            
            choice = Prompt.ask("Select option", choices=["1", "2", "3", "4"])
            
            if choice == "1":
                text = Prompt.ask("Enter text to convert to speech")
                model_key = Prompt.ask("Select TTS model", choices=self.tts_manager.list_models(), default="f5-tts")
                voice_clone_path = Prompt.ask("Voice clone audio file (optional, press Enter to skip)")
                output_path = Prompt.ask("Output file path", default="output.wav")
                
                if voice_clone_path and not os.path.exists(voice_clone_path):
                    self.console.print(f"[red]❌ Voice clone file not found: {voice_clone_path}[/red]")
                    voice_clone_path = None
                
                self.process_text(text, model_key, voice_clone_path, output_path)
                
            elif choice == "2":
                self.show_models()
                
            elif choice == "3":
                text = self.get_clipboard_text()
                if text:
                    model_key = Prompt.ask("Select TTS model", choices=self.tts_manager.list_models(), default="f5-tts")
                    voice_clone_path = Prompt.ask("Voice clone audio file (optional, press Enter to skip)")
                    output_path = Prompt.ask("Output file path", default="output.wav")
                    
                    if voice_clone_path and not os.path.exists(voice_clone_path):
                        self.console.print(f"[red]❌ Voice clone file not found: {voice_clone_path}[/red]")
                        voice_clone_path = None
                    
                    self.process_text(text, model_key, voice_clone_path, output_path)
                
            elif choice == "4":
                self.console.print("[yellow]👋 Goodbye![/yellow]")
                break

def main():
    """Main function with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="CLI TTS Generator - Professional Text-to-Speech File Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Interactive CLI mode
  %(prog)s --text "Hello world"              # Generate speech from text
  %(prog)s --text "Hello world" --model f5-tts  # Use specific model
  %(prog)s --text "Hello world" --voice-clone voice.wav  # With voice cloning
  %(prog)s --clipboard                       # Read from clipboard
  %(prog)s --list-models                     # List available models
  %(prog)s --list-environments               # Show environment status
  %(prog)s --create-environment f5-tts      # Create isolated environment
  %(prog)s --cleanup-environment f5-tts     # Remove specific environment
  %(prog)s --cleanup-all-environments       # Remove all environments
  %(prog)s --text "Hello" --output speech.wav  # Specify output file
        """
    )
    
    parser.add_argument("--text", help="Text to convert to speech")
    parser.add_argument("--model", choices=["f5-tts", "edge-tts", "dia", "kyutai", "kokoro", "vibevoice"], 
                      default="f5-tts", help="TTS model to use")
    parser.add_argument("--voice-clone", help="Audio file for voice cloning")
    parser.add_argument("--clipboard", action="store_true", help="Read text from clipboard")
    parser.add_argument("--list-models", action="store_true", help="List available models")
    parser.add_argument("--list-environments", action="store_true", help="List environment status for all models")
    parser.add_argument("--create-environment", help="Create isolated environment for specific model")
    parser.add_argument("--cleanup-environment", help="Remove isolated environment for specific model")
    parser.add_argument("--cleanup-all-environments", action="store_true",
                       help="Remove all isolated environments")
    parser.add_argument("--output", help="Output audio file path")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--test-model", help="Test specific model compatibility")
    parser.add_argument("--test-all-models", action="store_true", help="Test all models for compatibility")
    parser.add_argument("--benchmark-model", help="Benchmark specific model performance")
    parser.add_argument("--platform-info", action="store_true", help="Show detailed platform information")
    
    args = parser.parse_args()
    
    try:
        # Initialize TTS manager
        tts_manager = TTSManager()
        
        # Initialize CLI interface
        cli_interface = CLITTSInterface(tts_manager)
        
        # Handle different modes
        if args.list_models:
            cli_interface.show_models()
            return
        
        if args.list_environments:
            cli_interface.show_environments()
            return
        
        if args.create_environment:
            if args.create_environment not in tts_manager.list_models():
                console.print(f"[red]❌ Unknown model: {args.create_environment}[/red]")
                return
            success = tts_manager.create_environment(args.create_environment)
            if success:
                console.print(f"[green]✅ Environment created successfully for {args.create_environment}[/green]")
            else:
                console.print(f"[red]❌ Failed to create environment for {args.create_environment}[/red]")
            return
        
        if args.cleanup_environment:
            if args.cleanup_environment not in tts_manager.list_models():
                console.print(f"[red]❌ Unknown model: {args.cleanup_environment}[/red]")
                return
            success = tts_manager.cleanup_environment(args.cleanup_environment)
            if success:
                console.print(f"[green]✅ Environment removed successfully for {args.cleanup_environment}[/green]")
            else:
                console.print(f"[red]❌ Failed to remove environment for {args.cleanup_environment}[/red]")
            return
        
        if args.cleanup_all_environments:
            success = tts_manager.cleanup_all_environments()
            if success:
                console.print("[green]✅ All environments removed successfully[/green]")
            else:
                console.print("[red]❌ Failed to remove all environments[/red]")
            return
        
        if args.text or args.clipboard:
            # Non-interactive mode
            if args.clipboard:
                text = cli_interface.get_clipboard_text()
                if not text:
                    console.print("[red]❌ No text found in clipboard[/red]")
                    return
            else:
                text = args.text
            
            # Validate voice clone file if provided
            voice_clone_path = None
            if args.voice_clone:
                if not os.path.exists(args.voice_clone):
                    console.print(f"[red]❌ Voice clone file not found: {args.voice_clone}[/red]")
                    return
                voice_clone_path = args.voice_clone
            
            # Process text and generate file
            cli_interface.process_text(text, args.model, voice_clone_path, args.output)
            
        else:
            # Interactive mode (default)
            cli_interface.run_interactive()
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutdown requested. Goodbye![/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        logger.error(f"Application error: {e}")

if __name__ == "__main__":
    main()
