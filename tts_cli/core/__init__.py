"""
Core TTS CLI components.

This module contains the core functionality for the TTS CLI tool including:
- Model registry for dynamic model loading
- Environment manager for UV-based isolation
- Voice manager for voice listing and validation
- Model daemon for persistent shared model with PID-tracked inference queuing
- Daemon client for transparent daemon communication
"""
