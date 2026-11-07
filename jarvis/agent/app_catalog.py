"""Local Windows application discovery and safe launching.

The catalog is built from Windows-owned Start Menu and AppsFolder sources.
No model-provided executable path or shell command is ever executed.
"""

from dataclasses import dataclass
import difflib
import json
import os
from pathlib import Path
import subprocess
import time

from jarvis.skills import windowtools


CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def normalize_name(text):
    """Make app-name matching tolerant of speech transcription differences."""
    text = text.casefold()
    return "".join(char for char in text if char.isalnum())


@dataclass(frozen=True)
class AppRecord:
    """One locally discovered launchable application."""

    name: str
    source: str
    launcher: str
    launcher_kind: str

    def launch(self):
        """Launch only a path or AppID obtained from Windows local sources."""
        if self.launcher_kind == "start_menu":
            os.startfile(self.launcher)
            return

        if self.launcher_kind == "apps_folder":
            subprocess.Popen(
                ["explorer.exe", f"shell:AppsFolder\\{self.launcher}"],
                creationflags=CREATE_NO_WINDOW,
            )
            return

        raise RuntimeError(f"Unsupported launcher kind: {self.launcher_kind}")


@dataclass(frozen=True)
class AppResolution:
    """Result of resolving a human-provided app name."""

    status: str
    record: AppRecord | None = None
    candidates: tuple[AppRecord, ...] = ()

    @property
    def found(self):
        return self.status == "found" and self.record is not None


class AppCatalog:
    """Discovers and resolves locally installed Windows applications."""

    def __init__(self):
        self.records = []
        self.refresh()

    def refresh(self):
        """Rebuild the catalog from local Windows sources.

        The same app may appear in both Start Menu and AppsFolder. Keep only
        one record per normalized name, preferring the Start Menu shortcut.
        """
        records = []
        records.extend(self._start_menu_records())
        records.extend(self._apps_folder_records())

        source_priority = {
            "start_menu": 0,
            "apps_folder": 1,
        }

        unique = {}

        for record in records:
            key = normalize_name(record.name)
            current = unique.get(key)

            if current is None:
                unique[key] = record
                continue

            if source_priority[record.source] < source_priority[current.source]:
                unique[key] = record

        self.records = sorted(
            unique.values(),
            key=lambda item: item.name.casefold(),
        )

    def resolve(self, requested_name):
        """Find one local app, or return ambiguity/missing safely."""
        query = normalize_name(requested_name)

        if not query:
            return AppResolution(status="missing")

        exact = [
            record
            for record in self.records
            if normalize_name(record.name) == query
        ]
        if len(exact) == 1:
            return AppResolution(status="found", record=exact[0])
        if len(exact) > 1:
            return AppResolution(
                status="ambiguous",
                candidates=tuple(exact[:5]),
            )

        scored = []
        for record in self.records:
            candidate = normalize_name(record.name)

            if query in candidate or candidate in query:
                score = 0.95
            else:
                score = difflib.SequenceMatcher(
                    a=query,
                    b=candidate,
                ).ratio()

            scored.append((score, record))

        scored.sort(key=lambda item: item[0], reverse=True)

        if not scored or scored[0][0] < 0.72:
            return AppResolution(status="missing")

        best_score, best_record = scored[0]
        close_matches = [
            record
            for score, record in scored
            if score >= best_score - 0.04 and score >= 0.72
        ]

        if len(close_matches) > 1:
            return AppResolution(
                status="ambiguous",
                candidates=tuple(close_matches[:5]),
            )

        return AppResolution(status="found", record=best_record)

    def search(self, query="", limit=15):
        """Return matching locally installed apps for a read-only listing."""
        normalized_query = normalize_name(query)

        if not normalized_query:
            return self.records[:limit]

        matches = [
            record
            for record in self.records
            if normalized_query in normalize_name(record.name)
        ]
        return matches[:limit]

    def launch_and_verify(self, record, timeout=8.0):
        """Launch a local app and wait for a matching real window."""
        record.launch()

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            found = windowtools.find_window_fuzzy(record.name, strict=True)
            if found:
                return found
            time.sleep(0.2)

        return None

    @staticmethod
    def _start_menu_records():
        roots = []

        program_data = os.environ.get("PROGRAMDATA")
        if program_data:
            roots.append(
                Path(program_data)
                / "Microsoft"
                / "Windows"
                / "Start Menu"
                / "Programs"
            )

        app_data = os.environ.get("APPDATA")
        if app_data:
            roots.append(
                Path(app_data)
                / "Microsoft"
                / "Windows"
                / "Start Menu"
                / "Programs"
            )

        records = []
        for root in roots:
            if not root.exists():
                continue

            for path in root.rglob("*"):
                if not path.is_file():
                    continue

                if path.suffix.casefold() not in {".lnk", ".appref-ms"}:
                    continue

                name = path.stem.strip()
                if not name:
                    continue

                if name.casefold().startswith("uninstall "):
                    continue

                records.append(
                    AppRecord(
                        name=name,
                        source="start_menu",
                        launcher=str(path),
                        launcher_kind="start_menu",
                    )
                )

        return records

    @staticmethod
    def _apps_folder_records():
        """Read Windows app registrations without parsing human-formatted text."""
        command = (
            "Get-StartApps | "
            "Select-Object Name,AppID | "
            "ConvertTo-Json -Compress"
        )

        try:
            completed = subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    command,
                ],
                capture_output=True,
                text=True,
                timeout=15,
                check=True,
                creationflags=CREATE_NO_WINDOW,
            )
        except (OSError, subprocess.SubprocessError):
            return []

        raw = completed.stdout.strip()
        if not raw:
            return []

        try:
            items = json.loads(raw)
        except json.JSONDecodeError:
            return []

        if isinstance(items, dict):
            items = [items]
        if not isinstance(items, list):
            return []

        records = []
        for item in items:
            if not isinstance(item, dict):
                continue

            name = str(item.get("Name") or "").strip()
            app_id = str(item.get("AppID") or "").strip()

            if not name or not app_id:
                continue

            records.append(
                AppRecord(
                    name=name,
                    source="apps_folder",
                    launcher=app_id,
                    launcher_kind="apps_folder",
                )
            )

        return records