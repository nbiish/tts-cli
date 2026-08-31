#!/usr/bin/env python3
"""
KittenTTS Maximum Text Length Test (Isolated Environment)

This script tests KittenTTS with progressively longer texts
to determine the actual limits and optimal constraints.
Uses the isolated KittenTTS environment.
"""

import sys
import os
import subprocess
from pathlib import Path

def test_kitten_with_isolated_env(text: str, test_name: str) -> dict:
    """Test KittenTTS with a specific text using isolated environment."""
    print(f"\n{'=' * 70}")
    print(f"TEST: {test_name}")
    print(f"{'=' * 70}")
    print(f"Text length: {len(text)} characters")
    print(f"Word count: {len(text.split())}")
    print(f"Text preview: {text[:100]}...")

    # Escape text for Python
    escaped_text = text.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'").replace('\n', '\\n')

    # Create test script
    script = f'''
import os
import sys
import time
os.environ['PHONEMIZER_ESPEAK_LIBRARY'] = '/opt/homebrew/lib/libespeak-ng.dylib'

try:
    from kittentts import KittenTTS
    import soundfile as sf

    print("Loading KittenTTS model...")
    t0 = time.time()
    model = KittenTTS()
    load_time = time.time() - t0
    print(f"Model loaded in {{load_time:.2f}}s")

    print("Generating audio...")
    t0 = time.time()
    audio = model.generate("{escaped_text}", voice='expr-voice-2-m')
    gen_time = time.time() - t0

    if audio is None:
        print("ERROR: Generated audio is None")
        sys.exit(1)

    audio_duration = len(audio) / 24000
    rtf = gen_time / audio_duration if audio_duration > 0 else 0

    output_file = "test_kitten_{test_name.lower().replace(' ', '_')}.wav"
    sf.write(output_file, audio, 24000)

    import pathlib
    file_size = pathlib.Path(output_file).stat().st_size / (1024 * 1024)

    print(f"SUCCESS")
    print(f"gen_time={{gen_time}}")
    print(f"audio_duration={{audio_duration}}")
    print(f"rtf={{rtf}}")
    print(f"file_size={{file_size}}")
    print(f"word_count={{len("{escaped_text}".split())}}")

except Exception as e:
    print(f"ERROR: {{type(e).__name__}}: {{str(e)[:200]}}")
    sys.exit(1)
'''

    # Find KittenTTS environment
    env_path = Path(".model-envs/kitten-tts-env/.venv/bin/python")
    if not env_path.exists():
        print(f"❌ KittenTTS environment not found")
        return {"success": False, "error": "Environment not found"}

    # Run script
    try:
        result = subprocess.run(
            [str(env_path), "-c", script],
            capture_output=True,
            text=True,
            timeout=120
        )

        output = result.stdout + result.stderr

        if "ERROR:" in output:
            error_line = [line for line in output.split('\n') if 'ERROR:' in line]
            if error_line:
                error_msg = error_line[0].split('ERROR:')[1].strip()
                print(f"❌ FAILED")
                print(f"   Error: {error_msg}")

                # Check for specific error types
                if "expand shape" in error_msg.lower():
                    print(f"   → This is a text length limit error!")

                return {
                    "success": False,
                    "error": error_msg,
                    "full_output": output
                }

        # Parse success output
        metrics = {}
        for line in output.split('\n'):
            if '=' in line and not line.startswith('ERROR'):
                try:
                    key, value = line.split('=', 1)
                    metrics[key.strip()] = float(value)
                except:
                    pass

        if 'gen_time' in metrics:
            gen_time = metrics['gen_time']
            audio_duration = metrics['audio_duration']
            rtf = metrics['rtf']
            file_size = metrics['file_size']
            word_count = int(metrics.get('word_count', len(text.split())))

            print(f"✅ SUCCESS")
            print(f"   Generation time: {gen_time:.2f}s")
            print(f"   Audio duration: {audio_duration:.2f}s")
            print(f"   Real-Time Factor: {rtf:.3f}")
            print(f"   Speed: {word_count / gen_time:.1f} words/sec")
            print(f"   File size: {file_size:.2f} MB")

            return {
                "success": True,
                "gen_time": gen_time,
                "audio_duration": audio_duration,
                "rtf": rtf,
                "file_size": file_size,
                "words_per_sec": word_count / gen_time
            }

    except subprocess.TimeoutExpired:
        print(f"❌ TIMEOUT (120s)")
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return {"success": False, "error": str(e)}

def main():
    """Run tests with progressively longer texts."""
    print("KittenTTS Maximum Text Length Test (Isolated Environment)")
    print("=" * 70)

    # Test cases with different lengths
    tests = []

    # Very short (baseline)
    tests.append(("Very Short (10 words)",
                  "This is a very short text for testing. " * 1))

    # Short
    tests.append(("Short (25 words)",
                  "This is a short text for testing the KittenTTS model. "
                  "It should work fine without any issues. " * 1))

    # Medium-short
    tests.append(("Medium-Short (50 words)",
                  "This is a medium short text for testing the KittenTTS model. "
                  "The quick brown fox jumps over the lazy dog. "
                  "Testing various sentence structures and word combinations. "
                  "This should still work well. " * 2))

    # Medium
    tests.append(("Medium (100 words)",
                  "This is a medium length text for comprehensive testing. "
                  "The quick brown fox jumps over the lazy dog repeatedly. "
                  "Testing various sentence structures, word combinations, and "
                  "checking how the model handles different types of content. "
                  "This includes questions? Exclamations! And statements. "
                  "We want to ensure robust performance across different inputs. "
                  "The model should handle this without any issues whatsoever. " * 2))

    # Medium-long
    tests.append(("Medium-Long (150 words)",
                  "This is a medium long text that starts to push the boundaries. "
                  "We are testing how KittenTTS handles longer content. "
                  "The model has been trained on various text lengths, but there "
                  "may be practical limits due to the underlying architecture. "
                  "Let's continue adding more content to see where the threshold is. "
                  "This includes testing different sentence structures, punctuation, "
                  "and various linguistic patterns. The goal is to find the optimal "
                  "text length for reliable generation without hitting model limits. "
                  "We continue this exploration by adding more descriptive content. "
                  "The quick brown fox continues its journey over various lazy dogs. " * 3))

    # Long
    tests.append(("Long (200 words)",
                  "This is a long text that may approach or exceed KittenTTS limits. "
                  "We are conducting systematic testing to determine the maximum "
                  "reliable text length for this TTS model. The underlying ONNX "
                  "architecture has specific tensor size constraints that may become "
                  "apparent with longer inputs. As we increase the text length, we "
                  "monitor for specific error patterns such as 'invalid expand shape' "
                  "which typically indicates the model has reached its token limit. "
                  "This information is crucial for setting appropriate constraints in "
                  "the hybrid TTS system. By understanding these limits precisely, we "
                  "can configure the fallback mechanism to trigger at the right "
                  "threshold, ensuring users always get working audio output. "
                  "Let's continue testing with additional content to observe behavior. " * 4))

    # Very long (likely to fail)
    tests.append(("Very Long (250 words)",
                  "This is a very long text that will likely exceed KittenTTS limits. "
                  "We expect this to fail with an 'invalid expand shape' error or "
                  "similar tensor dimension issue. This is valuable information for "
                  "configuring the hybrid TTS system with appropriate fallback triggers. "
                  "The KittenTTS model uses a specific ONNX architecture with fixed "
                  "tensor dimensions, and when the phonemized text exceeds these "
                  "dimensions, the model cannot process the input. By finding the "
                  "exact threshold where failures begin, we can set optimal text "
                  "length limits for the hybrid system. This ensures users get fast "
                  "KittenTTS generation for shorter texts while automatically falling "
                  "back to PocketTTS for longer content that exceeds KittenTTS capacity. "
                  "Let's add even more content to ensure we definitely hit the limit. "
                  "The quick brown fox jumps over lazy dogs repeatedly in various "
                  "scenarios and contexts. Testing continues with more sentences. " * 6))

    results = []
    for test_name, text in tests:
        result = test_kitten_with_isolated_env(text, test_name)
        result["test_name"] = test_name
        result["text_length"] = len(text)
        result["word_count"] = len(text.split())
        results.append(result)

        # If we got a failure, maybe stop or continue to see pattern
        if not result["success"]:
            print(f"\n⚠️  Failure detected at {test_name}")
            print(f"   Continuing with remaining tests to establish pattern...")

    # Print summary
    print(f"\n{'=' * 70}")
    print("TEST SUMMARY")
    print(f"{'=' * 70}")
    print(f"{'Test':<20} {'Chars':<10} {'Words':<10} {'Result':<15} {'Time':<10}")
    print("-" * 70)

    for r in results:
        status = "✅ PASS" if r["success"] else "❌ FAIL"
        time_str = f"{r.get('gen_time', 0):.2f}s" if r["success"] else "N/A"
        print(f"{r['test_name']:<20} {r['text_length']:<10} {r['word_count']:<10} {status:<15} {time_str:<10}")

    # Analysis
    print(f"\n{'=' * 70}")
    print("ANALYSIS")
    print(f"{'=' * 70}")

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    if successful:
        max_success = max(successful, key=lambda x: x["text_length"])
        print(f"✅ Maximum successful length: {max_success['text_length']} chars ({max_success['word_count']} words)")
        print(f"   Test: {max_success['test_name']}")

    if failed:
        min_fail = min(failed, key=lambda x: x["text_length"])
        print(f"❌ Minimum failure length: {min_fail['text_length']} chars ({min_fail['word_count']} words)")
        print(f"   Test: {min_fail['test_name']}")
        print(f"   Error: {min_fail.get('error', 'Unknown')[:100]}")

    # Recommendation
    print(f"\n{'=' * 70}")
    print("RECOMMENDATION")
    print(f"{'=' * 70}")

    if successful and failed:
        # Find a safe threshold (80% of minimum failure)
        threshold = int(min_fail["text_length"] * 0.8)
        print(f"Recommended KITTENTTS_MAX_LENGTH: {threshold} characters")
        print(f"This provides a safety margin below the actual failure point.")
    elif successful:
        # All tests passed - recommend conservative limit
        max_len = max(r["text_length"] for r in results)
        threshold = min(max_len + 100, 500)
        print(f"All tests passed! Recommended KITTENTTS_MAX_LENGTH: {threshold} characters")
        print(f"(Conservative estimate based on successful tests)")

    return 0

if __name__ == "__main__":
    sys.exit(main())
