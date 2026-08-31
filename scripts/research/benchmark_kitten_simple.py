import time
import sys
import soundfile as sf
import os

# Medium text sample (2 sentences)
MEDIUM_TEXT = """
In the heart of the ancient forest, a hidden path revealed itself only to those who knew where to look. The sunlight filtered through the dense canopy, dappling the mossy ground in a shifting pattern of gold and green.
"""

def benchmark_simple():
    print("🚀 Benchmarking KittenTTS - Medium Text Generation...")

    # Check dependencies
    try:
        from kittentts import KittenTTS
    except ImportError:
        print("Error: kittentts not found. Run with proper uv context.")
        sys.exit(1)

    print("Loading model (KittenML/kitten-tts-nano-0.1)...")
    t0 = time.time()
    try:
        # Load the default model
        model = KittenTTS()  # Uses default model from library
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        sys.exit(1)
    t1 = time.time()
    print(f"✅ Model Load time: {t1 - t0:.4f}s")

    word_count = len(MEDIUM_TEXT.split())
    print(f"\nInput Text: ~{word_count} words")
    print("-" * 50)
    print(MEDIUM_TEXT.strip())
    print("-" * 50)

    # Test with multiple voices
    voices = ['expr-voice-2-m', 'expr-voice-2-f', 'expr-voice-3-m', 'expr-voice-3-f']

    for voice in voices:
        print(f"\nTesting voice: {voice}")

        # Benchmark Generation
        print("Generating audio...")
        t_start = time.perf_counter()

        try:
            audio = model.generate(MEDIUM_TEXT, voice=voice)
        except Exception as e:
            print(f"❌ Generation failed for {voice}: {e}")
            continue

        t_end = time.perf_counter()
        duration = t_end - t_start

        # Calculate metrics
        audio_duration_sec = len(audio) / 24000  # 24kHz sample rate
        rtf = duration / audio_duration_sec  # Real Time Factor (lower is better)

        print(f"  Generation Time: {duration:.4f}s")
        print(f"  Audio Duration:  {audio_duration_sec:.2f}s")
        print(f"  RTF:             {rtf:.4f} (Process time / Audio duration)")
        print(f"  Speed:           {word_count / duration:.1f} words/sec")

        # Save output
        output_file = f"benchmark_kitten_{voice.replace('-', '_')}.wav"
        sf.write(output_file, audio, 24000)
        print(f"  💾 Saved to: {output_file}")

        # Verify file size
        size_mb = os.path.getsize(output_file) / (1024 * 1024)
        print(f"  File Size:       {size_mb:.2f} MB")

if __name__ == "__main__":
    benchmark_simple()
