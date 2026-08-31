#!/usr/bin/env bash
# Run three IndexTTS-2.5 prompting variants with UTC timestamps + RTF.
# Assets (GGUF, examples, env, cli-tts) come from MAIN repo; outputs go to OUT_DIR.
# Usage: run_three_variants.sh <main_repo> <out_dir>
set -u
MAIN="${1:-/Volumes/1tb-sandisk/code-external/tts-cli}"
OUT="${2:-/Volumes/1tb-sandisk/code-external/indextts-prompting/benchmarks/indextts-prompting}"
GGUF="$MAIN/models-gguf/IndexTTS2.5-GGUF/index-tts2_5-q8_0.gguf"
REF="$MAIN/examples/voice_01.wav"
PY="$MAIN/.model-envs/index-tts-env/.venv/bin/python"
TEXT="cli-tts is ready for all agents. IndexTTS-2.5 is the sole engine. Next step: verify the voice channel end to end."
RESULTS="$OUT/RESULTS.txt"
: > "$RESULTS"
ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

echo "=== IndexTTS-2.5 Three-Variant Prompting Benchmark ===" >> "$RESULTS"
echo "Text: $TEXT" >> "$RESULTS"
echo "Reference: $REF" >> "$RESULTS"
echo "GGUF: $GGUF" >> "$RESULTS"
echo >> "$RESULTS"

echo "[$(ts)] START A: quantized (GGUF Q8, audio.cpp, Metal, default controls)" >> "$RESULTS"
audiocpp_cli --task tts --family index_tts2 --model "$GGUF" --backend metal \
  --language en --voice-ref "$REF" --text "$TEXT" \
  --out "$OUT/out_A_quantized.wav" --metrics 2>>"$OUT/A.stderr.log" | tee -a "$RESULTS"
echo "[$(ts)] END   A" >> "$RESULTS"; echo >> "$RESULTS"

echo "[$(ts)] START B: normal (Python IndexTTS-2.5, MPS, --quality)" >> "$RESULTS"
( cd "$MAIN" && { time cli-tts --model index-tts-quality --quality --voice "$REF" --lang EN \
    --output "$OUT/out_B_normal.wav" --text "$TEXT" ; } >>"$OUT/B.log" 2>&1 )
echo "[$(ts)] END   B" >> "$RESULTS"
grep -E "real|generated|✅" "$OUT/B.log" | tail -3 >> "$RESULTS" 2>/dev/null
echo >> "$RESULTS"

echo "[$(ts)] START C: template (GGUF Q8 + --emotion happy --speaking-rate 0.95)" >> "$RESULTS"
audiocpp_cli --task tts --family index_tts2 --model "$GGUF" --backend metal \
  --language en --emotion happy --speaking-rate 0.95 --pitch-shift 0.0 --energy-scale 1.0 \
  --voice-ref "$REF" --text "$TEXT" \
  --out "$OUT/out_C_template.wav" --metrics 2>>"$OUT/C.stderr.log" | tee -a "$RESULTS"
echo "[$(ts)] END   C" >> "$RESULTS"; echo >> "$RESULTS"

echo "=== Audio durations ===" >> "$RESULTS"
for f in A_quantized B_normal C_template; do
  if [ -f "$OUT/out_$f.wav" ]; then
    dur=$("$PY" -c "import soundfile as sf; print(f'{sf.info(\"$OUT/out_$f.wav\").duration:.2f}s')" 2>/dev/null || echo "?")
    echo "out_$f.wav: $dur" >> "$RESULTS"
  fi
done
echo "[$(ts)] ALL DONE" >> "$RESULTS"
cat "$RESULTS"
