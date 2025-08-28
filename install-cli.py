#!/usr/bin/env python3
"""
TTS CLI Global Installer
========================

This script installs the TTS CLI tool globally so users can access
the 'cli-tts' command from anywhere on their system.

It creates:
1. A global entry point script
2. Adds the script to PATH (if possible)
3. Provides manual PATH instructions if needed

Usage:
    python install-cli.py [--user] [--force]

Requirements:
    - Python 3.10+ installed
    - TTS CLI already set up (run setup.py first)
"""

import os
import sys
import shutil
import argparse
import subprocess
from pathlib import Path
import platform


class TTSCLIGlobalInstaller:
    """Installer for making TTS CLI globally accessible."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.cli_module = "tts_cli.cli_tts"
        self.command_name = "cli-tts"
        
        # Determine system-specific paths
        self.system = platform.system().lower()
        self.is_windows = self.system == "windows"
        self.is_macos = self.system == "darwin"
        self.is_linux = self.system == "linux"
        
    def get_install_paths(self):
        """Get appropriate installation paths for the current system."""
        paths = []
        
        if self.is_windows:
            # Windows: Add to user's PATH or system PATH
            if os.environ.get('APPDATA'):
                paths.append(Path(os.environ['APPDATA']) / 'Python' / 'Scripts')
            if os.environ.get('LOCALAPPDATA'):
                paths.append(Path(os.environ['LOCALAPPDATA']) / 'Python' / 'Scripts')
            paths.append(Path('C:/Python/Scripts'))
            
        elif self.is_macos:
            # macOS: User's local bin directory
            home = Path.home()
            paths.extend([
                home / '.local' / 'bin',
                home / 'bin',
                Path('/usr/local/bin'),
                Path('/opt/homebrew/bin')  # Apple Silicon Homebrew
            ])
            
        else:  # Linux and others
            home = Path.home()
            paths.extend([
                home / '.local' / 'bin',
                home / 'bin',
                Path('/usr/local/bin'),
                Path('/usr/bin')
            ])
            
        return paths
    
    def find_available_path(self):
        """Find the first available path for installation."""
        paths = self.get_install_paths()
        
        for path in paths:
            if path.exists() or self.can_create_directory(path):
                return path
                
        return None
    
    def can_create_directory(self, path):
        """Check if we can create a directory at the given path."""
        try:
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                return True
            return path.is_dir() and os.access(path, os.W_OK)
        except (OSError, PermissionError):
            return False
    
    def create_entry_point_script(self, install_path):
        """Create the entry point script."""
        if self.is_windows:
            # Use the project's virtual environment Python with absolute paths
            project_venv_python = self.project_root / ".venv" / "Scripts" / "python.exe"
            project_root = self.project_root
            script_content = f'''@echo off
REM TTS CLI Entry Point
set PYTHONPATH={project_root};%PYTHONPATH%
"{project_venv_python}" -m {self.cli_module} %*
'''
            script_path = install_path / f"{self.command_name}.bat"
        else:
            # Use the project's virtual environment Python with absolute paths
            project_venv_python = self.project_root / ".venv" / "bin" / "python"
            project_root = self.project_root
            script_content = f'''#!/bin/bash
# TTS CLI Entry Point
export PYTHONPATH="{project_root}:$PYTHONPATH"
exec "{project_venv_python}" -m {self.cli_module} "$@"
'''
            script_path = install_path / self.command_name
        
        try:
            # Write the script
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            # Make executable on Unix systems
            if not self.is_windows:
                script_path.chmod(0o755)
            
            return script_path
        except Exception as e:
            print(f"❌ Failed to create entry point script: {e}")
            return None
    
    def add_to_path(self, install_path):
        """Attempt to add the install path to PATH."""
        if self.is_windows:
            return self.add_to_path_windows(install_path)
        else:
            return self.add_to_path_unix(install_path)
    
    def add_to_path_windows(self, install_path):
        """Add path to Windows PATH environment variable."""
        try:
            # Get current PATH
            current_path = os.environ.get('PATH', '')
            path_parts = current_path.split(os.pathsep)
            
            # Check if already in PATH
            if str(install_path) in path_parts:
                print(f"✅ Path already in PATH: {install_path}")
                return True
            
            # Add to PATH
            new_path = os.pathsep.join([str(install_path)] + path_parts)
            
            # Try to set for current session
            os.environ['PATH'] = new_path
            
            print(f"✅ Added to PATH for current session: {install_path}")
            print("⚠️  For permanent PATH changes, you may need to:")
            print("   1. Open System Properties > Environment Variables")
            print(f"   2. Add {install_path} to your PATH")
            
            return True
            
        except Exception as e:
            print(f"⚠️  Could not modify PATH: {e}")
            return False
    
    def add_to_path_unix(self, install_path):
        """Add path to Unix PATH environment variable."""
        try:
            # Get shell configuration files
            home = Path.home()
            shell_configs = []
            
            if os.path.exists(home / '.bashrc'):
                shell_configs.append(home / '.bashrc')
            if os.path.exists(home / '.zshrc'):
                shell_configs.append(home / '.zshrc')
            if os.path.exists(home / '.profile'):
                shell_configs.append(home / '.profile')
            if os.path.exists(home / '.bash_profile'):
                shell_configs.append(home / '.bash_profile')
            
            if not shell_configs:
                print("⚠️  No shell configuration files found")
                return False
            
            # Check if already in PATH
            current_path = os.environ.get('PATH', '')
            if str(install_path) in current_path.split(':'):
                print(f"✅ Path already in PATH: {install_path}")
                return True
            
            # Add to first available shell config
            config_file = shell_configs[0]
            path_export = f'\n# TTS CLI PATH\nexport PATH="{install_path}:$PATH"\n'
            
            with open(config_file, 'a') as f:
                f.write(path_export)
            
            print(f"✅ Added to {config_file}: {install_path}")
            print(f"⚠️  Please restart your terminal or run: source {config_file}")
            
            # Also add to current session
            os.environ['PATH'] = f"{install_path}:{current_path}"
            
            return True
            
        except Exception as e:
            print(f"⚠️  Could not modify shell configuration: {e}")
            return False
    
    def verify_installation(self, script_path):
        """Verify that the CLI command is working."""
        try:
            # Test the command
            if self.is_windows:
                result = subprocess.run([str(script_path), "--help"], 
                                      capture_output=True, text=True, timeout=10)
            else:
                result = subprocess.run([str(script_path), "--help"], 
                                      capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print("✅ CLI command verification successful!")
                return True
            else:
                print(f"⚠️  CLI command may have issues: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("⚠️  CLI command timed out during verification")
            return False
        except Exception as e:
            print(f"❌ CLI command verification failed: {e}")
            return False
    
    def install(self, user_only=False, force=False):
        """Perform the global installation."""
        print("🚀 TTS CLI Global Installer")
        print("=" * 40)
        
        # Check if TTS CLI is set up
        if not (self.project_root / ".venv").exists():
            print("❌ TTS CLI not set up. Please run 'python setup.py' first.")
            return False
        
        # Find installation path
        install_path = self.find_available_path()
        if not install_path:
            print("❌ No suitable installation path found")
            print("Available paths:")
            for path in self.get_install_paths():
                status = "✅ Available" if path.exists() else "❌ Not available"
                print(f"  {path}: {status}")
            return False
        
        print(f"📁 Installing to: {install_path}")
        
        # Create entry point script
        script_path = self.create_entry_point_script(install_path)
        if not script_path:
            return False
        
        print(f"✅ Entry point script created: {script_path}")
        
        # Add to PATH
        if not user_only:
            self.add_to_path(install_path)
        
        # Verify installation
        if self.verify_installation(script_path):
            print("\n🎉 Installation Complete!")
            print(f"\n📋 Usage:")
            print(f"  {self.command_name} --help")
            print(f"  {self.command_name} --list-models")
            print(f"  {self.command_name} --text 'Hello' --model edge-tts")
            
            if not user_only:
                print(f"\n✅ The '{self.command_name}' command is now available globally!")
                print(f"📁 Installed at: {script_path}")
            else:
                print(f"\n⚠️  The '{self.command_name}' command is installed but may not be in PATH")
                print(f"📁 You can run it directly from: {script_path}")
            
            return True
        else:
            print("❌ Installation verification failed")
            return False
    
    def uninstall(self):
        """Remove the global CLI command."""
        print("🧹 TTS CLI Global Uninstaller")
        print("=" * 40)
        
        # Find and remove entry point scripts
        install_paths = self.get_install_paths()
        removed = False
        
        for install_path in install_paths:
            if self.is_windows:
                script_path = install_path / f"{self.command_name}.bat"
            else:
                script_path = install_path / self.command_name
            
            if script_path.exists():
                try:
                    script_path.unlink()
                    print(f"✅ Removed: {script_path}")
                    removed = True
                except Exception as e:
                    print(f"⚠️  Could not remove {script_path}: {e}")
        
        if removed:
            print("\n✅ Uninstallation complete!")
            print("⚠️  Note: PATH modifications may need manual cleanup")
        else:
            print("ℹ️  No CLI commands found to remove")
        
        return removed


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="TTS CLI Global Installer")
    parser.add_argument("--user", action="store_true", 
                       help="Install for current user only (don't modify PATH)")
    parser.add_argument("--force", action="store_true", 
                       help="Force installation even if command exists")
    parser.add_argument("--uninstall", action="store_true", 
                       help="Uninstall the global CLI command")
    
    args = parser.parse_args()
    
    installer = TTSCLIGlobalInstaller()
    
    if args.uninstall:
        success = installer.uninstall()
    else:
        success = installer.install(user_only=args.user, force=args.force)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
