# TTS Quick Reference Guide

**Author:** Nbiish Waabanimii-Kinawaabakizi | **Date:** August 26, 2025 | **Version:** 1.0

## Quick Testing Commands

### 1. F5-TTS (SWivid)
```bash
# Test basic functionality
f5-tts_infer-cli --model F5TTS_v1_Base --gen_text "Hello world! This is a test of F5-TTS voice synthesis."

# Test voice cloning
f5-tts_infer-cli --model F5TTS_v1_Base --ref_audio "test-voice-clone.wav" --gen_text "Hello world! This is a test of voice cloning with F5-TTS."

# Test with reference text
f5-tts_infer-cli --model F5TTS_v1_Base --ref_audio "test-voice-clone.wav" --ref_text "This is the reference text." --gen_text "Hello world! This is a test of voice cloning with reference text."
```

### 2. Edge TTS (Microsoft)
```bash
# Test basic functionality
python -c "
import asyncio
import edge_tts

async def test():
    communicate = edge_tts.Communicate('en-US-AriaNeural', 'Hello world! This is a test of Edge TTS.')
    await communicate.save('edge-tts-test.wav')

asyncio.run(test())
"

# List available voices
python -c "
import asyncio
import edge_tts

async def list_voices():
    voices = await edge_tts.list_voices()
    for voice in voices[:10]:  # Show first 10
        print(f'{voice[\"name\"]}: {voice[\"locale\"]}')

asyncio.run(list_voices())
"
```

### 3. Dia (Nari Labs)
```bash
# Test basic functionality
python -c "
from dia_tts import DiaTTS
dia = DiaTTS()
audio = dia.generate('Hello world! This is a test of Dia TTS.')
dia.save_audio(audio, 'dia-test.wav')
"

# Test multi-speaker dialogue
python -c "
from dia_tts import DiaTTS
dia = DiaTTS()

dialogue = '''
[S1] Hello there! How are you today?
[S2] I am doing great, thank you for asking!
[S1] That is wonderful to hear!
'''

audio = dia.generate(dialogue)
dia.save_audio(audio, 'dia-dialogue-test.wav')
"

# Test non-verbal expressions
python -c "
from dia_tts import DiaTTS
dia = DiaTTS()

text = 'Hello! (laughs) That was funny! (coughs) Excuse me.'
audio = dia.generate(text)
dia.save_audio(audio, 'dia-expressions-test.wav')
"
```

### 4. Kyutai TTS
```bash
# Test basic functionality
python -m moshi_mlx.run_tts --hf-repo kyutai/tts-1.6b-en_fr --text "Hello world! This is a test of Kyutai TTS." --output_file "kyutai-test.wav"

# Test voice cloning
python -m moshi_mlx.run_tts --hf-repo kyutai/tts-1.6b-en_fr --text "Hello world! This is a test of voice cloning with Kyutai TTS." --voice_repo "voice_repo_path" --output_file "kyutai-clone-test.wav"

# Test multilingual (French)
python -m moshi_mlx.run_tts --hf-repo kyutai/tts-1.6b-en_fr --text "Bonjour le monde! Ceci est un test de Kyutai TTS." --output_file "kyutai-french-test.wav"
```

### 5. Kokoro TTS (Hexgrad)
```bash
# Test basic functionality
python -c "
from kokoro_tts import KokoroTTS
kokoro = KokoroTTS()
audio = kokoro.generate('Hello world! This is a test of Kokoro TTS.')
kokoro.save_audio(audio, 'kokoro-test.wav')
"

# Test voice cloning
python -c "
from kokoro_tts import KokoroTTS
kokoro = KokoroTTS()
audio = kokoro.generate('Hello world! This is a test of voice cloning with Kokoro TTS.', reference_audio='test-voice-clone.wav')
kokoro.save_audio(audio, 'kokoro-clone-test.wav')
"
```

#

# Install dependencies in isolated environment
uv pip install langid jieba soundfile

# Test basic functionality
python examples/generation.py \
  --temperature 0.3 \

# Test with custom temperature
python examples/generation.py \
  --transcript "This is a test with different temperature settings." \
  --temperature 0.7 \

# Expected performance: ~3 minutes for short text (high-quality generation)
# Output: 24kHz mono PCM WAV file
# Status: ✅ Production Ready - All functionality working correctly
```

### 7. VibeVoice (Microsoft)
```bash
# Test demo mode
python -m vibevoice.demo

# Test inference from file
echo "Hello world! This is a test of VibeVoice TTS." > vibevoice-test.txt
python -m vibevoice.inference --text_file "vibevoice-test.txt" --output_file "vibevoice-test.wav"

# Test voice cloning
python -m vibevoice.inference --text_file "vibevoice-test.txt" --output_file "vibevoice-clone-test.wav" --reference_audio "test-voice-clone.wav"
```

---

## Test Cases by Capability

### Voice Cloning Tests
```bash
# Test with various reference audio lengths
for length in 5 10 30 60; do
    # Generate test audio of specified length
    ffmpeg -f lavfi -i "sine=frequency=1000:duration=$length" "test-${length}s.wav"
    
    # Test each model with this reference audio
    # (Run appropriate commands for each model)
done
```

### Multi-Speaker Tests
```bash
# Test dialogue generation
dialogue_text="
[S1] Welcome to our conversation!
[S2] Thank you for having me.
[S1] How are you today?
[S2] I'm doing well, how about you?
[S1] I'm excellent!
"

echo "$dialogue_text" > dialogue-test.txt

# Test with Dia TTS
python -c "
from dia_tts import DiaTTS
dia = DiaTTS()
with open('dialogue-test.txt', 'r') as f:
    dialogue = f.read()
audio = dia.generate(dialogue)
dia.save_audio(audio, 'dia-dialogue-test.wav')
"
```

### Non-Verbal Expression Tests
```bash
# Test various expressions
expressions=(
    "Hello! (laughs) That was funny!"
    "(coughs) Excuse me, let me continue."
    "This is amazing! (gasps) I can't believe it!"
    "(whispers) This is a secret."
    "Goodbye! (waves) See you later!"
)

for i, expr in "${expressions[@]}"; do
    echo "$expr" > "expression-test-${i}.txt"
done

# Test with Dia TTS
python -c "
from dia_tts import DiaTTS
dia = DiaTTS()

for i in range(1, 6):
    with open(f'expression-test-{i}.txt', 'r') as f:
        text = f.read()
    audio = dia.generate(text)
    dia.save_audio(audio, f'dia-expression-test-{i}.wav')
"
```

---

## Performance Testing

### Speed Tests
```bash
# Test inference speed for various text lengths
texts=(
    "Hello world!"
    "This is a longer sentence to test processing speed."
    "This is a much longer paragraph that contains multiple sentences and should take longer to process. We want to measure how the processing time scales with text length."
)

for text in "${texts[@]}"; do
    echo "Testing: $text"
    time python -c "
# Run appropriate model command here
"
done
```

### Memory Usage Tests
```bash
# Monitor memory usage during inference
python -c "
import psutil
import time

def monitor_memory():
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Run model inference here
    
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    peak_memory = process.memory_info().peak_wset / 1024 / 1024  # MB
    
    print(f'Initial: {initial_memory:.2f} MB')
    print(f'Final: {final_memory:.2f} MB')
    print(f'Peak: {peak_memory:.2f} MB')
    print(f'Delta: {final_memory - initial_memory:.2f} MB')

monitor_memory()
"
```

---

## Error Handling Tests

### Invalid Input Tests
```bash
# Test with empty text
python -c "
# Run model with empty string
"

# Test with very long text
long_text=$(printf 'A%.0s' {1..10000})
echo "$long_text" > long-text-test.txt
python -c "
# Run model with very long text
"

# Test with special characters
special_text="Hello! @#$%^&*()_+{}|:<>?[]\\;'\",./<>?"
echo "$special_text" > special-chars-test.txt
python -c "
# Run model with special characters
"
```

### Resource Limit Tests
```bash
# Test with large reference audio files
# Generate large test files
ffmpeg -f lavfi -i "sine=frequency=1000:duration=300" "large-audio-test.wav"  # 5 minutes

python -c "
# Run model with large reference audio
"
```

---

## Platform Compatibility Tests

### MPS (Apple Silicon) Tests
```bash
# Test on MPS
export PYTORCH_ENABLE_MPS_FALLBACK=1
python -c "
import torch
print(f'MPS available: {torch.backends.mps.is_available()}')
print(f'MPS built: {torch.backends.mps.is_built()}')

# Run model tests
"
```

### CUDA Tests
```bash
# Test on CUDA
python -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA device: {torch.cuda.get_device_name()}')
    print(f'CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB')

# Run model tests
"
```

### CPU Fallback Tests
```bash
# Force CPU usage
export CUDA_VISIBLE_DEVICES=""
export PYTORCH_ENABLE_MPS_FALLBACK=0

python -c "
import torch
print(f'Device: {torch.device(\"cpu\")}')

# Run model tests
"
```

---

## Quality Assessment Tests

### Audio Quality Tests
```bash
# Generate test audio files
test_texts=(
    "The quick brown fox jumps over the lazy dog."
    "She sells seashells by the seashore."
    "Peter Piper picked a peck of pickled peppers."
    "How much wood would a woodchuck chuck if a woodchuck could chuck wood?"
)

for i, text in "${test_texts[@]}"; do
    echo "$text" > "quality-test-${i}.txt"
done

# Test each model and save outputs
# Compare audio quality subjectively
```

### Voice Consistency Tests
```bash
# Test voice cloning consistency
reference_text="This is my reference voice for testing."
echo "$reference_text" > reference-text.txt

# Generate multiple samples with same reference
for i in {1..5}; do
    # Run voice cloning for each model
    # Save as clone-test-${model}-${i}.wav
done

# Compare consistency across samples
```

---

## Integration Tests

### CLI Tool Tests
```bash
# Test CLI interface
python tts_cli/cli_tts.py --model f5-tts --text "Hello world!" --output "cli-f5-test.wav"
python tts_cli/cli_tts.py --model edge-tts --text "Hello world!" --output "cli-edge-test.wav"
python tts_cli/cli_tts.py --model dia --text "Hello world!" --output "cli-dia-test.wav"

# Test voice cloning
python tts_cli/cli_tts.py --model f5-tts --text "Hello world!" --voice-clone "test-voice-clone.wav" --output "cli-f5-clone-test.wav"
```

### Environment Management Tests
```bash
# Test isolated environments
python tts_cli/cli_tts.py --create-env f5-tts
python tts_cli/cli_tts.py --list-envs
python tts_cli/cli_tts.py --activate-env f5-tts
python tts_cli/cli_tts.py --test-env f5-tts
```

---

## Test Results Template

```markdown
# Test Results for [Model Name]

## Basic Functionality
- [ ] Text-to-speech generation works
- [ ] Audio output is saved correctly
- [ ] Audio quality is acceptable

## Voice Cloning (if supported)
- [ ] Reference audio is processed correctly
- [ ] Cloned voice maintains characteristics
- [ ] Different reference audio produces different results

## Multi-Speaker (if supported)
- [ ] Speaker tags are recognized
- [ ] Different speakers have distinct voices
- [ ] Dialogue flow is natural

## Non-Verbal Expressions (if supported)
- [ ] Expressions are recognized
- [ ] Audio reflects expression intent
- [ ] Multiple expressions work together

## Performance
- [ ] Inference speed is acceptable
- [ ] Memory usage is reasonable
- [ ] Platform compatibility works

## Error Handling
- [ ] Invalid inputs are handled gracefully
- [ ] Resource limits are respected
- [ ] Clear error messages are provided

## Notes
- Any issues encountered
- Workarounds found
- Recommendations for improvement
```

---

*Use this guide to systematically test each TTS model and document results.*

## Model Implementation Examples

### 1. F5-TTS (SWivid)
```python
from f5_tts import F5TTS
tts = F5TTS()
audio = tts.generate('Hello world! This is a test of F5-TTS.')
tts.save_audio(audio, 'f5tts-test.wav')
```

### 2. Edge TTS (Microsoft)
```python
import edge_tts
import asyncio

async def generate_speech():
    communicate = edge_tts.Communicate('Hello world! This is a test of Edge TTS.', 'en-US-AriaNeural')
    await communicate.save('edge-tts-test.wav')

asyncio.run(generate_speech())
```

### 3. Dia (Nari Labs)
```python
from transformers import AutoTokenizer, AutoModel
tokenizer = AutoTokenizer.from_pretrained('nari-labs/Dia-1.6B-0626')
model = AutoModel.from_pretrained('nari-labs/Dia-1.6B-0626')
# Implementation details to be added
```

### 4. Kyutai TTS
```python
import moshi_mlx
# Implementation details to be added
```

### 5. Kokoro TTS (Hexgrad)
```python
from kokoro import KokoroEngine
engine = KokoroEngine()
audio = engine.generate('Hello world! This is a test of Kokoro TTS.')
engine.save_audio(audio, 'kokoro-test.wav')
```

#

### 7. VibeVoice (Microsoft)
```python
from vibevoice import VibeVoiceEngine
engine = VibeVoiceEngine()
# Implementation details to be added
```

---

## Voice Cloning Examples

### 1. F5-TTS Voice Cloning
```python
from f5_tts import F5TTS
tts = F5TTS()
audio = tts.generate('Hello world! This is a test of voice cloning with F5-TTS.', reference_audio='test-voice-clone.wav')
tts.save_audio(audio, 'f5tts-clone-test.wav')
```

### 2. Dia Voice Cloning
```python
from transformers import AutoTokenizer, AutoModel
# Implementation details to be added
```

### 3. Kyutai TTS Voice Cloning
```python
import moshi_mlx
# Implementation details to be added
```

### 4. Kokoro Voice Cloning
```python
from kokoro import KokoroEngine
engine = KokoroEngine()
audio = engine.generate('Hello world! This is a test of voice cloning with Kokoro TTS.', reference_audio='test-voice-clone.wav')
engine.save_audio(audio, 'kokoro-clone-test.wav')
```

```python
# Implementation details to be added
```

### 6. VibeVoice Voice Cloning
```python
from vibevoice import VibeVoiceEngine
# Implementation details to be added
```
