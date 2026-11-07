"""Loads settings from config.yaml, manages data directories, and validates the environment."""
import os
from pathlib import Path
import shutil

import yaml
from dotenv import load_dotenv

# The main project folder (the one that contains config.yaml)
ROOT = Path(__file__).resolve().parent.parent

# Load .env from the project root if it exists
load_dotenv(ROOT / ".env")


def get_data_dir() -> Path:
    """Return the platform-appropriate user data directory.

    On Windows: %APPDATA%/JarvisLite (e.g., C:/Users/<User>/AppData/Roaming/JarvisLite)
    Fallback/Linux/macOS: ~/.jarvis-lite
    """
    appdata = os.environ.get("APPDATA")
    if appdata:
        data_dir = Path(appdata) / "JarvisLite"
    else:
        data_dir = Path.home() / ".jarvis-lite"

    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def migrate_legacy_data():
    """Migrate legacy project-root 'data/' files to %APPDATA%/JarvisLite if present."""
    legacy_dir = ROOT / "data"
    if not legacy_dir.exists() or not legacy_dir.is_dir():
        return

    new_dir = get_data_dir()
    for item in legacy_dir.iterdir():
        dest = new_dir / item.name
        if not dest.exists():
            try:
                if item.is_dir():
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)
            except OSError:
                pass


def load_config(path=None):
    path = Path(path) if path else ROOT / "config.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def cpu_threads(cfg):
    """How many CPU threads the assistant may use."""
    wanted = cfg.get("performance", {}).get("cpu_threads", 0)
    if wanted and wanted > 0:
        return wanted
    total = os.cpu_count() or 2
    return max(1, int(total * 0.6))


def validate_env(cfg):
    """Check required environment variables before models load."""
    engine = cfg.get("brain", {}).get("engine", "")

    if engine == "groq" and not os.environ.get("GROQ_API_KEY"):
        raise SystemExit(
            "\n"
            "  [ERROR] GROQ_API_KEY is not set, but brain.engine is 'groq'.\n"
            "\n"
            "  Please create a .env file in the project root with:\n"
            "    GROQ_API_KEY=gsk_your_key_here\n"
        )