#!/usr/bin/env python3
"""
Benchmark Script for TTS CLI
Measures execution time of the CLI tool.
"""

import subprocess
import time
import sys
import os
import statistics
import argparse

def run_benchmark(iterations=3, text="Hello world", script_path=None):
    print(f"🚀 Benchmarking TTS CLI ({iterations} iterations)...")
    print(f"Text: '{text}'")
    
    # Locate the global wrapper script or use direct python invocation
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_path:
        wrapper_script = script_path
        # Check if it's a python script or shell script
        if wrapper_script.endswith(".py"):
            cmd = ["python3", wrapper_script]
        else:
            cmd = [wrapper_script]
    else:
        wrapper_script = os.path.join(script_dir, "tts-cli-wrapper.py")
        cmd = ["python3", wrapper_script]
    
    cmd.extend(["--text", text, "--output", "bench_test.wav"])
    print(f"Command: {' '.join(cmd)}")
    
    times = []
    
    for i in range(iterations):
        
        start_time = time.perf_counter()
        try:
            # We use check=True to ensure it actually worked
            # We capture output to avoid cluttering, but print if error
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Error: {result.stderr}")
                continue
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            continue
            
        end_time = time.perf_counter()
        duration = end_time - start_time
        times.append(duration)
        print(f" {duration:.4f}s")
        
    if not times:
        print("❌ All runs failed.")
        return

    avg_time = statistics.mean(times)
    min_time = min(times)
    max_time = max(times)
    
    print("\n📊 Results:")
    print(f"  Average: {avg_time:.4f}s")
    print(f"  Min:     {min_time:.4f}s")
    print(f"  Max:     {max_time:.4f}s")
    
    # Clean up
    if os.path.exists("bench_test.wav"):
        os.remove("bench_test.wav")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark TTS CLI")
    parser.add_argument("--script", help="Path to script to benchmark")
    parser.add_argument("--text", default="Benchmark test for speed.", help="Text to synthesize")
    parser.add_argument("--iterations", type=int, default=3, help="Number of iterations")
    args = parser.parse_args()
    
    run_benchmark(iterations=args.iterations, text=args.text, script_path=args.script)
