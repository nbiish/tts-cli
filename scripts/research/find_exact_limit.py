#!/usr/bin/env python3
"""
Find Exact KittenTTS Limit

Binary search to find the exact character limit where KittenTTS fails.
"""

import sys
import os
import subprocess
from pathlib import Path

def test_length(char_count: int) -> bool:
    """Test if KittenTTS can handle text of specific length."""

    # Generate text of exactly this length
    base_text = "The quick brown fox jumps over the lazy dog. "
    text = ""
    while len(text) < char_count:
        text += base_text
    text = text[:char_count]

    # Escape text
    escaped_text = text.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'").replace('\n', '\\n')

    script = f'''
import os
os.environ['PHONEMIZER_ESPEAK_LIBRARY'] = '/opt/homebrew/lib/libespeak-ng.dylib'
try:
    from kittentts import KittenTTS
    import soundfile as sf
    model = KittenTTS()
    audio = model.generate("{escaped_text}", voice='expr-voice-2-m')
    if audio is None:
        print("FAIL: None")
    else:
        print("SUCCESS")
except Exception as e:
    print(f"FAIL: {{type(e).__name__}}")
'''

    env_path = Path(".model-envs/kitten-tts-env/.venv/bin/python")
    if not env_path.exists():
        print("❌ KittenTTS environment not found")
        return False

    try:
        result = subprocess.run(
            [str(env_path), "-c", script],
            capture_output=True,
            text=True,
            timeout=60
        )

        output = result.stdout + result.stderr
        return "SUCCESS" in output

    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False

def binary_search_limit(min_len: int, max_len: int) -> int:
    """Binary search to find the exact limit."""

    print(f"Binary searching between {min_len} and {max_len} characters...")

    while max_len - min_len > 10:
        mid = (min_len + max_len) // 2
        print(f"Testing {mid} characters... ", end="", flush=True)

        if test_length(mid):
            print("✅ SUCCESS")
            min_len = mid
        else:
            print("❌ FAIL")
            max_len = mid

    return min_len

def find_precise_limit(around: int):
    """Test individual characters around the limit."""

    print(f"\nPrecise testing around {around} characters:")

    success_limit = 0
    for length in range(around - 50, around + 51, 5):
        if test_length(length):
            print(f"{length} chars: ✅")
            success_limit = length
        else:
            print(f"{length} chars: ❌")
            break

    return success_limit

def main():
    """Main function."""
    print("Finding Exact KittenTTS Character Limit")
    print("=" * 60)

    # Binary search to find approximate limit
    limit = binary_search_limit(388, 816)

    print(f"\n✅ Approximate limit found: {limit} characters")

    # Find precise limit
    precise = find_precise_limit(limit)

    print(f"\n{'=' * 60}")
    print("FINAL RESULTS")
    print(f"{'=' * 60}")
    print(f"Maximum successful length: {precise} characters")

    # Calculate safe threshold (80% of limit)
    safe_threshold = int(precise * 0.8)
    print(f"Recommended safe threshold: {safe_threshold} characters (80% safety margin)")

    # Round to nice numbers
    print(f"\nSuggested configuration:")
    print(f"  KITTENTTS_MAX_LENGTH = {safe_threshold}")
    print(f"  (Rounded to nearest multiple of 50)")

    return 0

if __name__ == "__main__":
    sys.exit(main())
