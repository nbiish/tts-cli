# AGENTS.md

```xml
<agent>
Approach: Security-first, Zero Trust, Standardized
Output: Production-ready, tested, encrypted, PQC-compliant, secure by default

**End-of-Chat Voice Summary (MANDATORY):** Before yielding back to the operator at the end of your turn, ALWAYS speak a brief status update via `tts-cli`. This is not optional — it is how the operator (who may be away from the screen) tracks what every agent did across every repo.

- One command, spoken aloud:
  `cli-tts --text "<1-2 sentence concise summary of what was accomplished>. Next step: <ONE recommendation a decades-long hardened software & cybersecurity engineer would take as the single most logical next action.>"`
- The single suggestion must be concrete and adversarial-minded — the next hardening move, not a vague "consider": verify the boundary case, check the supply-chain provenance, lock down the secret, add the failing test, confirm the rollback/bisect path, fail-closed on the untrusted input, audit for the banned primitive, run the native linter + secret scan. Pick the ONE that most reduces risk or closes the loop.
- Keep stdout quiet — the spoken audio IS the channel; do not dump logs into the terminal.
- Default model is `index-tts` (IndexTTS-2.5, the sole engine). Use `--lang ZH|EN|JA|ES|AR` when the summary is non-English; `--voice <ref.wav>` only when a specific clone voice is set.
- If the `local-tts-mcp` MCP server is enabled in the harness, prefer it over the CLI.
- Skip only if `cli-tts` is unavailable or the operator has explicitly disabled audio for the session.
</agent>

<coding>
Universal Standards:
- Match existing codebase style
- Small, focused changes over rewrites
- Never create dummy, filler, or simulated code
- Never make waste files outside of the workspace
- Websearch, `fetch`, `curl`, etc the facts from online sources
- Well documented code saves lives and time

SOLID — A set of 5 object-oriented design principles:
- Single Responsibility — A class should do only one thing
- Open/Closed — Open for extension, closed for modification
- Liskov Substitution — Subclasses should be replaceable by their parent class
- Interface Segregation — Don't force classes to implement interfaces they don't need
- Dependency Inversion — Depend on abstractions, not concrete implementations

DRY — Don't Repeat Yourself:
- Avoid duplicating code/logic. If you write the same thing twice, extract it into a reusable function or module.

YAGNI — You Aren't Gonna Need It:
- Don't build features "just in case." Only code what you actually need right now.

KISS — Keep It Simple, Stupid:
- Don't over-engineer. The simplest solution that works is usually the best one.

By Language:
| Language | Standards |
|----------|-----------|
| Bash | `set -euo pipefail`, `[[ ]]`, `"${var}"` |
| Python | PEP 8, type hints, `uv`/`poetry`, `.venv` |
| TypeScript | strict mode, ESLint, Prettier |
| Rust | `cargo fmt`, `cargo clippy`, `Result` over panic |
| Go | `gofmt`, `go vet`, Effective Go |
| C++ | `clang-format`, `clang-tidy`, C++20, RAII |
</coding>

<security>
Core Principles:
Zero Trust: Verify every tool call; sanitize all inputs.
Least Privilege: Minimal permissions; scoped credentials per session.
No hardcoded secrets: Environment variables only, accessed via secure vault.
Sandboxing: Code execution via WASM/Firecracker only.
Tool Misuse: Strict schema validation (Zod/Pydantic) for all inputs.
Identity Abuse: Independent Permission Broker; short-lived tokens.
Information Disclosure: PII Redaction; Env var only secrets.
Repudiation: Structured immutable ledgers; remote logging.

Data Protection & Encryption:
In Transit:
TLS 1.3+ with mTLS for inter-agent communication.
Hybrid PQC Key Exchange: X25519 + ML-KEM-768 (FIPS 203).
At Rest:
AES-256-GCM for databases and file storage.
Tenant-specific keys for Vector DB embeddings.
Encrypted logs with strict retention and PII redaction.


Post-Quantum Crytography (NIST FIPS Standards)
| Purpose | Standard | Algorithm | Status (2026) |
|---------|----------|-----------|---------------|
| Key Encapsulation | FIPS 203 | ML-KEM-768/1024 | Standard |
| Digital Signatures | FIPS 204 | ML-DSA-65/87 | Standard |
| Hash-Based Sig | FIPS 205 | SLH-DSA | Standard |
</security>

Git Commits: `<type>(<scope>): <description>` — feat|fix|docs|refactor|test|chore|perf|ci
```
