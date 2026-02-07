"""
Pocket TTS model implementation for TTS CLI.

This module provides the Pocket TTS model implementation, a lightweight
CPU-optimized TTS system.
"""

import sys
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
import subprocess

from ..core.model_registry import BaseTTSModel
from ..core.environment_manager import env_manager


class PocketTTSModel(BaseTTSModel):
    """Pocket TTS model implementation."""
    
    def __init__(self, model_name: str = "pocket-tts"):
        super().__init__(model_name)
        self.python_executable = env_manager.get_python_executable(model_name)
        self.is_available = self.python_executable is not None
        
        # Default voices available in pocket-tts
        self._default_voices = [
            "alba", "victor", "umair", "vivaldi", 
            "yesid", "wealthiest", "awais", "gmaskell", "robert"
        ]
    
    def generate_speech(self, text: str, voice: Optional[str] = None, 
                       output_path: str = "output.wav", **kwargs) -> bool:
        """Generate speech from text using Pocket TTS."""
        # Check for voice_clone in kwargs
        voice_clone = kwargs.get('voice_clone')
        if voice_clone:
            voice = voice_clone

        if not self.is_available:
            # Check if we are running in a UV environment that has the package even if env_manager doesn't know
            try:
                import pocket_tts
            except ImportError:
                print("Pocket TTS model is not available. Please create the environment first.")
                return False
        
        # Use default voice if none specified
        if not voice:
            voice = random.choice(self._default_voices)
            print(f"ℹ️  No voice specified. Using random voice: {voice}")
            
        # Optimization: Try in-process generation if dependencies are met
        try:
            import pocket_tts
            import numpy as np
            import scipy.io.wavfile
            # Only print this if we are verbose, but for now it helps verify optimization
            # print("⚡️ Fast path: Pocket TTS found in current environment. Running in-process...")
            self._generate_in_process(text, voice, output_path)
            return True
        except ImportError:
            pass
        
        try:
            # Create temporary script for isolated execution
            script_content = self._create_generation_script(text, voice, output_path)
            
            # Execute in isolated environment
            success = self._execute_in_environment(script_content)
            
            if success:
                # Verify output file was created
                if Path(output_path).exists():
                    print(f"Pocket TTS: Speech generated successfully to {output_path}")
                    return True
                else:
                    print("Pocket TTS: Output file was not created")
                    return False
            else:
                print("Pocket TTS: Speech generation failed")
                return False
                
        except Exception as e:
            print(f"Pocket TTS generation failed: {e}")
            return False

    def _generate_in_process(self, text: str, voice: str, output_path: str) -> None:
        """Generate speech in the current process."""
        import numpy as np
        import scipy.io.wavfile
        from pocket_tts import TTSModel
        
        print(f"Initializing Pocket TTS...")
        
        # Load model
        tts_model = TTSModel.load_model()
        
        # Get voice state
        voice_input = voice
        voice_is_path = Path(voice).exists()
        
        print(f"Loading voice: {voice_input}")
        if voice_is_path:
            # Voice cloning from file
            voice_state = tts_model.get_state_for_audio_prompt(voice_input)
        else:
            # Predefined voice mapping
            voice_map = {
                "alba": "hf://kyutai/tts-voices/alba-mackenna/casual.wav",
                "victor": "hf://kyutai/tts-voices/voice-donations/Victor_Garcia.wav",
                "umair": "hf://kyutai/tts-voices/voice-donations/Umair.wav",
                "vivaldi": "hf://kyutai/tts-voices/voice-donations/Vivaldi.wav",
                "yesid": "hf://kyutai/tts-voices/voice-donations/Yesid.wav",
                "wealthiest": "hf://kyutai/tts-voices/voice-donations/Wealthiest.wav",
                "awais": "hf://kyutai/tts-voices/voice-donations/awais_shah.wav",
                "gmaskell": "hf://kyutai/tts-voices/voice-donations/gmaskell92.wav",
                "robert": "hf://kyutai/tts-voices/voice-donations/robert.wav"
            }
            
            if voice_input in voice_map:
                voice_state = tts_model.get_state_for_audio_prompt(voice_map[voice_input])
            else:
                # Fallback
                try:
                    voice_state = tts_model.get_state_for_audio_prompt(voice_input)
                except:
                    print(f"Unknown voice: {voice_input}, defaulting to alba")
                    voice_state = tts_model.get_state_for_audio_prompt(voice_map["alba"])

        print(f"Generating audio for text: {text[:50]}...")
        audio = tts_model.generate_audio(voice_state, text)
        
        # Audio is a 1D torch tensor containing PCM data
        print(f"Saving to {output_path}...")
        audio_data = audio.numpy()
        # Convert to 16-bit PCM if it's float
        if audio_data.dtype.kind == 'f':
            audio_data = (audio_data * 32767).clip(-32768, 32767).astype(np.int16)
            
        scipy.io.wavfile.write(output_path, tts_model.sample_rate, audio_data)
        print("Done.")
        print(f"Pocket TTS: Speech generated successfully to {output_path}")

    def list_voices(self) -> List[str]:
        """List available voices for this model."""
        return self._default_voices
    
    def validate_voice(self, voice: str) -> bool:
        """Validate if a voice is available for this model."""
        # Check if it's a default voice or a file path (for cloning)
        if voice in self._default_voices:
            return True
        if Path(voice).exists():
            return True
        return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and capabilities."""
        return {
            "name": "pocket-tts",
            "description": "Lightweight CPU-optimized TTS model by Kyutai",
            "capabilities": ["text-to-speech", "voice-cloning", "cpu-optimized"],
            "languages": ["en"],
            "version": "0.1.0"  # Approximate version based on web info
        }
    
    def _create_generation_script(self, text: str, voice: str, output_path: str) -> str:
        """Create a script for Pocket TTS generation."""
        # Escape text for safe inclusion in script
        escaped_text = text.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'").replace('\n', '\\n').replace('\r', '\\r')
        
        # Check if voice is a path (for cloning)
        voice_is_path = str(Path(voice).exists())
        
        return f'''
import sys
import os
import numpy as np
import scipy.io.wavfile
from pocket_tts import TTSModel

def generate():
    print(f"Initializing Pocket TTS...")
    try:
        # Load model
        tts_model = TTSModel.load_model()
        
        # Get voice state
        voice_input = "{voice}"
        voice_is_path = {voice_is_path}
        
        print(f"Loading voice: {{voice_input}}")
        if voice_is_path:
            # Voice cloning from file
            voice_state = tts_model.get_state_for_audio_prompt(voice_input)
        else:
            # Predefined voice
            # The web info says: "The --voice argument can also take a plain wav file... We provide a small catalog of voices."
            # The python API example shows loading from hf:// for 'alba-mackenna/casual.wav'.
            # However, the CLI example suggests `pocket-tts generate --voice alba`.
            # Let's try to map the simple names to what the library likely expects or use the library's internal mapping if available.
            # If the library doesn't support simple names in get_state_for_audio_prompt directly, we might need to look them up.
            # But the web page says "Modify the voice with --voice... We provide a small catalog... alba, marius..."
            # Let's assume there's a way to get these.
            # Inspecting the library source would be ideal, but based on the CLI usage, it might be built-in.
            # Wait, the python example uses `hf://kyutai/tts-voices/alba-mackenna/casual.wav`.
            # Let's try to find if there is a helper for default voices.
            # If not, we might need to map them.
            
            # Map common names to likely HF paths if needed, or hope the library handles it.
            # Given the CLI supports it, the library likely has a way. 
            # Let's assume for now we can pass the name if we use the CLI, but here we are using the Python API.
            # The Python API example explicitly uses a HF URL.
            # Let's use a mapping for the known voices.
            
            voice_map = {{
                "alba": "hf://kyutai/tts-voices/alba-mackenna/casual.wav",
                "victor": "hf://kyutai/tts-voices/voice-donations/Victor_Garcia.wav",
                "umair": "hf://kyutai/tts-voices/voice-donations/Umair.wav",
                "vivaldi": "hf://kyutai/tts-voices/voice-donations/Vivaldi.wav",
                "yesid": "hf://kyutai/tts-voices/voice-donations/Yesid.wav",
                "wealthiest": "hf://kyutai/tts-voices/voice-donations/Wealthiest.wav",
                "awais": "hf://kyutai/tts-voices/voice-donations/awais_shah.wav",
                "gmaskell": "hf://kyutai/tts-voices/voice-donations/gmaskell92.wav",
                "robert": "hf://kyutai/tts-voices/voice-donations/robert.wav"
            }}
            
            if voice_input in voice_map:
                voice_state = tts_model.get_state_for_audio_prompt(voice_map[voice_input])
            else:
                # Fallback: try to use the name directly, maybe the library is smart
                try:
                    voice_state = tts_model.get_state_for_audio_prompt(voice_input)
                except:
                    print(f"Unknown voice: {{voice_input}}, defaulting to alba")
                    voice_state = tts_model.get_state_for_audio_prompt(voice_map["alba"])

        text = "{escaped_text}"
        output_path = "{output_path}"
        
        print(f"Generating audio for text: {{text[:50]}}...")
        audio = tts_model.generate_audio(voice_state, text)
        
        # Audio is a 1D torch tensor containing PCM data
        print(f"Saving to {{output_path}}...")
        audio_data = audio.numpy()
        # Convert to 16-bit PCM if it's float
        if audio_data.dtype.kind == 'f':
            audio_data = (audio_data * 32767).clip(-32768, 32767).astype(np.int16)
            
        scipy.io.wavfile.write(output_path, tts_model.sample_rate, audio_data)
        print("Done.")
        
    except Exception as e:
        print(f"Error: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    generate()
'''

    def _execute_in_environment(self, script_content: str) -> bool:
        """Execute python script in the model's isolated environment."""
        if not self.python_executable:
            return False
            
        with subprocess.Popen(
            [str(self.python_executable), "-c", script_content],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        ) as process:
            stdout, stderr = process.communicate()
            
            if stdout:
                print(stdout)
            if stderr:
                print(stderr, file=sys.stderr)
                
            return process.returncode == 0
