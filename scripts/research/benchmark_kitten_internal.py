import time
import sys
import soundfile as sf
import os

# Try to import kittentts
try:
    from kittentts import KittenTTS
except ImportError:
    print("Error: kittentts not found.")
    sys.exit(1)

def benchmark():
    print("🚀 Benchmarking KittenTTS Internal (In-Process)...")
    
    print("Loading model (KittenML/kitten-tts-nano-0.8-int8)...")
    t0 = time.time()
    try:
        model = KittenTTS("KittenML/kitten-tts-nano-0.8-int8")
    except Exception as e:
        print(f"❌ Failed to load KittenTTS model: {e}")
        sys.exit(1)
    t1 = time.time()
    print(f"✅ Model Load time: {t1 - t0:.4f}s")
    
    text = "This is a benchmark to compare text to speech models."
    print(f"Text: '{text}'")
    
    # Inference Loop
    times = []
    print(f"Running 5 iterations...")
    for i in range(5):
        t0 = time.perf_counter()
        try:
            # Using 'Jasper' as suggested in docs
            audio = model.generate(text, voice='Jasper')
        except Exception as e:
            print(f"❌ Inference failed: {e}")
            break
            
        t1 = time.perf_counter()
        duration = t1 - t0
        times.append(duration)
        print(f" Iteration {i+1}: {duration:.4f}s")
        
    if times:
        avg = sum(times) / len(times)
        print(f"\n📊 Average Inference Time: {avg:.4f}s")
        print(f"⚡ Speed (approx words/sec): {len(text.split()) / avg:.1f}")
    else:
        print("No successful iterations.")

if __name__ == "__main__":
    benchmark()
