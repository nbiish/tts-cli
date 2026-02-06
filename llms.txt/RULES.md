# Project Rules

## Core Principles

1.  **Security First**:
    *   Zero Trust architecture.
    *   Sanitize all inputs (text, file paths).
    *   No hardcoded secrets.
    *   Least privilege for file operations.

2.  **Code Quality**:
    *   Follow PEP 8 for Python code.
    *   Use type hints (`typing` module) extensively.
    *   Keep code DRY (Don't Repeat Yourself) and SOLID.
    *   Prefer small, focused changes.

3.  **Architecture**:
    *   **Isolation**: Every model MUST run in its own `uv` environment.
    *   **Centralization**: All model environments are stored in the `.model-envs/` directory within the project (or `~/.tts-cli/model-envs` if installed globally).
    *   **Compatibility**: All audio output MUST be **16-bit PCM WAV** to ensure compatibility with downstream tools (like voice cloning inputs).

## Implementation Rules

### Pocket TTS Only
*   We exclusively support the **Pocket TTS** model by Kyutai.
*   Do not implement other legacy models (Coqui, Edge TTS, etc.) unless explicitly authorized.

### File Handling
*   **Reading**: Verify file existence before access. Use absolute paths where possible.
*   **Writing**: Check permissions. Use temporary directories if primary locations (like home cache) are not writable.
*   **Cleanup**: Rotate cache files to prevent disk bloat (default limit: 9 files).

### CLI Behavior
*   **Auto-Play**: Always attempt to play generated audio unless explicitly disabled (feature pending, currently always on).
*   **Defaults**: If no text is provided for voice cloning, use a sensible default string.
*   **Feedback**: Provide clear emojis-based status updates (✅, ❌, ℹ️) in the terminal.

## Development Workflow

1.  **Environment**: Use `uv` for dependency management.
2.  **Testing**: Verify changes with actual audio generation tests.
3.  **Documentation**: Keep `llms.txt/` files updated with new features and architectural decisions.
