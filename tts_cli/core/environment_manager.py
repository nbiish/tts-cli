"""
Environment Manager - UV-based isolated environment management.

This module manages isolated UV environments for each TTS model to prevent
dependency conflicts following the tiered composition architecture.
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import os
import shutil


class EnvironmentManager:
    """Manages UV-based isolated environments for TTS models."""
    
    def __init__(self, base_path: Optional[Path] = None):
        if base_path is None:
            # Always find the project root by looking for pyproject.toml
            current_dir = Path(__file__).parent
            project_root = None
            
            # Walk up the directory tree looking for pyproject.toml
            while current_dir != current_dir.parent:
                if (current_dir / "pyproject.toml").exists():
                    project_root = current_dir
                    break
                current_dir = current_dir.parent
            
            if project_root:
                # Platform-safe env location. WSL checkouts on a Windows
                # drive (/mnt/*) cannot host venvs reliably (drvfs symlinks,
                # slow 9p I/O) — redirect those to ~/.tts-cli/model-envs.
                override = os.environ.get("TTS_CLI_MODEL_ENVS_DIR")
                if override:
                    self.base_path = Path(override).expanduser().resolve()
                elif self._is_wsl_windows_drive(project_root):
                    self.base_path = Path.home() / ".tts-cli" / "model-envs"
                    print(
                        "ℹ️  WSL Windows-drive checkout detected; model envs "
                        f"redirected to {self.base_path} "
                        "(set TTS_CLI_MODEL_ENVS_DIR to override)."
                    )
                else:
                    # Always use the project root's .model-envs directory
                    self.base_path = project_root / ".model-envs"
                self.project_root = project_root
            else:
                # Fallback if project root not found (shouldn't happen in normal usage)
                home_dir = Path.home()
                self.base_path = home_dir / ".tts-cli" / "model-envs"
                self.project_root = None
        else:
            self.base_path = base_path
            self.project_root = None
        
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._environment_configs = self._load_configs()
    
    @staticmethod
    def _is_wsl_windows_drive(path: Path) -> bool:
        """True when `path` sits on a Windows drive mounted inside WSL (/mnt/*)."""
        try:
            resolved = path.resolve()
            if not resolved.is_relative_to(Path("/mnt")):
                return False
            proc_version = Path("/proc/version")
            if proc_version.exists():
                return "microsoft" in proc_version.read_text(errors="ignore").lower()
        except Exception:
            pass
        return False

    def _load_configs(self) -> Dict[str, Dict]:
        """Load environment configurations from config file."""
        config_file = self.base_path / "environments.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}
    
    def _save_configs(self) -> None:
        """Save environment configurations to config file."""
        config_file = self.base_path / "environments.json"
        with open(config_file, 'w') as f:
            json.dump(self._environment_configs, f, indent=2)
    
    def create_environment(self, model_name: str, dependencies: List[str]) -> bool:
        """Create an isolated UV environment for a model."""
        env_path = self.base_path / f"{model_name}-env"
        
        try:
            # Create environment directory
            env_path.mkdir(exist_ok=True)
            
            # Per-model Python version pinning. Some engines require a Python
            # version outside the host project's range (e.g. IndexTTS needs
            # >=3.10,<3.12 while this project targets >=3.12).
            model_python_versions = {
                "kitten-tts": "3.11",  # KittenTTS (ONNX) tested on 3.11
            }
            python_version = model_python_versions.get(model_name)
            
            # A globally exported UV_PROJECT_ENVIRONMENT (e.g. a stale
            # per-project cache path) must not leak into these isolated
            # per-model environments.
            uv_env = {
                k: v for k, v in os.environ.items()
                if k != "UV_PROJECT_ENVIRONMENT"
            }

            # Initialize UV environment
            venv_cmd = ["uv", "venv", "--clear", str(env_path / ".venv")]
            if python_version:
                venv_cmd += ["--python", python_version]
            result = subprocess.run(
                venv_cmd, capture_output=True, text=True, check=True, env=uv_env
            )
            
            # Install dependencies: one resolver pass, streaming output
            # (capturing hides progress, so a stall looks like a hang)
            # with a hard timeout.
            venv_python = env_path / ".venv" / "bin" / "python"
            if not venv_python.exists():
                venv_python = env_path / ".venv" / "Scripts" / "python.exe"
            
            install = subprocess.run(
                ["uv", "pip", "install", *dependencies, "--python", str(venv_python)],
                text=True,
                timeout=900,
                env=uv_env,
            )
            if install.returncode != 0:
                raise subprocess.CalledProcessError(install.returncode, install.args)
            
            # Save configuration
            self._environment_configs[model_name] = {
                "path": str(env_path),
                "dependencies": dependencies,
                "created": True
            }
            self._save_configs()
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Failed to create environment for {model_name}: {e}")
            if getattr(e, "stderr", None):
                print(str(e.stderr)[-2000:])
            if env_path.exists():
                shutil.rmtree(env_path)
            return False
        except subprocess.TimeoutExpired as e:
            print(f"Timed out creating environment for {model_name}: {e}")
            if env_path.exists():
                shutil.rmtree(env_path)
            return False
        except Exception as e:
            print(f"Unexpected error creating environment for {model_name}: {e}")
            return False
    
    def get_environment_path(self, model_name: str) -> Optional[Path]:
        """Get the path to a model's environment."""
        if model_name in self._environment_configs:
            path_str = self._environment_configs[model_name]["path"]
            path = Path(path_str)
            # If path is relative, make it relative to the project root
            if not path.is_absolute():
                if self.project_root:
                    # Always use project root for consistency
                    path = self.project_root / path
                else:
                    # Fallback to base_path
                    path = self.base_path / path
            return path
        return None
    
    def get_python_executable(self, model_name: str) -> Optional[Path]:
        """Get the Python executable for a model's environment."""
        env_path = self.get_environment_path(model_name)
        if not env_path:
            return None

        # Try .venv structure first (standard venv)
        venv_python = env_path / ".venv" / "bin" / "python"
        if venv_python.exists():
            return venv_python

        venv_python = env_path / ".venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            return venv_python

        # Try direct structure (uv style)
        direct_python = env_path / "bin" / "python"
        if direct_python.exists():
            return direct_python

        direct_python_exe = env_path / "Scripts" / "python.exe"
        if direct_python_exe.exists():
            return direct_python_exe

        return None
    
    def environment_exists(self, model_name: str) -> bool:
        """Check if an environment exists for a model."""
        env_path = self.get_environment_path(model_name)
        return env_path and env_path.exists()
    
    def list_environments(self) -> List[Dict[str, str]]:
        """List all available environments."""
        environments = []
        for model_name, config in self._environment_configs.items():
            env_path = Path(config["path"])
            status = "Available" if env_path.exists() else "Missing"
            environments.append({
                "model": model_name,
                "path": str(env_path),
                "status": status,
                "dependencies": ", ".join(config.get("dependencies", []))
            })
        return environments
    
    def cleanup_environment(self, model_name: str) -> bool:
        """Remove an environment for a model."""
        try:
            env_path = self.get_environment_path(model_name)
            if env_path and env_path.exists():
                shutil.rmtree(env_path)
            
            if model_name in self._environment_configs:
                del self._environment_configs[model_name]
                self._save_configs()
            
            return True
        except Exception as e:
            print(f"Failed to cleanup environment for {model_name}: {e}")
            return False
    
    def cleanup_all_environments(self) -> bool:
        """Remove all environments."""
        try:
            if self.base_path.exists():
                shutil.rmtree(self.base_path)
            self.base_path.mkdir(exist_ok=True)
            self._environment_configs = {}
            self._save_configs()
            return True
        except Exception as e:
            print(f"Failed to cleanup all environments: {e}")
            return False
    
    def test_environment(self, model_name: str) -> Tuple[bool, str]:
        """Test if an environment is working correctly."""
        python_exec = self.get_python_executable(model_name)
        if not python_exec:
            return False, f"Python executable not found for {model_name}"
        
        try:
            # Test basic Python execution
            result = subprocess.run([
                str(python_exec), "-c", "import sys; print('Python working')"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return True, "Environment working correctly"
            else:
                return False, f"Python execution failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Environment test timed out"
        except Exception as e:
            return False, f"Environment test failed: {e}"


# Global environment manager instance
env_manager = EnvironmentManager()
