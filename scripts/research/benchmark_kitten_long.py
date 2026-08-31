import time
import sys
import soundfile as sf
import os
import numpy as np

# Long text sample (approx 3 paragraphs)
LONG_TEXT = """
In the heart of the ancient forest, where the trees whispered secrets to the wind, a hidden path revealed itself only to those who knew where to look. The sunlight filtered through the dense canopy, dappling the mossy ground in a shifting pattern of gold and green. Birds called out from high branches, their melodies weaving a complex tapestry of sound that seemed to guide the traveler deeper into the woods.

As the path wound its way down into the valley, the air grew cooler and the scent of pine and damp earth became stronger. A small stream bubbled alongside the trail, its clear waters rushing over smooth stones, carrying with it the stories of the mountains from which it came. It was a place of profound stillness, a sanctuary away from the noise and chaos of the world outside, where time seemed to slow down and breathe.

Suddenly, the trees parted to reveal a clearing, in the center of which stood an old stone circle. The stones were weathered and covered in lichen, standing as silent sentinels of a forgotten age. A sense of magic lingered here, faint but undeniable, a vibration in the air that made the skin prickle. It was here that the traveler stopped, listening not with their ears, but with their heart, waiting for the forest to speak its final truth.
"""

def benchmark_long():
    print("🚀 Benchmarking KittenTTS - Long Form Generation...")
    
    # Check dependencies
    try:
        from kittentts import KittenTTS
    except ImportError:
        print("Error: kittentts not found. Run with proper uv context.")
        sys.exit(1)

    print("Loading model (KittenML/kitten-tts-nano-0.1)...")
    t0 = time.time()
    try:
        # Load the default model (KittenTTS library uses 0.1 by default)
        model = KittenTTS()  # Uses default model from library
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        sys.exit(1)
    t1 = time.time()
    print(f"✅ Model Load time: {t1 - t0:.4f}s")
    
    word_count = len(LONG_TEXT.split())
    print(f"\nInput Text: ~{word_count} words")
    print("-" * 50)
    print(LONG_TEXT.strip())
    print("-" * 50)

    # Benchmark Generation
    print("\nGenerating audio...")
    t_start = time.perf_counter()
    
    try:
        # Generate with specific voice (use one of the available voices)
        audio = model.generate(LONG_TEXT, voice='expr-voice-2-m')
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        sys.exit(1)
        
    t_end = time.perf_counter()
    duration = t_end - t_start
    
    # Calculate metrics
    audio_duration_sec = len(audio) / 24000  # 24kHz sample rate
    rtf = duration / audio_duration_sec  # Real Time Factor (lower is better)
    
    print("\n📊 Results:")
    print(f"  Generation Time: {duration:.4f}s")
    print(f"  Audio Duration:  {audio_duration_sec:.2f}s")
    print(f"  RTF:             {rtf:.4f} (Process time / Audio duration)")
    print(f"  Speed:           {word_count / duration:.1f} words/sec")
    
    # Save output
    output_file = "benchmark_kitten_long.wav"
    sf.write(output_file, audio, 24000)
    print(f"\n💾 Saved to: {output_file}")
    
    # Verify file size
    size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"  File Size:       {size_mb:.2f} MB")

if __name__ == "__main__":
    benchmark_long()
