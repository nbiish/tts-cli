#!/usr/bin/env python3
"""
Global TTS CLI Wrapper Script

This script provides a reliable way to run the TTS CLI from anywhere on the system.
"""

import sys
import os
import subprocess

def find_python_with_tts_cli():
    """Find a Python executable that has the tts_cli module installed."""
    # Try common Python locations where the module might be installed
    python_candidates = [
        # Common Conda locations
        os.path.expanduser("~/miniconda3/bin/python"),
        os.path.expanduser("~/anaconda3/bin/python"),
        # System locations
        "/usr/local/bin/python3",
        "/opt/homebrew/bin/python3",
        "python3",
        "python"
    ]
    
    for python_path in python_candidates:
        try:
            # Check if this Python has the tts_cli module
            result = subprocess.run(
                [python_path, "-c", "import tts_cli.cli"], 
                capture_output=True, 
                check=False
            )
            if result.returncode == 0:
                return python_path
        except (FileNotFoundError, subprocess.SubprocessError):
            continue
    
    return None

def main():
    """Run the TTS CLI module."""
    try:
        # Find the correct Python executable
        python_path = find_python_with_tts_cli()
        if not python_path:
            print("Error: Could not find Python installation with tts_cli module.")
            print("Please ensure the TTS CLI is properly installed.")
            sys.exit(1)
        
        # Use the found Python to run the module
        cmd = [python_path, "-m", "tts_cli.cli"] + sys.argv[1:]
        result = subprocess.run(cmd, check=False)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(130)
    except subprocess.SubprocessError as e:
        print(f"Error running TTS CLI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()