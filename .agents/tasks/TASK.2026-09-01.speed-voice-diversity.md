# TASK 2026-09-01 — CLI-owned 1.8× readout, random voice, fire-and-forget

**Branch (this plan):** `docs/tts-cli-speed-voice-diversity`
**Worktree:** `../tts-cli-speed-voice-diversity`
**Implement next chat on:** `feat/tts-cli-speed-voice-diversity` from `main` (new worktree; do not reuse this docs branch for code)
**Classification:** Confidential — no secrets

## Goal

Treat `cli-tts` as a **singular speak system**. Agents make **one** `--prompt`
call and do **not** choose a voice, a playback rate, or a wait. The CLI itself:

1. Reads the content out at **heard rate 1.8×**.
2. On every generation with `--voice` omitted, picks **uniformly at random**
   from the eight KittenTTS built-in voices so successive readings differ.
3. **Does not block the agent.** Launch speak and continue. Do not wait for
   generation or playback to finish. The operator can read the chat or the
   ledger if a phrase is missed.

This chat **plans only** (docs + this task). Next chat implements CLI + tests,
then copies the skill into consuming repos (ainish-coder, wtf-is-going-on-mcp).

## Why CLI-owned (not agent-owned flags)

Today agents already omit `--voice` (default `expr-voice-5-m`) and hear
`play_audio(..., speed=1.2)` on macOS (`afplay --rate`). If we prompt every
agent to pass `--speed 1.8 --voice <pick>`, they will loop, pick favorites,
or forget. The operator asked for a **singular system**: one invocation, the
tool applies tempo + diversity.

`--voice NAME` stays an **operator override**. Unknown names stay fail-closed.

## Current code (do not treat as the target)

| Surface | Today | Target |
| :--- | :--- | :--- |
| Heard tempo | `play_audio` default **1.2×** (`tts_cli/cli.py`); KittenTTS generate `speed` **1.0** | Heard **1.8×** without stacking 1.8× generate × 1.2× play |
| Voice when `--voice` omitted | `DEFAULT_VOICE = "expr-voice-5-m"` (`kitten_tts_model.py`) | `secrets.choice(BUILT_IN_VOICES)` once per generation |
| Agent `--prompt` | No `--voice` / no `--speed` flag exists on argparse | Still omit both; CLI fills them in |
| Agent wait | `play_audio` **blocks** on `afplay`/`ffplay`/`PlaySync`; generate blocks too | Parent **returns immediately** after accepting the job; child generates, logs, plays |
| Windows play | PowerShell `SoundPlayer` — **no rate** | WAV must already be 1.8× **or** Windows stays slow |

## Heard-rate design (pick this in the implement chat)

**Bake 1.8 into KittenTTS generate `speed`, set `play_audio` default to 1.0.**

- One knob. The WAV itself is 1.8×. macOS / Linux / Windows all hear it.
- Do **not** leave `play_audio` at 1.2 while generating at 1.8 (that stacks to ~2.16×).
- Operator chose **1.8×** (was 1.4×) to save listen time; missing a phrase is acceptable — the chat transcript and `AGENTS-TTS-COMMS.txt` remain.
- Verify KittenTTS nano accepts `speed=1.8`. If the runner rejects or sounds broken, fall back: generate `1.0` + `play_audio` `1.8` on Darwin/`ffplay`, and document Windows as best-effort.
- Optional argparse `--speed` for operators; default 1.8. Agents must not pass it.

Constant: `DEFAULT_PLAYBACK_RATE = 1.8` (generate) and `PLAY_AUDIO_RATE = 1.0` (player), or one named `HEARD_SPEED = 1.8` applied only in generate.

## Fire-and-forget design (blocking is a bug)

Today `play_audio` uses `subprocess.run(..., check=True)` so the CLI (and any
agent waiting on it) sits until the last sample plays. Long `--prompt` bodies
are several minutes. The operator does not want agents to wait.

**CLI default: detach.** After fail-closed validation (empty / overlong text,
bad `--voice`), the parent process starts a child and **exits 0 immediately**.
The child generates, appends the ledger, and plays. No warm daemon — the
child is still one-shot and exits when done.

- Unix: `os.fork` + `os.setsid` (or re-exec `cli-tts --wait ...` with
  `start_new_session=True`) so SIGHUP does not kill playback when the parent
  exits.
- Windows: `subprocess.Popen(..., creationflags=DETACHED_PROCESS |
  CREATE_NEW_PROCESS_GROUP)` re-exec with `--wait`.
- `play_audio` in the child must also **not** block the child longer than
  needed if we later want generate-then-detach-play; for `--wait`, waiting
  on the player is OK.
- `--wait` (operator / tests / smoke): current synchronous path. Pytest
  uses `--wait`.
- Agent `--prompt` never passes `--wait`.
- Stdout stays quiet. Do not print "Playing audio..." on the agent path
  (debug logger only). Failures after detach are not on the agent's wait
  path; ledger absence is the signal (`cli-tts --last-suggestion`).

**Until that CLI lands:** agents still must not wait. Launch `cli-tts` in
the background (`&`, or harness `block_until_ms: 0`) and continue. Do not
poll. Do not wait on the shell.

## Random voice design

When `voice` is `None` / omitted:

```python
import secrets
chosen_voice = secrets.choice(BUILT_IN_VOICES)
```

- Use `secrets.choice` (stdlib CSPRNG). Not `random.choice` for this pick —
  no extra dependency; not a secrets-bundle operation.
- Pick **once per `generate_speech` call** so all KittenTTS chunks of one
  `--prompt` share the same voice.
- `--voice expr-voice-3-f` still pins that name; unknown still fails closed
  (existing test `test_unknown_voice_fail_closed`).
- Do **not** write the voice name into `AGENTS-TTS-COMMS.txt` (ledger stays
  suggestion text only). Keep stdout quiet on the agent speak path — do not
  print the chosen voice on `--prompt` (debug logger only).

Drop “default `expr-voice-5-m`” from agent-facing docs. Keep the eight names
for `--list-voices` and operator `--voice`.

## Agent prompt (binding copy — install next chat)

Agents already use one HEREDOC `--prompt`. Add this rule everywhere they are
told to speak. **Do not** add `--voice` or `--speed` to the HEREDOC.

### `AGENTS.md` `<OUTPUT>` — add after the HEREDOC

```
- **Singular system.** One `cli-tts --prompt` is the whole speak path. Do not
  pass `--voice` or `--speed`. Do not pick a favorite voice. Do not loop
  voices or call `cli-tts` per master. The CLI reads out at 1.8× and, when
  `--voice` is omitted, chooses one of the eight built-in voices at random
  for that call. `--voice NAME` is an operator override only.
- **Do not wait.** Launch the one `--prompt` call and continue immediately.
  Do not wait for generation or playback. Do not poll the process. Next chat:
  CLI default is detach (parent exits 0; `--wait` for tests). Until then,
  background the command (`&` / harness non-blocking). Missed speech is
  acceptable — read the chat or the ledger.
```

Trim the Model bullet so it no longer says “default `expr-voice-5-m`” as the
agent path. Keep: eight fixed voices, `--list-voices`, fail-closed unknown
names, English-only, kitten-tts-nano.

### `.agents/skills/tts-cli/SKILL.md`

- YAML `description`: mention CLI-owned 1.8× tempo and per-call random voice;
  agents omit `--voice` / `--speed`. **No MCP wording.**
- §1: same singular-system paragraph as OUTPUT.
- §3 table: “Choose voice” stays an operator row (`--voice NAME`); agent
  summary row stays `--prompt` only.
- §4: remove “← default” on `expr-voice-5-m`. State: omitted `--voice` →
  random among the eight; `--voice` pins; unknown fails closed.

### `llms.txt` User Preferences

Replace the current end-of-chat bullet with one that includes: one `--prompt`;
eleven masters; CLI-owned 1.8× + random voice; never pass `--voice`/`--speed`
on the agent call.

## Implement-chat file list

Code (Python, native language — do not rewrite the stack):

- `tts_cli/cli.py` — `play_audio` default 1.0 once generate carries 1.8; wire
  generate `speed`; omit-voice path does not pin `expr-voice-5-m` at argparse;
  **default detach** after validation (parent exit 0); `--wait` for sync;
  do not `subprocess.run` the player on the agent path.
- `tts_cli/models/kitten_tts_model.py` — omit-voice → `secrets.choice`;
  default generate speed 1.8; still fail-closed on unknown names.
- `testing/test_kitten_tts_validation.py` — omit voice still spawns; monkeypatch
  `secrets.choice` to a fixed name and assert JSON payload `voice`; unknown
  still refused; generate speed 1.8 in payload.
- `testing/test_play_audio_rate.py` (new) — `play_audio` default does not
  stack a second 1.8× if generate already baked it in (assert default arg).
- `testing/test_detach.py` (new) — default `--prompt` returns before playback
  would finish; `--wait` still runs generate; no `mcp` in skill.
- `testing/test_skill_cli_only.py` — still no `mcp` in the skill; skill text
  says omit `--voice` / `--speed` and do not wait.

Docs (promote the planned copy; delete “planned/next chat” hedges):

- `AGENTS.md` `<OUTPUT>`
- `.agents/skills/tts-cli/SKILL.md`
- `llms.txt`
- `README.md` (Voices + Available Models bullets)
- `INSTALLATION.md` (Voices)
- `MCP_AUDIO_GUIDE.md` (quick-ref voice row: operator override, not agent default)

Out of scope unless it is one sentence:

- `repo_docs/PRD.md` is stale (IndexTTS). Do not revive IndexTTS. Optional
  one-liner under UX: agent speak is CLI-owned 1.8× + random voice.
- `TTS_CLI_MIGRATION_GUIDE.md` / hybrid docs — leave.

After tts-cli merge: copy skill + OUTPUT to ainish-coder and the skill to
wtf-is-going-on-mcp (same as the CLI-only skill copy). No `/Volumes/` in
ainish-coder task files.

## Verification (implement chat)

```bash
python -m pytest testing/test_kitten_tts_validation.py testing/test_skill_cli_only.py -q --no-cov
# Smoke (worktree, engine env present): two --text calls, different voices in runner logs; heard tempo 1.8
```

Do not commit `AGENTS-TTS-COMMS.txt` noise from smokes unless it is the
speak-contract demo. Ask before merge.

## Non-goals

- No TTS MCP. Skill stays MCP-free (`test_skill_cli_only.py`).
- No per-expert `cli-tts` calls. No voice-clone on the agent path.
- Do not log chosen voice into the public ledger.
- Do not implement in this docs worktree.

## Done when (this planning chat)

- This task file exists and names every file the implement chat will touch.
- Agent-facing docs in this branch tell agents: one `--prompt`, omit
  `--voice`/`--speed`, **do not wait**, CLI will own 1.8× + random + detach
  (implement next chat).
- No `cli.py` / model behavior change in this branch.
