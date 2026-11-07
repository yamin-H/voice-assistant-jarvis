"""Saves small bits of data (notes, reminders, memories) as JSON files in user data."""
import json
import os
from pathlib import Path
import threading

from jarvis.config import get_data_dir

_lock = threading.RLock()


def _data_path(name: str) -> Path:
    return get_data_dir() / f"{name}.json"


def load(name: str, default):
    """Reads <data_dir>/<name>.json. Returns `default` if it does not exist yet."""
    path = _data_path(name)
    with _lock:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return default
        except json.JSONDecodeError:
            # A damaged file: keep a copy so nothing is lost, then start fresh
            try:
                os.replace(path, path.with_suffix(".bad"))
            except OSError:
                pass
            return default


def save(name: str, data):
    """Writes <data_dir>/<name>.json safely (atomic write via temp file)."""
    with _lock:
        data_dir = get_data_dir()
        path = data_dir / f"{name}.json"
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(temp, path)