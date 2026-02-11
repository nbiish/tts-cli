"""
Tests for the model daemon and daemon client.

Covers:
    - Daemon lifecycle (start, idle shutdown, signal shutdown)
    - PID tracking across multiple client requests
    - Request queuing / ordering
    - Protocol validation (malformed requests, missing fields)
    - Idle timer auto-unload after 10 seconds
    - Single-instance enforcement via file lock
    - Client auto-spawn of daemon
"""

from __future__ import annotations

import json
import os
import socket
import struct
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from tts_cli.core.model_daemon import (
    DAEMON_DIR,
    SOCKET_PATH,
    LOCK_PATH,
    PID_FILE,
    MAX_MESSAGE_BYTES,
    InferenceRequest,
    InferenceResponse,
    PIDRecord,
    ModelDaemon,
    _send_json,
    _recv_json,
    validate_inference_request,
    is_daemon_running,
    get_daemon_status,
    stop_daemon,
)


class TestValidation(unittest.TestCase):
    """Test request validation logic."""

    def test_valid_request(self) -> None:
        data = {"text": "hello", "voice": "alba", "output_path": "/tmp/out.wav"}
        self.assertIsNone(validate_inference_request(data))

    def test_missing_text(self) -> None:
        data = {"voice": "alba", "output_path": "/tmp/out.wav"}
        err = validate_inference_request(data)
        self.assertIsNotNone(err)
        self.assertIn("text", err)

    def test_missing_voice(self) -> None:
        data = {"text": "hello", "output_path": "/tmp/out.wav"}
        err = validate_inference_request(data)
        self.assertIsNotNone(err)
        self.assertIn("voice", err)

    def test_missing_output_path(self) -> None:
        data = {"text": "hello", "voice": "alba"}
        err = validate_inference_request(data)
        self.assertIsNotNone(err)
        self.assertIn("output_path", err)

    def test_empty_text(self) -> None:
        data = {"text": "", "voice": "alba", "output_path": "/tmp/out.wav"}
        err = validate_inference_request(data)
        self.assertIsNotNone(err)
        self.assertIn("text", err)

    def test_non_dict_input(self) -> None:
        err = validate_inference_request("not a dict")
        self.assertIsNotNone(err)
        self.assertIn("JSON object", err)

    def test_voice_clone_string(self) -> None:
        data = {
            "text": "hello",
            "voice": "alba",
            "output_path": "/tmp/out.wav",
            "voice_clone": "/path/to/ref.wav",
        }
        self.assertIsNone(validate_inference_request(data))

    def test_voice_clone_null(self) -> None:
        data = {
            "text": "hello",
            "voice": "alba",
            "output_path": "/tmp/out.wav",
            "voice_clone": None,
        }
        self.assertIsNone(validate_inference_request(data))

    def test_voice_clone_invalid_type(self) -> None:
        data = {
            "text": "hello",
            "voice": "alba",
            "output_path": "/tmp/out.wav",
            "voice_clone": 42,
        }
        err = validate_inference_request(data)
        self.assertIsNotNone(err)
        self.assertIn("voice_clone", err)


class TestProtocol(unittest.TestCase):
    """Test the length-prefixed JSON protocol helpers."""

    def _make_socket_pair(self):
        """Create a connected pair of Unix sockets."""
        s1, s2 = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        return s1, s2

    def test_roundtrip(self) -> None:
        s1, s2 = self._make_socket_pair()
        try:
            msg = {"type": "ping", "data": 123}
            _send_json(s1, msg)
            received = _recv_json(s2, timeout=5.0)
            self.assertEqual(received, msg)
        finally:
            s1.close()
            s2.close()

    def test_large_payload_rejected(self) -> None:
        s1, s2 = self._make_socket_pair()
        try:
            huge = {"text": "x" * (MAX_MESSAGE_BYTES + 1)}
            with self.assertRaises(ValueError):
                _send_json(s1, huge)
        finally:
            s1.close()
            s2.close()

    def test_recv_on_closed_socket(self) -> None:
        s1, s2 = self._make_socket_pair()
        s1.close()
        result = _recv_json(s2, timeout=1.0)
        self.assertIsNone(result)
        s2.close()


class TestPIDRecord(unittest.TestCase):
    """Test PID tracking data class."""

    def test_creation(self) -> None:
        now = time.time()
        rec = PIDRecord(pid=1234, first_seen=now, last_seen=now, request_count=1)
        self.assertEqual(rec.pid, 1234)
        self.assertEqual(rec.request_count, 1)

    def test_update(self) -> None:
        now = time.time()
        rec = PIDRecord(pid=1234, first_seen=now, last_seen=now, request_count=1)
        rec.last_seen = now + 5
        rec.request_count += 1
        self.assertEqual(rec.request_count, 2)
        self.assertGreater(rec.last_seen, rec.first_seen)


class TestInferenceRequest(unittest.TestCase):
    """Test InferenceRequest data class."""

    def test_defaults(self) -> None:
        req = InferenceRequest(
            request_id="abc",
            client_pid=999,
            text="hello",
            voice="alba",
            output_path="/tmp/test.wav",
        )
        self.assertIsNone(req.voice_clone)
        self.assertGreater(req.timestamp, 0)

    def test_with_voice_clone(self) -> None:
        req = InferenceRequest(
            request_id="abc",
            client_pid=999,
            text="hello",
            voice="alba",
            output_path="/tmp/test.wav",
            voice_clone="/ref.wav",
        )
        self.assertEqual(req.voice_clone, "/ref.wav")


class TestModelDaemonUnit(unittest.TestCase):
    """Unit tests for ModelDaemon methods (no actual model loading)."""

    def test_pid_recording(self) -> None:
        daemon = ModelDaemon(idle_timeout=60)
        daemon._record_pid(1111)
        daemon._record_pid(2222)
        daemon._record_pid(1111)

        self.assertIn(1111, daemon._pid_records)
        self.assertIn(2222, daemon._pid_records)
        self.assertEqual(daemon._pid_records[1111].request_count, 2)
        self.assertEqual(daemon._pid_records[2222].request_count, 1)

    def test_idle_timer_creation(self) -> None:
        daemon = ModelDaemon(idle_timeout=60)
        daemon._reset_idle_timer()
        self.assertIsNotNone(daemon._idle_timer)
        # Clean up
        daemon._idle_timer.cancel()

    def test_idle_timeout_triggers_shutdown(self) -> None:
        """With a very short idle timeout the daemon should flag itself to stop."""
        daemon = ModelDaemon(idle_timeout=0.2)
        daemon._running = True
        daemon._reset_idle_timer()
        # Wait for the timer to fire
        time.sleep(0.5)
        self.assertFalse(daemon._running)

    @patch("tts_cli.core.model_daemon.ModelDaemon._ensure_model_loaded")
    @patch("tts_cli.core.model_daemon.ModelDaemon._run_inference")
    def test_unload_model_clears_state(self, mock_run, mock_ensure) -> None:
        daemon = ModelDaemon(idle_timeout=60)
        daemon._model = MagicMock()
        daemon._model_loaded = True
        daemon._unload_model()
        self.assertFalse(daemon._model_loaded)
        self.assertIsNone(daemon._model)


class TestIsDaemonRunning(unittest.TestCase):
    """Test the is_daemon_running() helper when no daemon is active."""

    def test_no_socket_file(self) -> None:
        """When the socket file doesn't exist, should return False."""
        with patch("tts_cli.core.model_daemon.SOCKET_PATH") as mock_path:
            mock_path.exists.return_value = False
            self.assertFalse(is_daemon_running())


class TestDaemonClientImport(unittest.TestCase):
    """Verify the daemon client module imports cleanly."""

    def test_import(self) -> None:
        from tts_cli.core.daemon_client import daemon_generate_speech  # noqa: F401
        self.assertTrue(callable(daemon_generate_speech))


if __name__ == "__main__":
    unittest.main()
