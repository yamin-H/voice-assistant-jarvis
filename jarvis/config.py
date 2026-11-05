"""Loads settings from config.yaml."""
import os
from pathlib import Path

import yaml

# The main project folder (the one that contains config.yaml)
ROOT = Path(__file__).resolve().parent.parent


def load_config(path=None):
    path = Path(path) if path else ROOT / "config.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def cpu_threads(cfg):
    """How many CPU threads the assistant may use."""
    wanted = cfg["performance"]["cpu_threads"]
    if wanted and wanted > 0:
        return wanted
    total = os.cpu_count() or 2
    return max(1, int(total * 0.6))