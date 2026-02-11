"""
Daemon Client - Connects CLI invocations to the model daemon.

This module provides the client-side interface for communicating with the
model daemon.  When a CLI invocation needs TTS inference, it:

    1. Checks if the daemon is already running.
    2. If not, spawns it as a detached background process.
    3. Connects via Unix domain socket.
    4. Sends an inference request (tagged with the caller's PID).
    5. Blocks until the daemon returns a result.

All of this is transparent to the caller — they just call
``daemon_generate_speech()`` and get a bool back.
"""

from __future__ import annotations

import json
import os
import socket
import struct
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Optional

from .model_daemon import (
    DAEMON_DIR,
    LOG_PATH,
    SOCKET_PATH,
    MAX_MESSAGE_BYTES,
    _recv_json,
    _send_json,
    is_daemon_running,
)


# ---------------------------------------------------------------------------
# Daemon spawner
# ---------------------------------------------------------------------------


def _ensure_daemon_running(timeout: float = 30.0) -> bool:
    """Ensure the model daemon is running, spawning it if necessary.

    Uses double-fork daemonization so the daemon survives the death of any
    parent process (terminal, MCP server, IDE, etc.).  Stdout/stderr of the
    daemon are redirected to the daemon log file so library output is never
    lost.

    Returns True if the daemon is reachable, False on failure.
    """
    if is_daemon_running():
        return True

    DAEMON_DIR.mkdir(parents=True, exist_ok=True)

    # We launch via the same Python interpreter so the daemon shares our
    # installed packages (pocket_tts, scipy, etc.).
    daemon_module = "tts_cli.core.model_daemon"
    cmd = [sys.executable, "-m", daemon_module]

    # Double-fork to fully orphan the daemon:
    #   Parent → fork → child (exits immediately) → fork → grandchild (daemon)
    # The grandchild is adopted by init/launchd and cannot be affected by
    # the death of any ancestor process, terminal session, or IDE.
    try:
        pid = os.fork()
        if pid > 0:
            # Parent: wait for the intermediate child to exit (prevents zombie)
            os.waitpid(pid, 0)
        else:
            # ---- First child ----
            os.setsid()  # new session leader (detach from terminal)

            pid2 = os.fork()
            if pid2 > 0:
                # Intermediate child exits immediately
                os._exit(0)

            # ---- Grandchild (the actual daemon) ----
            # Redirect stdin/stdout/stderr to log / devnull
            devnull_r = os.open(os.devnull, os.O_RDONLY)
            log_fd = os.open(
                str(LOG_PATH), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600
            )
            os.dup2(devnull_r, 0)   # stdin  → /dev/null
            os.dup2(log_fd, 1)      # stdout → daemon.log
            os.dup2(log_fd, 2)      # stderr → daemon.log
            os.close(devnull_r)
            os.close(log_fd)

            os.execvp(cmd[0], cmd)  # replaces this process entirely

    except OSError as exc:
        print(f"Failed to spawn daemon: {exc}", file=sys.stderr)
        return False

    # Parent continues: poll until daemon is reachable or timeout
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(0.15)
        if is_daemon_running():
            return True

    print("Daemon did not become reachable within timeout.", file=sys.stderr)
    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def daemon_generate_speech(
    text: str,
    voice: str,
    output_path: str,
    voice_clone: Optional[str] = None,
    timeout: float = 120.0,
) -> bool:
    """Generate speech via the model daemon.

    Transparently starts the daemon if it is not running.  The caller's PID
    is attached to the request for tracking.

    Args:
        text: The text to synthesize.
        voice: Voice identifier (name or path).
        output_path: Where to write the output WAV file.
        voice_clone: Optional path to a reference audio for voice cloning.
        timeout: Maximum seconds to wait for inference completion.

    Returns:
        True on success, False on failure.
    """
    # 1. Ensure daemon is alive
    if not _ensure_daemon_running():
        return False

    caller_pid = os.getpid()
    request_id = str(uuid.uuid4())

    request_payload = {
        "type": "inference",
        "request_id": request_id,
        "pid": caller_pid,
        "text": text,
        "voice": voice,
        "output_path": output_path,
        "voice_clone": voice_clone,
    }

    # 2. Connect and send
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect(str(SOCKET_PATH))
        _send_json(sock, request_payload)

        # 3. Block until response
        resp = _recv_json(sock, timeout=timeout)
        if resp is None:
            print(
                f"[PID {caller_pid}] No response from daemon (timeout or disconnect).",
                file=sys.stderr,
            )
            return False

        if resp.get("success"):
            duration = resp.get("duration_ms", 0)
            print(
                f"[PID {caller_pid}] Inference complete in {duration:.0f}ms "
                f"→ {resp.get('output_path', output_path)}"
            )
            return True
        else:
            error = resp.get("error", "unknown error")
            print(
                f"[PID {caller_pid}] Inference failed: {error}",
                file=sys.stderr,
            )
            return False

    except ConnectionRefusedError:
        print(
            f"[PID {caller_pid}] Could not connect to daemon.",
            file=sys.stderr,
        )
        return False
    except socket.timeout:
        print(
            f"[PID {caller_pid}] Timed out waiting for inference result.",
            file=sys.stderr,
        )
        return False
    except Exception as exc:
        print(
            f"[PID {caller_pid}] Daemon communication error: {exc}",
            file=sys.stderr,
        )
        return False
    finally:
        try:
            sock.close()
        except OSError:
            pass
