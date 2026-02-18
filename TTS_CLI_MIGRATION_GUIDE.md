# Architecture Update Guide: Aligning `tts-cli` with `local-tts-mcp`

This document outlines recommended architectural updates for the `tts-cli` repository based on improvements implemented in `local-tts-mcp`. These changes aim to enhance stability, handle long inputs gracefully, and improve resource management.

## 1. Robust Text Processing (Critical)

The current `local-tts-mcp` implementation includes a robust `split_text` function. `tts-cli` currently passes raw text directly to the model, which can cause tensor shape mismatches or OOM errors with long inputs.

### Recommendation
Implement a `split_text` utility in `tts_cli/core/utils.py` (or similar) and use it within `ModelDaemon._run_inference`.

**Logic to Port:**
- Split text into chunks < 200 characters.
- Respect sentence boundaries (.!?).
- Force-split very long words if necessary.
- Process chunks sequentially and concatenate the resulting audio tensors *before* saving to WAV.

```python
def split_text(text: str, max_length: int = 200) -> list[str]:
    # ... implementation from local-tts-mcp ...
```

## 2. Voice File Pre-processing

`pocket-tts` can struggle or hallucinate if the voice cloning reference audio is too long (> 10-15s). `local-tts-mcp` now automatically trims input voice files to 10 seconds.

### Recommendation
Update `ModelDaemon._run_inference` (or `voice_manager.py`) to include a pre-processing step for custom voice files.

**Logic to Port:**
1. Check duration of `req.voice` (if it's a file).
2. If > 10.0s, trim to first 10s.
3. Save to a temporary file.
4. Use temporary file for `get_state_for_audio_prompt`.
5. Clean up temp file.

## 3. Tensor Validation & Error Handling

`local-tts-mcp` includes specific checks for the tensors returned by `model.generate_audio`:
- Check if output is a valid Tensor.
- Check for 0-dimension or empty tensors.
- Fix shape dimensions (ensure 2D `[1, T]`).

### Recommendation
Enhance `ModelDaemon._run_inference` to include these validation checks to prevent silent failures or crashes during `scipy.io.wavfile.write`.

## 4. Architecture Comparison & Strategy

| Feature | `local-tts-mcp` | `tts-cli` | Recommendation for `tts-cli` |
| :--- | :--- | :--- | :--- |
| **Idle Strategy** | Unload Model (Keep Server) | Shutdown Daemon (Kill Process) | **Keep Shutdown**. CLI usage is sporadic; killing the process is cleaner. |
| **Concurrency** | Queue + Worker Thread | Queue + Worker Thread | **No Change**. Current `tts-cli` architecture is solid. |
| **Playback** | Server-side (`afplay`) | Client-side (CLI) | **No Change**. CLI architecture separates generation (daemon) from playback (client). |

## 5. Implementation Checklist

- [ ] **Create `tts_cli/core/text_utils.py`**:
    - Add `split_text(text, max_length=200)` function.
- [ ] **Update `tts_cli/core/model_daemon.py`**:
    - Import `split_text`.
    - In `_run_inference`:
        - Apply `split_text` to incoming `req.text`.
        - Loop through chunks, generate audio, collect segments.
        - Concatenate segments using `torch.cat`.
        - Add Tensor validation checks (dim, size).
        - Implement Voice File trimming (using `scipy` or `soundfile` before passing to model).

## 6. Code Snippets for Reference

**Text Splitting:**
```python
def split_text(text: str, max_length: int = 200) -> list[str]:
    # Normalize and split logic
    # ...
```

**Voice Trimming:**
```python
if duration > 10.0:
    # Trim to 10s
    # Write temp file
    # Return temp path
```
