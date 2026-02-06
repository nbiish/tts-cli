
import soundfile as sf
import numpy as np
import sys

def create_messy(output="messy.wav"):
    data1, sr = sf.read("base_part1.wav")
    data2, _ = sf.read("base_part2.wav")
    
    # Ensure shapes match for addition by padding to the larger one
    max_babble_len = max(len(data1), len(data2))
    
    babble1 = np.pad(data1, (0, max_babble_len - len(data1)))
    babble2 = np.pad(data2, (0, max_babble_len - len(data2)))
    
    babble = np.roll(babble1, int(sr * 0.5)) + np.roll(babble2, int(sr * 0.3))
    babble = babble * 0.5
    
    # Pad to match length
    max_len = max(len(data1) + len(data2) + int(sr*2), len(babble))
    
    # Main speech: Part 1 + Silence + Part 2
    silence = np.zeros(int(sr * 2.0))
    speech = np.concatenate([data1, silence, data2])
    
    # Pad speech to max_len
    if len(speech) < max_len:
        speech = np.pad(speech, (0, max_len - len(speech)))
        
    # Resize babble to max_len (repeat if needed)
    if len(babble) < max_len:
        repeats = (max_len // len(babble)) + 1
        babble = np.tile(babble, repeats)[:max_len]
        
    # Generate "Traffic" Noise (Low frequency rumble + White noise)
    t = np.linspace(0, max_len/sr, max_len)
    rumble = np.sin(2 * np.pi * 50 * t) * 0.3 # 50Hz hum
    white = np.random.normal(0, 0.1, max_len)
    
    # Mix: Speech + Babble + Traffic + White
    # We want speech to be audible but "dirty"
    messy_audio = speech + (babble * 0.4) + (rumble * 0.2) + (white * 0.1)
    
    # Normalize
    messy_audio = messy_audio / np.max(np.abs(messy_audio))
    
    sf.write(output, messy_audio, sr)
    print(f"Created {output}")

if __name__ == "__main__":
    create_messy()
