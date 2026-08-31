import time
import sys
from pathlib import Path

# Try to import pocket_tts
try:
    from pocket_tts import TTSModel
except ImportError:
    print("Error: pocket_tts not found in this environment.")
    print("Please run this script using the python executable inside .model-envs/pocket-tts-env/")
    sys.exit(1)

def benchmark():
    print("🚀 Benchmarking PocketTTS Internal (In-Process)...")
    
    t_start_import = time.time()
    # already imported above
    t_end_import = time.time()
    print(f"Import check overhead: {t_end_import - t_start_import:.4f}s")
    
    print("Loading model...")
    t0 = time.time()
    model = TTSModel.load_model()
    t1 = time.time()
    print(f"✅ Model Load time: {t1 - t0:.4f}s")
    
    text = "This is a benchmark to compare text to speech models."
    print(f"Text: '{text}'")
    
    # Pre-load voice state to isolate inference time
    print("Loading default voice state (alba)...")
    t0 = time.time()
    # Using a known HF path or fallback logic similar to the model code
    voice_path = "hf://kyutai/tts-voices/alba-mackenna/casual.wav"
    try:
        voice_state = model.get_state_for_audio_prompt(voice_path)
    except Exception as e:
        print(f"⚠️ Failed to load voice from HF: {e}")
        # Try local fallback if available or mock
        sys.exit(1)
    t1 = time.time()
    print(f"Voice Load time: {t1 - t0:.4f}s")
    
    # Inference Loop
    times = []
    print(f"Running 5 iterations...")
    for i in range(5):
        t0 = time.perf_counter()
        audio = model.generate_audio(voice_state, text)
        t1 = time.perf_counter()
        duration = t1 - t0
        times.append(duration)
        print(f" Iteration {i+1}: {duration:.4f}s")
        
    avg = sum(times) / len(times)
    print(f"\n📊 Average Inference Time: {avg:.4f}s")
    print(f"⚡ Speed (approx words/sec): {len(text.split()) / avg:.1f}")

if __name__ == "__main__":
    benchmark()
