# Hybrid TTS Architecture - Implementation Plan

**Date:** 2026-02-22
**Objective:** Implement KittenTTS as the default TTS engine with automatic fallback to PocketTTS for voice cloning and long text scenarios.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         TTS CLI                                 │
├─────────────────────────────────────────────────────────────────┤
│  User Input: Text + Optional Voice Clone                        │
├─────────────────────────────────────────────────────────────────┤
│  Primary Engine: KittenTTS (Fast, 8 built-in voices)            │
│    - Timeout: 60 seconds per generation request                 │
│    - Max text length: 500 characters (soft limit)               │
│    - Fallback triggers:                                         │
│      * Timeout exceeded                                         │
│      * Text too long (model token limit)                        │
│      * ONNX runtime errors                                      │
│      * Phonemization failures                                   │
├─────────────────────────────────────────────────────────────────┤
│  Fallback Engine: PocketTTS (Slower, voice cloning)             │
│    - Activated when:                                            │
│      * --voice-clone flag is used                               │
│      * KittenTTS fails (any reason)                             │
│      * Text exceeds safe limits                                 │
│    - Timeout: 180 seconds per generation request                │
├─────────────────────────────────────────────────────────────────┤
│  Error Handling:                                                │
│    - Log fallback reason                                        │
│    - Notify user of engine switch                               │
│    - Clear error messages                                       │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Strategy

### Phase 1: Create Hybrid Model Manager

**File:** `tts_cli/models/hybrid_tts_model.py`

**Responsibilities:**
1. Try KittenTTS first with timeout
2. Catch specific KittenTTS errors
3. Fallback to PocketTTS on failure
4. Log all fallbacks with reasons
5. Provide unified interface to CLI

**Key Features:**
- Configurable timeouts per engine
- Text length pre-validation
- Detailed error logging
- Performance metrics collection

### Phase 2: Implement KittenTTS Model Wrapper

**File:** `tts_cli/models/kitten_tts_model.py`

**Requirements:**
- Implement `BaseTTSModel` interface
- Handle espeak-ng dependency checking
- Support 8 built-in voices
- Timeout wrapper for generation
- Proper error messages

**Error Handling:**
- `espeak not installed` → Clear setup instructions
- `Model load timeout` → Retry once, then fallback
- `Text too long` → Fallback to PocketTTS
- `ONNX errors` → Fallback to PocketTTS

### Phase 3: Update Model Daemon

**File:** `tts_cli/core/model_daemon.py`

**Changes:**
- Support multiple model types simultaneously
- Separate daemon instances per model type
- Shared request queue with model type tagging
- Intelligent model switching

**Implementation:**
- `KittenTTSModelDaemon` - Fast, low memory
- `PocketTTSModelDaemon` - Slower, higher memory
- Automatic daemon lifecycle management

### Phase 4: Update CLI

**File:** `tts_cli/cli.py`

**Changes:**
1. Replace `PocketTTSModel` with `HybridTTSModel` as default
2. Add `--model kitten-tts` flag (for explicit selection)
3. Add `--model pocket-tts` flag (for explicit selection)
4. Add `--model auto` flag (default, hybrid behavior)
5. Keep `--voice-clone` force PocketTTS

**User Experience:**
```bash
# Default: KittenTTS with automatic fallback
cli-tts "Hello world"

# Explicit KittenTTS (no fallback)
cli-tts "Hello world" --model kitten-tts

# Explicit PocketTTS
cli-tts "Hello world" --model pocket-tts

# Voice cloning (forces PocketTTS)
cli-tts "Hello world" --voice-clone my_voice.wav
```

### Phase 5: Configuration Management

**File:** `tts_cli/config.py` (new)

**Configuration:**
```python
HYBRID_CONFIG = {
    "kitten_tts": {
        "timeout_seconds": 60,
        "max_text_length": 500,
        "retry_count": 1,
        "enabled": True
    },
    "pocket_tts": {
        "timeout_seconds": 180,
        "max_text_length": 5000,
        "retry_count": 2,
        "enabled": True
    },
    "fallback": {
        "enabled": True,
        "log_reasons": True,
        "notify_user": True
    }
}
```

## Fallback Triggers

### KittenTTS → PocketTTS Fallback Conditions

1. **Text Length**
   - Input > 500 characters → Immediate fallback
   - Input > 1000 characters → Force PocketTTS

2. **Timeout**
   - Generation > 60 seconds → Fallback
   - Model load > 30 seconds → Fallback

3. **Specific Errors**
   - `ONNXRuntimeError: invalid expand shape` → Text too long
   - `RuntimeError: espeak not installed` → Fallback
   - `AttributeError` / `ImportError` → Fallback

4. **Voice Cloning**
   - `--voice-clone` flag present → Use PocketTTS directly

5. **Custom Voices**
   - Custom voice from `custom_voices/` → Use PocketTTS

## Error Messages

### User-Facing Messages

```python
FALLBACK_MESSAGES = {
    "text_too_long": "Text too long for KittenTTS, using PocketTTS instead...",
    "timeout": "KittenTTS timeout, falling back to PocketTTS...",
    "espeak_missing": "espeak-ng not found, using PocketTTS instead...",
    "onnx_error": "KittenTTS processing error, falling back to PocketTTS...",
    "voice_cloning": "Voice cloning requested, using PocketTTS...",
    "custom_voice": "Custom voice detected, using PocketTTS...",
    "unknown_error": "KittenTTS unavailable, falling back to PocketTTS..."
}
```

### Logging Format

```
[HYBRID] Attempting KittenTTS for text: "Hello world" (11 chars)
[HYBRID] KittenTTS generation failed: ONNXRuntimeError - invalid expand shape
[HYBRID] Fallback reason: text_too_long
[HYBRID] Switching to PocketTTS
[HYBRID] PocketTTS generation successful: 1.2s
```

## Performance Considerations

### Latency Analysis

| Scenario | KittenTTS | PocketTTS | User Impact |
|----------|-----------|-----------|-------------|
| Short text (< 100 chars) | ~1s | ~2s | Minimal |
| Medium text (100-500 chars) | ~2s | ~4s | Acceptable |
| Long text (> 500 chars) | FAIL | ~6s | Better than error |
| Voice cloning | N/A | ~8s | Expected |

### Memory Usage

- KittenTTS: ~200MB (ONNX model)
- PocketTTS: ~500MB (PyTorch model)
- Hybrid: ~700MB (both loaded, but managed by daemon)

## Testing Strategy

### Test Cases

1. **Short Text (< 100 chars)**
   - Expected: KittenTTS success
   - Verify: Fast generation, good quality

2. **Medium Text (100-500 chars)**
   - Expected: KittenTTS success
   - Verify: Fast generation, good quality

3. **Long Text (> 500 chars)**
   - Expected: Immediate PocketTTS fallback
   - Verify: No KittenTTS attempt, clean fallback

4. **Very Long Text (> 1000 chars)**
   - Expected: Direct PocketTTS
   - Verify: No fallback attempts

5. **Voice Cloning**
   - Expected: Direct PocketTTS
   - Verify: No KittenTTS attempt

6. **KittenTTS Timeout**
   - Simulate: Mock timeout
   - Expected: Clean PocketTTS fallback

7. **espeak-ng Missing**
   - Simulate: Uninstall espeak-ng
   - Expected: Clean PocketTTS fallback

8. **Custom Voice Selection**
   - Expected: Direct PocketTTS
   - Verify: No KittenTTS attempt

## Implementation Priority

### Sprint 1: Core Infrastructure
1. ✅ Design hybrid architecture
2. ⏳ Create `HybridTTSModel` class
3. ⏳ Implement `KittenTTSModel` wrapper
4. ⏳ Add timeout mechanisms

### Sprint 2: Integration
1. ⏳ Update CLI to use hybrid model
2. ⏳ Add configuration management
3. ⏳ Implement fallback logging
4. ⏳ Add user-friendly messages

### Sprint 3: Testing & Polish
1. ⏳ Write comprehensive tests
2. ⏳ Test all fallback scenarios
3. ⏳ Performance optimization
4. ⏳ Documentation updates

## Success Criteria

✅ **Must Have:**
- Default command uses KittenTTS
- Automatic fallback on any KittenTTS failure
- Long text (> 500 chars) uses PocketTTS directly
- Voice cloning uses PocketTTS
- Clear user feedback during fallback

✅ **Should Have:**
- Configurable timeouts
- Detailed fallback logging
- Performance metrics
- Graceful degradation

✅ **Nice to Have:**
- Automatic fallback tuning
- Machine learning for timeout prediction
- User preference persistence
- Advanced diagnostics

## Rollback Plan

If hybrid approach causes issues:
1. Revert to PocketTTS-only: Change default model in CLI
2. Keep KittenTTS available via `--model kitten-tts` flag
3. Document known issues
4. Plan fixes for next release

## Monitoring & Metrics

Key metrics to track:
- KittenTTS success rate
- Fallback frequency
- Fallback reasons distribution
- Average generation time per engine
- User satisfaction (feedback)

## Conclusion

This hybrid architecture provides the best of both worlds:
- **Speed**: KittenTTS for typical use cases
- **Reliability**: PocketTTS fallback for edge cases
- **Features**: Voice cloning when needed
- **User Experience**: Transparent, automatic switching

The implementation is designed to be maintainable, testable, and user-friendly.
