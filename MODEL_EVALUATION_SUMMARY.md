# TTS Model Evaluation Summary

## Objective
Evaluate alternative TTS models to determine if there's a faster option than Pocket TTS for the codebase.

## Models Evaluated

### 1. LuxTTS
**Source**: https://github.com/ysharma3501/LuxTTS  
**Claimed Performance**: 150x realtime on GPU, 10-30x on CPU  
**Status**: ❌ **Rejected**

**Reasons**:
- Dependency on `piper-phonemize` which has no ARM Mac (Apple Silicon) wheels
- Requires Python 3.11 workaround or Rosetta 2 emulation
- Complex installation with multiple dependencies
- Not compatible with target platform (ARM Mac)

### 2. Marvis TTS
**Source**: https://github.com/Marvis-Labs/marvis-tts  
**Claimed Performance**: Real-time streaming on Apple Silicon  
**Status**: ❌ **Rejected**

**Reasons**:
- Installation succeeded but integration failed
- Benchmark tests timed out
- API compatibility issues with current architecture
- Added complexity without proven benefit

## Current Model: Pocket TTS

**Status**: ✅ **Retained**

**Advantages**:
- Already working and integrated
- Native ARM Mac support
- Simple installation (2 dependencies)
- Proven reliability in production
- 5-10x realtime performance on CPU
- Voice cloning support
- 9 predefined voices

**Performance**:
- Speed: 5-10x realtime (sufficient for most use cases)
- Quality: 24kHz audio
- Memory: Low footprint
- Compatibility: Works on all platforms

## Decision

**Keep Pocket TTS as the sole model** for the following reasons:

1. **Reliability**: Already proven to work in the codebase
2. **Simplicity**: Minimal dependencies, easy maintenance
3. **Compatibility**: Native support for ARM Mac
4. **Performance**: Adequate speed for TTS use cases
5. **Risk**: Alternative models failed integration tests

## Recommendation

Focus on optimizing Pocket TTS usage rather than adding alternative models:
- Use the model daemon for shared model instances
- Implement caching for repeated text
- Optimize voice cloning workflows
- Improve error handling and recovery

## Lessons Learned

1. **Platform compatibility is critical**: Always verify ARM Mac support before integration
2. **Test before integrating**: Benchmark in actual environment, not just claims
3. **Simplicity wins**: Working solution > theoretical performance gains
4. **Dependencies matter**: Complex dependency chains increase failure risk

## Future Considerations

If faster TTS is needed in the future:
- Wait for better ARM Mac support in newer models
- Consider cloud-based TTS APIs for extreme performance needs
- Evaluate models with proven ARM Mac compatibility
- Test thoroughly before integration

## Conclusion

Pocket TTS remains the best choice for this codebase. No changes needed.
