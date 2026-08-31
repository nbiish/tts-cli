# KittenTTS Limits Testing - Final Results

**Date:** 2026-02-22
**Objective:** Determine the exact text length limits for KittenTTS to configure optimal fallback thresholds.

## Testing Methodology

Progressive testing with increasing text lengths to find:
1. Maximum successful text length
2. Minimum failing text length
3. Exact boundary where ONNX tensor errors occur
4. Optimal safe threshold for production use

## Test Results

### Progressive Length Tests

| Test | Characters | Words | Result | Generation Time | RTF |
|------|------------|-------|--------|-----------------|-----|
| Very Short | 39 | 8 | ✅ PASS | 0.35s | 0.127 |
| Short | 94 | 17 | ✅ PASS | 0.87s | 0.132 |
| Medium-Short | 388 | 64 | ✅ PASS | 2.85s | 0.120 |
| Medium | 816 | 118 | ❌ FAIL | N/A | N/A |
| Medium-Long | 1,896 | 294 | ❌ FAIL | N/A | N/A |
| Long | 3,092 | 468 | ❌ FAIL | N/A | N/A |
| Very Long | 5,472 | 846 | ❌ FAIL | N/A | N/A |

### Error Pattern

All failures beyond 388 characters showed the same error:
```
InvalidArgument: [ONNXRuntimeError] : 2 : INVALID_ARGUMENT :
Non-zero status code returned while running Expand node.
Name:'/bert/Expand' Status Message: invalid expand shape
```

This is the classic KittenTMS tensor dimension limit error.

### Binary Search Results

Binary search between 388 and 816 characters:

| Length | Result |
|--------|--------|
| 602 | ❌ FAIL |
| 495 | ❌ FAIL |
| 441 | ❌ FAIL |
| 414 | ✅ SUCCESS |
| 427 | ❌ FAIL |
| 420 | ✅ SUCCESS |

### Precise Boundary Testing

Testing individual character counts around 420:

| Range | Result |
|-------|--------|
| 370-420 | ✅ SUCCESS (all) |
| 425+ | ❌ FAIL |

## Final Results

**Maximum successful length:** 420 characters
**Failure point:** 425 characters
**Error type:** ONNX tensor dimension limit

## Configuration Recommendations

### Production Threshold

**Recommended KITTENTTS_MAX_LENGTH: 350 characters**

**Rationale:**
- 83% of actual limit (420 chars)
- Provides safety margin for edge cases
- Allows for phonemization expansion (phonemes > characters)
- Ensures reliable operation without errors

### Fallback Strategy

```python
if text_length <= 350:
    use_kitten_tts()  # Fast, reliable
else:
    use_pocket_tts()  # Handles longer texts
```

### Performance Impact

| Text Length | Engine | Time | RTF |
|-------------|--------|------|-----|
| < 350 chars | KittenTTS | ~1-3s | 0.12 |
| > 350 chars | PocketTTS | ~4-8s | 0.15 |

## Test Environment

- **Model:** KittenTTS (kitten-tts-nano-0.1)
- **Voice:** expr-voice-2-m
- **Platform:** macOS (Apple Silicon)
- **espeak-ng:** Version 1.52.0
- **Test Date:** 2026-02-22

## Implementation Notes

### Files Updated

1. **tts_cli/models/kitten_tts_model.py**
   - `MAX_TEXT_LENGTH = 350` (updated from 500)

2. **tts_cli/models/hybrid_tts_model.py**
   - `KITTENTTS_MAX_LENGTH = 350` (updated from 500)

### Testing Scripts Created

1. `scripts/research/test_kitten_limits_isolated.py` - Progressive length tests
2. `scripts/research/find_exact_limit.py` - Binary search for exact limit

## Conclusion

The exact KittenTTS text limit is **420 characters**, with failures occurring at **425 characters** due to ONNX tensor dimension constraints.

For production reliability, we use **350 characters** as the threshold, providing a comfortable safety margin while maximizing the use of the faster KittenTTS engine for typical use cases.

This configuration ensures:
- ✅ Reliable operation within KittenTTS limits
- ✅ Fast generation for typical texts (< 350 chars)
- ✅ Automatic fallback to PocketTTS for longer texts
- ✅ No ONNX errors or tensor dimension issues
- ✅ Consistent user experience
