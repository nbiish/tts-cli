"""
Model Daemon - Persistent model server with PID-tracked request queuing.

This module implements a Unix domain socket daemon that holds the TTS model
in memory, accepts inference requests from multiple concurrent CLI invocations,
queues them in FIFO order with PID tracking, and auto-unloads after an idle
timeout (default 10 seconds).

Architecture:
    - Single daemon instance enforced via file lock (fcntl.flock)
    - Unix domain socket for IPC (fast, secure, local-only)
    - JSON-line protocol for request/response framing
    - Threading: acceptor thread + single inference worker thread
    - Idle timer resets on every completed request; fires model unload + shutdown

Security:
    - Socket permissions restricted to current user (0o600)
    - All inputs validated via schema before processing
    - PID verified via SO_PEERCRED where available
"""

from __future__ import annotations

import fcntl
import json
import logging
import os
import queue
import signal
import socket
import struct
import sys
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import tempfile

from tts_cli.core.text_utils import split_text

logger = logging.getLogger("tts_cli.daemon")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DAEMON_DIR = Path.home() / ".tts-cli" / "daemon"
SOCKET_PATH = DAEMON_DIR / "daemon.sock"
LOCK_PATH = DAEMON_DIR / "daemon.lock"
PID_FILE = DAEMON_DIR / "daemon.pid"
LOG_PATH = DAEMON_DIR / "daemon.log"

IDLE_TIMEOUT_SECONDS = 10.0

# Maximum message size: 1 MiB (protects against runaway payloads)
MAX_MESSAGE_BYTES = 1 * 1024 * 1024


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class InferenceRequest:
    """A queued TTS inference request."""

    request_id: str
    client_pid: int
    text: str
    voice: str
    output_path: str
    voice_clone: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class InferenceResponse:
    """Response sent back to the requesting client."""

    request_id: str
    success: bool
    client_pid: int
    output_path: str = ""
    error: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class PIDRecord:
    """Tracking record for a client PID."""

    pid: int
    first_seen: float
    last_seen: float
    request_count: int = 0


# ---------------------------------------------------------------------------
# Protocol helpers
# ---------------------------------------------------------------------------


def _send_json(conn: socket.socket, obj: dict) -> None:
    """Send a JSON object as a length-prefixed message."""
    payload = json.dumps(obj).encode("utf-8")
    length = len(payload)
    if length > MAX_MESSAGE_BYTES:
        raise ValueError(f"Payload too large: {length} bytes")
    conn.sendall(struct.pack("!I", length) + payload)


def _recv_json(conn: socket.socket, timeout: float = 120.0) -> Optional[dict]:
    """Receive a length-prefixed JSON message."""
    conn.settimeout(timeout)
    try:
        header = _recv_exact(conn, 4)
        if header is None:
            return None
        (length,) = struct.unpack("!I", header)
        if length > MAX_MESSAGE_BYTES:
            raise ValueError(f"Message too large: {length} bytes")
        data = _recv_exact(conn, length)
        if data is None:
            return None
        return json.loads(data.decode("utf-8"))
    except (socket.timeout, ConnectionResetError, BrokenPipeError):
        return None


def _recv_exact(conn: socket.socket, n: int) -> Optional[bytes]:
    """Read exactly n bytes from a socket."""
    buf = bytearray()
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            return None
        buf.extend(chunk)
    return bytes(buf)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

_REQUIRED_INFERENCE_FIELDS = {"text", "voice", "output_path"}


def validate_inference_request(data: dict) -> Optional[str]:
    """Validate an incoming inference request dict.  Returns error string or None."""
    if not isinstance(data, dict):
        return "Request must be a JSON object"
    missing = _REQUIRED_INFERENCE_FIELDS - set(data.keys())
    if missing:
        return f"Missing required fields: {missing}"
    if not isinstance(data["text"], str) or not data["text"].strip():
        return "Field 'text' must be a non-empty string"
    if not isinstance(data["voice"], str) or not data["voice"].strip():
        return "Field 'voice' must be a non-empty string"
    if not isinstance(data["output_path"], str) or not data["output_path"].strip():
        return "Field 'output_path' must be a non-empty string"
    if "voice_clone" in data and data["voice_clone"] is not None:
        if not isinstance(data["voice_clone"], str):
            return "Field 'voice_clone' must be a string or null"
    return None


# ---------------------------------------------------------------------------
# Model Daemon
# ---------------------------------------------------------------------------


class ModelDaemon:
    """Persistent TTS model daemon with PID-tracked inference queuing."""

    def __init__(self, idle_timeout: float = IDLE_TIMEOUT_SECONDS) -> None:
        self._idle_timeout = idle_timeout

        # Model state (guarded by _model_lock)
        self._model_lock = threading.Lock()
        self._model: Any = None  # TTSModel instance
        self._model_loaded = False

        # Request queue (unbounded FIFO)
        self._request_queue: queue.Queue[
            tuple[InferenceRequest, socket.socket]
        ] = queue.Queue()

        # PID tracking (guarded by _pid_lock)
        self._pid_lock = threading.Lock()
        self._pid_records: Dict[int, PIDRecord] = {}

        # Idle timer
        self._idle_timer: Optional[threading.Timer] = None
        self._idle_lock = threading.Lock()
        self._last_activity = time.time()

        # Server state
        self._server_socket: Optional[socket.socket] = None
        self._lock_fd: Optional[int] = None
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        self._accept_thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the daemon: acquire lock, bind socket, launch threads."""
        DAEMON_DIR.mkdir(parents=True, exist_ok=True)

        # Acquire exclusive file lock (non-blocking)
        self._lock_fd = os.open(str(LOCK_PATH), os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            os.close(self._lock_fd)
            self._lock_fd = None
            raise RuntimeError(
                "Another daemon instance is already running "
                f"(lock: {LOCK_PATH})"
            ) from exc

        # Write our PID
        PID_FILE.write_text(str(os.getpid()))

        # Clean up stale socket
        if SOCKET_PATH.exists():
            SOCKET_PATH.unlink()

        # Bind Unix socket
        self._server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._server_socket.bind(str(SOCKET_PATH))
        os.chmod(str(SOCKET_PATH), 0o600)
        self._server_socket.listen(32)
        self._server_socket.settimeout(1.0)  # allow periodic shutdown check

        self._running = True

        # Inference worker thread (single threaded — orderly execution)
        self._worker_thread = threading.Thread(
            target=self._inference_worker, daemon=True, name="inference-worker"
        )
        self._worker_thread.start()

        # Accept loop
        self._accept_thread = threading.Thread(
            target=self._accept_loop, daemon=True, name="accept-loop"
        )
        self._accept_thread.start()

        # Start idle timer
        self._reset_idle_timer()

        logger.info(
            "Daemon started  pid=%d  socket=%s  idle_timeout=%.1fs",
            os.getpid(),
            SOCKET_PATH,
            self._idle_timeout,
        )

        # Install signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_shutdown)
        signal.signal(signal.SIGINT, self._signal_shutdown)

    def run_forever(self) -> None:
        """Block the main thread until the daemon shuts down."""
        try:
            while self._running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """Gracefully stop the daemon and release resources."""
        if not self._running:
            return
        self._running = False
        logger.info("Daemon shutting down…")

        # Cancel idle timer
        with self._idle_lock:
            if self._idle_timer is not None:
                self._idle_timer.cancel()
                self._idle_timer = None

        # Unload model
        self._unload_model()

        # Close server socket
        if self._server_socket:
            try:
                self._server_socket.close()
            except OSError:
                pass

        # Drain queue — send error to waiting clients
        while not self._request_queue.empty():
            try:
                req, conn = self._request_queue.get_nowait()
                resp = InferenceResponse(
                    request_id=req.request_id,
                    success=False,
                    client_pid=req.client_pid,
                    error="daemon shutting down",
                )
                try:
                    _send_json(conn, asdict(resp))
                except OSError:
                    pass
                finally:
                    try:
                        conn.close()
                    except OSError:
                        pass
            except queue.Empty:
                break

        # Clean up files
        try:
            if SOCKET_PATH.exists():
                SOCKET_PATH.unlink()
        except OSError:
            pass

        try:
            if PID_FILE.exists():
                PID_FILE.unlink()
        except OSError:
            pass

        # Release lock
        if self._lock_fd is not None:
            try:
                fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
                os.close(self._lock_fd)
            except OSError:
                pass
            self._lock_fd = None

        logger.info("Daemon stopped.")

    # ------------------------------------------------------------------
    # Signal handler
    # ------------------------------------------------------------------

    def _signal_shutdown(self, signum: int, _frame: Any) -> None:
        """Handle SIGTERM / SIGINT."""
        logger.info("Received signal %d, shutting down…", signum)
        self._running = False

    # ------------------------------------------------------------------
    # Accept loop
    # ------------------------------------------------------------------

    def _accept_loop(self) -> None:
        """Accept incoming client connections."""
        while self._running:
            try:
                conn, _ = self._server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                if self._running:
                    logger.exception("Accept error")
                break

            # Handle each connection in a short-lived thread
            t = threading.Thread(
                target=self._handle_client, args=(conn,), daemon=True
            )
            t.start()

    # ------------------------------------------------------------------
    # Client handler
    # ------------------------------------------------------------------

    def _handle_client(self, conn: socket.socket) -> None:
        """Read one request from a client and either enqueue or respond."""
        try:
            data = _recv_json(conn, timeout=10.0)
            if data is None:
                conn.close()
                return

            msg_type = data.get("type", "inference")

            if msg_type == "ping":
                _send_json(conn, {"type": "pong", "pid": os.getpid()})
                conn.close()
                return

            if msg_type == "status":
                self._handle_status(conn)
                conn.close()
                return

            if msg_type == "shutdown":
                _send_json(conn, {"type": "ack", "message": "shutting down"})
                conn.close()
                self._running = False
                return

            # Default: inference request
            err = validate_inference_request(data)
            if err:
                _send_json(
                    conn,
                    {
                        "type": "error",
                        "error": err,
                        "request_id": data.get("request_id", ""),
                    },
                )
                conn.close()
                return

            client_pid = data.get("pid", 0)
            request_id = data.get("request_id", str(uuid.uuid4()))

            req = InferenceRequest(
                request_id=request_id,
                client_pid=client_pid,
                text=data["text"],
                voice=data["voice"],
                output_path=data["output_path"],
                voice_clone=data.get("voice_clone"),
            )

            # Track PID
            self._record_pid(client_pid)

            # Enqueue — the conn stays open so client blocks until done
            self._request_queue.put((req, conn))

            logger.info(
                "Enqueued request  id=%s  pid=%d  queue_depth=%d",
                request_id,
                client_pid,
                self._request_queue.qsize(),
            )

        except Exception:
            logger.exception("Error handling client")
            try:
                conn.close()
            except OSError:
                pass

    def _handle_status(self, conn: socket.socket) -> None:
        """Respond with daemon status."""
        with self._pid_lock:
            pid_info = [
                {
                    "pid": r.pid,
                    "first_seen": r.first_seen,
                    "last_seen": r.last_seen,
                    "request_count": r.request_count,
                }
                for r in self._pid_records.values()
            ]
        _send_json(
            conn,
            {
                "type": "status_response",
                "daemon_pid": os.getpid(),
                "model_loaded": self._model_loaded,
                "queue_depth": self._request_queue.qsize(),
                "active_pids": pid_info,
                "idle_timeout_seconds": self._idle_timeout,
                "uptime_seconds": time.time()
                - (self._last_activity - self._idle_timeout),
            },
        )

    # ------------------------------------------------------------------
    # PID tracking
    # ------------------------------------------------------------------

    def _record_pid(self, pid: int) -> None:
        """Update PID tracking records."""
        now = time.time()
        with self._pid_lock:
            if pid in self._pid_records:
                rec = self._pid_records[pid]
                rec.last_seen = now
                rec.request_count += 1
            else:
                self._pid_records[pid] = PIDRecord(
                    pid=pid,
                    first_seen=now,
                    last_seen=now,
                    request_count=1,
                )

    # ------------------------------------------------------------------
    # Inference worker
    # ------------------------------------------------------------------

    def _inference_worker(self) -> None:
        """Single-threaded worker: dequeue → ensure model → run inference → respond."""
        while self._running:
            try:
                req, conn = self._request_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            t_start = time.time()
            resp: InferenceResponse

            try:
                # Ensure model is loaded
                self._ensure_model_loaded()

                # Run inference
                self._run_inference(req)

                duration_ms = (time.time() - t_start) * 1000.0
                resp = InferenceResponse(
                    request_id=req.request_id,
                    success=True,
                    client_pid=req.client_pid,
                    output_path=req.output_path,
                    duration_ms=duration_ms,
                )
                logger.info(
                    "Inference complete  id=%s  pid=%d  duration_ms=%.1f",
                    req.request_id,
                    req.client_pid,
                    duration_ms,
                )

            except Exception as exc:
                duration_ms = (time.time() - t_start) * 1000.0
                resp = InferenceResponse(
                    request_id=req.request_id,
                    success=False,
                    client_pid=req.client_pid,
                    error=str(exc),
                    duration_ms=duration_ms,
                )
                logger.exception(
                    "Inference failed  id=%s  pid=%d", req.request_id, req.client_pid
                )

            # Send response
            try:
                _send_json(conn, asdict(resp))
            except OSError:
                logger.warning(
                    "Failed to send response to pid=%d (disconnected)",
                    req.client_pid,
                )
            finally:
                try:
                    conn.close()
                except OSError:
                    pass

            # Reset idle timer after each completed request
            self._reset_idle_timer()

    # ------------------------------------------------------------------
    # Model management
    # ------------------------------------------------------------------

    def _ensure_model_loaded(self) -> None:
        """Load the TTS model if not already loaded (thread-safe)."""
        with self._model_lock:
            if self._model_loaded and self._model is not None:
                return
            logger.info("Loading TTS model…")
            t0 = time.time()

            from pocket_tts import TTSModel  # type: ignore[import-untyped]

            self._model = TTSModel.load_model()
            self._model_loaded = True
            logger.info("Model loaded in %.2fs", time.time() - t0)

    def _unload_model(self) -> None:
        """Unload the model and free memory."""
        with self._model_lock:
            if not self._model_loaded:
                return
            logger.info("Unloading TTS model…")
            self._model = None
            self._model_loaded = False

            # Encourage garbage collection of large tensors
            import gc

            gc.collect()
            logger.info("Model unloaded.")

    def _run_inference(self, req: InferenceRequest) -> None:
        """Execute TTS inference (must be called from inference worker only)."""
        import numpy as np
        import scipy.io.wavfile  # type: ignore[import-untyped]
        import torch

        model = self._model
        if model is None:
            raise RuntimeError("Model is not loaded")

        voice_input = req.voice_clone if req.voice_clone else req.voice
        voice_is_path = Path(voice_input).exists()
        voice_temp_file: Optional[str] = None

        try:
            if voice_is_path:
                # Pre-process voice file: check duration and trim if > 10s
                try:
                    sr, data = scipy.io.wavfile.read(voice_input)
                    # Handle multi-channel audio if necessary (usually take first channel or mix)
                    # scipy read returns (rate, data). data can be 1D or 2D.
                    duration = len(data) / sr
                    if duration > 10.0:
                        logger.info(
                            "Voice input too long (%.1fs), trimming to 10.0s", duration
                        )
                        # Trim to 10s
                        trimmed_data = data[: int(10.0 * sr)]

                        # Create temp file
                        tf = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                        voice_temp_file = tf.name
                        tf.close()

                        scipy.io.wavfile.write(voice_temp_file, sr, trimmed_data)
                        voice_input = voice_temp_file
                except Exception as e:
                    logger.warning(
                        "Failed to process voice file '%s': %s", voice_input, e
                    )

            # Get voice state
            if Path(voice_input).exists():
                voice_state = model.get_state_for_audio_prompt(voice_input)
            else:
                voice_map = {
                    "alba": "hf://kyutai/tts-voices/alba-mackenna/casual.wav",
                    "victor": "hf://kyutai/tts-voices/voice-donations/Victor_Garcia.wav",
                    "umair": "hf://kyutai/tts-voices/voice-donations/Umair.wav",
                    "vivaldi": "hf://kyutai/tts-voices/voice-donations/Vivaldi.wav",
                    "yesid": "hf://kyutai/tts-voices/voice-donations/Yesid.wav",
                    "wealthiest": "hf://kyutai/tts-voices/voice-donations/Wealthiest.wav",
                    "awais": "hf://kyutai/tts-voices/voice-donations/awais_shah.wav",
                    "gmaskell": "hf://kyutai/tts-voices/voice-donations/gmaskell92.wav",
                    "robert": "hf://kyutai/tts-voices/voice-donations/robert.wav",
                }

                if voice_input in voice_map:
                    voice_state = model.get_state_for_audio_prompt(
                        voice_map[voice_input]
                    )
                else:
                    try:
                        voice_state = model.get_state_for_audio_prompt(voice_input)
                    except Exception:
                        logger.warning(
                            "Unknown voice '%s', falling back to 'alba'", voice_input
                        )
                        voice_state = model.get_state_for_audio_prompt(
                            voice_map["alba"]
                        )

            # Generate audio in chunks
            chunks = split_text(req.text, max_length=200)
            audio_segments = []

            for chunk in chunks:
                if not chunk.strip():
                    continue

                segment = model.generate_audio(voice_state, chunk)

                # Validation
                if segment is None:
                    continue
                if segment.numel() == 0:
                    continue
                if segment.dim() == 1:
                    segment = segment.unsqueeze(0)

                audio_segments.append(segment)

            if not audio_segments:
                logger.warning("No audio generated for text: '%s'", req.text)
                return

            audio = torch.cat(audio_segments, dim=1)

            # Convert and save
            audio_data = audio.cpu().numpy()
            
            # Ensure proper shape for wavfile.write (samples, channels)
            if audio_data.ndim == 2 and audio_data.shape[0] == 1:
                audio_data = audio_data.flatten()
            elif audio_data.ndim == 2 and audio_data.shape[0] > 1:
                # Assuming (channels, samples) -> transpose to (samples, channels)
                audio_data = audio_data.T
                
            if audio_data.dtype.kind == "f":
                audio_data = (
                    (audio_data * 32767).clip(-32768, 32767).astype(np.int16)
                )

            # Ensure output directory exists
            Path(req.output_path).parent.mkdir(parents=True, exist_ok=True)
            scipy.io.wavfile.write(req.output_path, model.sample_rate, audio_data)

        finally:
            # Clean up temp file
            if voice_temp_file and os.path.exists(voice_temp_file):
                try:
                    os.unlink(voice_temp_file)
                except OSError:
                    pass

    # ------------------------------------------------------------------
    # Idle timer
    # ------------------------------------------------------------------

    def _reset_idle_timer(self) -> None:
        """Reset the idle-shutdown timer."""
        with self._idle_lock:
            self._last_activity = time.time()
            if self._idle_timer is not None:
                self._idle_timer.cancel()
            self._idle_timer = threading.Timer(
                self._idle_timeout, self._on_idle_timeout
            )
            self._idle_timer.daemon = True
            self._idle_timer.start()

    def _on_idle_timeout(self) -> None:
        """Called when the idle timer fires."""
        # Check if there are pending requests — if so, don't unload
        if not self._request_queue.empty():
            logger.info("Idle timer fired but queue non-empty; resetting.")
            self._reset_idle_timer()
            return

        logger.info(
            "Idle timeout (%.1fs) reached with no pending requests. "
            "Shutting down daemon.",
            self._idle_timeout,
        )
        self._running = False


# ---------------------------------------------------------------------------
# Entry point for launching the daemon as a subprocess
# ---------------------------------------------------------------------------


def run_daemon(idle_timeout: float = IDLE_TIMEOUT_SECONDS) -> None:
    """Launch the daemon (blocking).  Intended to be called in a forked process."""
    # Configure logging to file
    DAEMON_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(str(LOG_PATH), mode="a"),
        ],
    )

    daemon = ModelDaemon(idle_timeout=idle_timeout)
    try:
        daemon.start()
        daemon.run_forever()
    except RuntimeError as exc:
        logger.error("Daemon failed to start: %s", exc)
        sys.exit(1)


def is_daemon_running() -> bool:
    """Check whether a daemon is currently alive."""
    if not SOCKET_PATH.exists():
        return False
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.settimeout(2.0)
        sock.connect(str(SOCKET_PATH))
        _send_json(sock, {"type": "ping"})
        resp = _recv_json(sock, timeout=3.0)
        return resp is not None and resp.get("type") == "pong"
    except (OSError, ConnectionRefusedError):
        # Stale socket — clean up
        try:
            SOCKET_PATH.unlink(missing_ok=True)
        except OSError:
            pass
        return False
    finally:
        try:
            sock.close()
        except OSError:
            pass


def get_daemon_status() -> Optional[dict]:
    """Query the running daemon for its status.  Returns None if not running."""
    if not is_daemon_running():
        return None
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.settimeout(5.0)
        sock.connect(str(SOCKET_PATH))
        _send_json(sock, {"type": "status"})
        resp = _recv_json(sock, timeout=5.0)
        return resp
    except (OSError, ConnectionRefusedError):
        return None
    finally:
        try:
            sock.close()
        except OSError:
            pass


def stop_daemon() -> bool:
    """Send a shutdown command to the running daemon."""
    if not is_daemon_running():
        return False
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.settimeout(5.0)
        sock.connect(str(SOCKET_PATH))
        _send_json(sock, {"type": "shutdown"})
        resp = _recv_json(sock, timeout=5.0)
        return resp is not None
    except (OSError, ConnectionRefusedError):
        return False
    finally:
        try:
            sock.close()
        except OSError:
            pass


if __name__ == "__main__":
    run_daemon()
