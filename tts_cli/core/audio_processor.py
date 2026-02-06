"""
Audio Processor - Handles audio preprocessing tasks (Demucs, VAD).

This module manages the execution of audio processing tasks in an isolated
environment to handle heavy dependencies like PyTorch and Demucs.
"""

import sys
import subprocess
from pathlib import Path
from typing import Optional, List
import shutil
import time

from .environment_manager import env_manager


class AudioProcessor:
    """Handles audio processing operations."""
    
    def __init__(self):
        self.env_name = "audio-processing"
        self.python_executable = env_manager.get_python_executable(self.env_name)
        self.is_available = self.python_executable is not None

    def check_availability(self) -> bool:
        """Check if audio processing environment is available."""
        self.python_executable = env_manager.get_python_executable(self.env_name)
        return self.python_executable is not None

    def isolate_voice(self, input_path: str, output_path: str) -> bool:
        """
        Isolate voice from audio using Demucs.
        
        Args:
            input_path: Path to input audio file
            output_path: Path where the isolated vocal track should be saved
            
        Returns:
            bool: True if successful
        """
        if not self.check_availability():
            print("Audio processing environment not found.")
            return False
            
        print(f"Isolating voice from {input_path} using Demucs...")
        
        # Create a temporary directory for Demucs output
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            # We use a simple python script to run demucs to ensure we use the env's context
            # relying on 'demucs' being installed as a module or bin in the env
            
            # Demucs output structure is usually: <out>/htdemucs/<track_name>/vocals.wav
            
            script = f"""
import sys
import subprocess
from pathlib import Path

def run_demucs():
    input_file = "{input_path}"
    out_dir = "{temp_dir}"
    
    # Run demucs command
    # We assume 'demucs' is in the path of the current python environment or accessible via module
    # Actually, easiest is to run it via 'python -m demucs'
    
    cmd = [sys.executable, "-m", "demucs", "--two-stems=vocals", "-n", "htdemucs", "-o", out_dir, input_file]
    
    print(f"Running Demucs: {{' '.join(cmd)}}")
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Demucs failed: {{e}}")
        return False

if __name__ == "__main__":
    success = run_demucs()
    sys.exit(0 if success else 1)
"""
            
            success = self._execute_in_environment(script)
            
            if success:
                # Locate the output file
                # Demucs creates a folder with the name of the track
                input_filename = Path(input_path).stem
                expected_output = Path(temp_dir) / "htdemucs" / input_filename / "vocals.wav"
                
                if expected_output.exists():
                    # Move to destination
                    shutil.copy2(expected_output, output_path)
                    print(f"✅ Voice isolated successfully: {output_path}")
                    return True
                else:
                    print(f"❌ Could not find Demucs output at {expected_output}")
                    # Debug: list files
                    print(f"Contents of {temp_dir}:")
                    for p in Path(temp_dir).rglob("*"):
                        print(f"  {p}")
                    return False
            else:
                return False

    def remove_silence(self, input_path: str, output_path: str) -> bool:
        """
        Remove silence from audio using VAD.
        
        Args:
            input_path: Path to input audio file
            output_path: Path where the cleaned audio should be saved
            
        Returns:
            bool: True if successful
        """
        if not self.check_availability():
            print("Audio processing environment not found.")
            return False
            
        print(f"Removing silence from {input_path} using Silero VAD...")
        
        script = f"""
import torch
import torchaudio
from pathlib import Path

def remove_silence_vad():
    input_path = "{input_path}"
    output_path = "{output_path}"
    
    print(f"Loading VAD model...")
    model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                  model='silero_vad',
                                  force_reload=False,
                                  onnx=False)
    
    (get_speech_timestamps,
     save_audio,
     read_audio,
     VADIterator,
     collect_chunks) = utils
    
    print(f"Reading audio...")
    wav = read_audio(input_path, sampling_rate=16000)
    
    # Get speech timestamps
    print(f"Detecting speech...")
    speech_timestamps = get_speech_timestamps(wav, model, sampling_rate=16000)
    
    if not speech_timestamps:
        print("No speech detected!")
        # Fallback: copy original? Or fail?
        # Let's fail for now or copy original if strict
        # Ideally we prefer to save original if VAD fails to find speech to avoid empty file
        return False
        
    # Merge chunks
    print(f"Merging {{len(speech_timestamps)}} speech chunks...")
    save_audio(output_path,
               collect_chunks(speech_timestamps, wav), 
               sampling_rate=16000)
               
    return True

if __name__ == "__main__":
    try:
        success = remove_silence_vad()
        if success:
            print("VAD processing complete.")
        else:
            print("VAD processing failed or no speech detected.")
            # If no speech, maybe we should just copy the file?
            # For now let's report failure
            import sys
            sys.exit(1)
    except Exception as e:
        print(f"Error during VAD: {{e}}")
        import sys
        sys.exit(1)
"""
        return self._execute_in_environment(script)

    def _execute_in_environment(self, script_content: str) -> bool:
        """Execute python script in the isolated environment."""
        if not self.python_executable:
            return False
            
        import tempfile
        import os
        
        # Create temp script
        fd, script_path = tempfile.mkstemp(suffix=".py", text=True)
        try:
            with os.fdopen(fd, 'w') as f:
                f.write(script_content)
                
            # Run
            result = subprocess.run(
                [str(self.python_executable), script_path],
                capture_output=False,  # Let output flow to stdout/stderr
                check=False
            )
            
            return result.returncode == 0
            
        finally:
            # Cleanup
            if os.path.exists(script_path):
                os.unlink(script_path)

# Global instance
audio_processor = AudioProcessor()
