# TTS Model Benchmark Report
Generated: 2025-09-07 05:53:47

Test Text (23 words): The quick brown fox jumps over the lazy dog while the sun shines brightly in the clear blue sky above the peaceful meadow.

## 🏆 Summary
**Fastest Model**: vibevoice (1.29s)
**Available Models**: 3/3

## 📊 Detailed Results

### vibevoice
- **Available**: ✅
- **Generation Time**: 1.29 seconds
- **File Size**: N/A bytes
- **Voice Used**: default
- **Output File**: None

### coqui-tts
- **Available**: ✅
- **Generation Time**: 9.63 seconds
- **File Size**: 371276 bytes
- **Voice Used**: tts_models/en/ljspeech/tacotron2-DDC_ph
- **Output File**: TESTING/OUTPUTS/benchmark_coqui-tts_20250907_055327.wav

### zonos
- **Available**: ✅
- **Generation Time**: 5.23 seconds
- **File Size**: N/A bytes
- **Voice Used**: default
- **Output File**: None

## 🎯 Recommendations

1. **Set Default Model**: `vibevoice` (fastest at 1.29s)
2. **CLI Command**: Update default model in `cli.py` line 240
3. **Performance**: Consider model quality vs speed trade-offs