#!/usr/bin/env python3
"""
Simple test script for the hybrid TTS model.

This script tests the hybrid model with different text lengths and scenarios.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from tts_cli.models.hybrid_tts_model import HybridTTSModel

def test_short_text():
    """Test with short text (should use KittenTTS)."""
    print("=" * 60)
    print("TEST 1: Short text (< 100 chars)")
    print("=" * 60)

    model = HybridTTSModel()
    text = "Hello, this is a short text test."
    output_path = "test_short.wav"

    print(f"Text: '{text}' ({len(text)} chars)")
    print(f"Expected: KittenTTS")

    success = model.generate_speech(text, voice="expr-voice-2-m", output_path=output_path)

    if success and Path(output_path).exists():
        print(f"✅ SUCCESS: Audio generated at {output_path}")
        size = Path(output_path).stat().st_size / 1024
        print(f"   File size: {size:.1f} KB")
    else:
        print(f"❌ FAILED: Audio not generated")

    print()
    return success

def test_medium_text():
    """Test with medium text (should use KittenTTS)."""
    print("=" * 60)
    print("TEST 2: Medium text (100-500 chars)")
    print("=" * 60)

    model = HybridTTSModel()
    text = "This is a medium length text that falls within the KittenTTS limits. " * 6
    output_path = "test_medium.wav"

    print(f"Text: '{text[:50]}...' ({len(text)} chars)")
    print(f"Expected: KittenTTS")

    success = model.generate_speech(text, voice="expr-voice-2-f", output_path=output_path)

    if success and Path(output_path).exists():
        print(f"✅ SUCCESS: Audio generated at {output_path}")
        size = Path(output_path).stat().st_size / 1024
        print(f"   File size: {size:.1f} KB")
    else:
        print(f"❌ FAILED: Audio not generated")

    print()
    return success

def test_long_text():
    """Test with long text (should fallback to PocketTTS)."""
    print("=" * 60)
    print("TEST 3: Long text (> 500 chars) - Should Fallback")
    print("=" * 60)

    model = HybridTTSModel()
    text = "This is a long text that exceeds the KittenTTS limits and should trigger automatic fallback to PocketTTS. " * 15
    output_path = "test_long.wav"

    print(f"Text length: {len(text)} chars")
    print(f"Expected: PocketTTS (fallback)")

    success = model.generate_speech(text, voice="alba", output_path=output_path)

    if success and Path(output_path).exists():
        print(f"✅ SUCCESS: Audio generated at {output_path}")
        size = Path(output_path).stat().st_size / 1024
        print(f"   File size: {size:.1f} KB")
    else:
        print(f"❌ FAILED: Audio not generated")

    print()
    return success

def test_model_info():
    """Test model info."""
    print("=" * 60)
    print("TEST 4: Model Information")
    print("=" * 60)

    model = HybridTTSModel()
    info = model.get_model_info()

    print(f"Model name: {info['name']}")
    print(f"Description: {info['description']}")
    print(f"Primary model: {info['primary_model']}")
    print(f"Fallback model: {info['fallback_model']}")
    print(f"Kitten voices: {info['kitten_voices']}")
    print(f"Pocket voices: {info['pocket_voices']}")
    print(f"Max text length: {info['max_text_length']}")
    print(f"Kitten max length: {info['kitten_max_length']}")

    print()
    return True

def main():
    """Run all tests."""
    print("Hybrid TTS Model Test Suite")
    print()

    # Set espeak library path if needed
    if not os.environ.get('PHONEMIZER_ESPEAK_LIBRARY'):
        os.environ['PHONEMIZER_ESPEAK_LIBRARY'] = '/opt/homebrew/lib/libespeak-ng.dylib'
        print(f"Set PHONEMIZER_ESPEAK_LIBRARY")
        print()

    results = []

    # Run tests
    results.append(("Model Info", test_model_info()))
    results.append(("Short Text", test_short_text()))
    results.append(("Medium Text", test_medium_text()))
    results.append(("Long Text", test_long_text()))

    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print()
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
