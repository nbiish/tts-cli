
import numpy as np
import soundfile as sf
import sys

def generate_noisy_speech(filename="test_input.wav", duration=10, sample_rate=16000):
    print(f"Generating synthetic audio: {filename}")
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # 1. Create "Speech" (Harmonic series to mimic voice)
    # Fundamental frequency 120Hz (male voice range)
    f0 = 120
    speech = np.sin(2 * np.pi * f0 * t)
    for k in range(2, 6):
        speech += (1/k) * np.sin(2 * np.pi * f0 * k * t)
    
    # Modulate amplitude to mimic syllables (2Hz envelope)
    envelope = 0.5 * (1 + np.sin(2 * np.pi * 2 * t))
    speech = speech * envelope
    
    # 2. Create "Noise" (White noise)
    noise = np.random.normal(0, 0.1, len(t))
    
    # 3. Create Silence regions (masking speech)
    # Silence at 0-2s, 4-6s, 8-10s
    # We want "Speech" only in active regions
    mask = np.zeros_like(t)
    mask[int(2*sample_rate):int(4*sample_rate)] = 1
    mask[int(6*sample_rate):int(8*sample_rate)] = 1
    
    # Mix: Speech only in active regions, Noise everywhere (simulating constant background)
    final_audio = (speech * mask) + (noise * 0.5)
    
    # Normalize
    final_audio = final_audio / np.max(np.abs(final_audio))
    
    # Save using soundfile
    sf.write(filename, final_audio, sample_rate)
    print("Done.")

if __name__ == "__main__":
    generate_noisy_speech()
