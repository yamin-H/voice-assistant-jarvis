"""Shared test fixtures for Jarvis Lite."""
import os
from pathlib import Path
import pytest


@pytest.fixture
def mock_data_dir(tmp_path, monkeypatch):
    """Redirects get_data_dir to a clean temporary path for test isolation."""
    monkeypatch.setattr("jarvis.config.get_data_dir", lambda: tmp_path)
    monkeypatch.setattr("jarvis.store.get_data_dir", lambda: tmp_path)
    return tmp_path


@pytest.fixture
def sample_config():
    """Provides a valid mock configuration dict."""
    return {
        "audio": {"sample_rate": 16000, "input_device": None, "output_device": None},
        "performance": {"cpu_threads": 4},
        "assistant": {"name": "Jarvis", "user_name": "TestUser"},
        "brain": {"engine": "ollama", "history_turns": 4},
        "wake": {
            "enabled": True,
            "threshold": 0.5,
            "listen_seconds": 8,
            "follow_up_seconds": 6,
            "threshold_while_busy": 0.7,
        },
        "stt": {"engine": "moonshine", "speech_level": 0.02},
        "tts": {"engine": "piper"},
        "vision": {"enabled": False},
        "agent": {
            "enabled": False,
            "voice_enabled": False,
            "max_steps": 6,
            "execution": {"allow_low_risk": True},
        },
    }