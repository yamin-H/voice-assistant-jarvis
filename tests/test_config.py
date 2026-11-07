import os
import pytest
from jarvis.config import cpu_threads, get_data_dir, validate_env


def test_cpu_threads_explicit():
    cfg = {"performance": {"cpu_threads": 6}}
    assert cpu_threads(cfg) == 6


def test_cpu_threads_auto():
    cfg = {"performance": {"cpu_threads": 0}}
    threads = cpu_threads(cfg)
    assert isinstance(threads, int)
    assert threads >= 1


def test_get_data_dir_resolution(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    data_dir = get_data_dir()
    assert data_dir == tmp_path / "JarvisLite"
    assert data_dir.is_dir()


def test_validate_env_missing_groq_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    cfg = {"brain": {"engine": "groq"}}
    with pytest.raises(SystemExit):
        validate_env(cfg)


def test_validate_env_valid_groq_key(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_key_123")
    cfg = {"brain": {"engine": "groq"}}
    validate_env(cfg)  # Should not raise


def test_validate_env_ollama(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    cfg = {"brain": {"engine": "ollama"}}
    validate_env(cfg)  # Should not raise