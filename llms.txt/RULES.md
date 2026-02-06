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

## Extended Standards (from AGENTS.md)

### Agent Guidelines
*   **Approach**: Security-first, Zero Trust, Standardized
*   **Output**: Production-ready, tested, encrypted, PQC-compliant

### Coding Standards by Language

| Language | Standards |
|----------|-----------|
| Bash | `set -euo pipefail`, `[[ ]]`, `"${var}"` |
| Python | PEP 8, type hints, `uv`/`poetry`, `.venv` |
| TypeScript | strict mode, ESLint, Prettier |
| Rust | `cargo fmt`, `cargo clippy`, `Result` over panic |
| Go | `gofmt`, `go vet`, Effective Go |
| C++ | `clang-format`, `clang-tidy`, C++20, RAII |

### Security Specification

**Core Principles:**
*   **Zero Trust**: Verify every tool call; sanitize all inputs.
*   **Least Privilege**: Minimal permissions; scoped credentials per session.
*   **No hardcoded secrets**: Environment variables only, accessed via secure vault.
*   **Sandboxing**: Code execution via WASM/Firecracker only.
*   **Tool Misuse**: Strict schema validation (Zod/Pydantic) for all inputs.
*   **Identity Abuse**: Independent Permission Broker; short-lived tokens.
*   **Information Disclosure**: PII Redaction; Env var only secrets.
*   **Repudiation**: Structured immutable ledgers; remote logging.

**Data Protection & Encryption:**
*   **In Transit**: TLS 1.3+ with mTLS for inter-agent communication. Hybrid PQC Key Exchange: X25519 + ML-KEM-768 (FIPS 203).
*   **At Rest**: AES-256-GCM for databases and file storage. Tenant-specific keys for Vector DB embeddings. Encrypted logs with strict retention and PII redaction.

**Post-Quantum Cryptography (NIST FIPS Standards):**

| Purpose | Standard | Algorithm | Status (2026) |
|---------|----------|-----------|---------------|
| Key Encapsulation | FIPS 203 | ML-KEM-768/1024 | Standard |
| Digital Signatures | FIPS 204 | ML-DSA-65/87 | Standard |
| Hash-Based Sig | FIPS 205 | SLH-DSA | Standard |

### Git Commits
Format: `<type>(<scope>): <description>` — feat|fix|docs|refactor|test|chore|perf|ci
