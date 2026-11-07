"""Restricted execution engine for Jarvis Agent Mode.

Supports all allowlisted tools with verified outcome checks and user confirmation gates.
All app targets are resolved from a local Windows catalog; arbitrary commands are never executed.
"""

from dataclasses import dataclass
from datetime import datetime
import re
import time
from urllib.parse import quote_plus

from PIL import ImageGrab
import pyautogui

from jarvis import store
from jarvis.agent.app_catalog import AppCatalog
from jarvis.agent.confirmation import ConfirmationGate, ConfirmationRequest
from jarvis.agent.contracts import AgentPlan, ToolCall
from jarvis.config import get_data_dir
from jarvis.scheduler import SCHEDULER
from jarvis.skills import apps_skills, winapi, windowtools
from jarvis.skills.keys_skills import HOTKEYS, ascii_only
from jarvis.skills.registry import Context
from jarvis.timeparse import find_when, spoken_clock, spoken_duration


EXECUTABLE_TOOLS = {
    "app.open",
    "app.list_installed",
    "web.search",
    "window.focus",
    "window.close",
    "window.layout",
    "input.type_text",
    "input.press_key",
    "input.scroll",
    "system.screenshot",
    "notes.create",
    "notes.read",
    "reminder.create",
}

ALLOWED_RISKS = {"safe", "reversible"}


@dataclass(frozen=True)
class ExecutionResult:
    tool: str
    status: str
    summary: str
    verified: bool = False
    confirmation: ConfirmationRequest | None = None

    def pretty(self):
        verification = "verified" if self.verified else "not verified"
        text = f"[{self.status} | {verification}] {self.tool}: {self.summary}"

        if self.confirmation is not None:
            text += "\n" + self.confirmation.pretty()

        return text


class ToolExecutor:
    """Runs allowlisted local capabilities with safety verification."""

    def __init__(self, cfg, ctx=None):
        if not cfg.get("agent", {}).get("execution", {}).get("allow_low_risk", False):
            raise RuntimeError(
                "Low-risk execution is disabled. Set "
                "agent.execution.allow_low_risk to true."
            )

        self.cfg = cfg
        self.ctx = ctx if ctx is not None else Context(cfg=cfg)
        self.apps = AppCatalog()
        self.confirmations = ConfirmationGate(
            lifetime_seconds=cfg["agent"].get("confirmation_seconds", 60)
        )

        self.handlers = {
            "app.open": self._open_app,
            "app.list_installed": self._list_installed_apps,
            "web.search": self._web_search,
            "window.focus": self._focus_window,
            "window.close": self._close_window,
            "window.layout": self._window_layout,
            "input.type_text": self._type_text,
            "input.press_key": self._press_key,
            "input.scroll": self._scroll,
            "system.screenshot": self._take_screenshot,
            "notes.create": self._create_note,
            "notes.read": self._read_notes,
            "reminder.create": self._create_reminder,
        }

    def run_plan(self, plan: AgentPlan):
        """Run a validated plan and halt if an outcome is uncertain."""
        if plan.mode != "plan":
            return [
                ExecutionResult(
                    tool="agent.plan",
                    status="skipped",
                    summary=f"Plan mode is '{plan.mode}', so nothing can run.",
                    verified=True,
                )
            ]

        results = []

        for step in plan.steps:
            result = self.run_step(step)
            results.append(result)

            if result.status != "succeeded":
                break

            if not result.verified:
                results.append(
                    ExecutionResult(
                        tool="agent.plan",
                        status="blocked",
                        summary=(
                            f"Stopped because step '{step.tool}' could not be verified."
                        ),
                        verified=True,
                    )
                )
                break

        return results

    def run_step(self, step: ToolCall, confirmation_token=None):
        """Run exactly one tool, requiring a bound token for confirm-risk tools."""

        if step.tool not in EXECUTABLE_TOOLS:
            return ExecutionResult(
                tool=step.tool,
                status="blocked",
                summary="This tool is not implemented for execution.",
            )

        if step.risk == "confirm":
            if confirmation_token is None:
                request = self.confirmations.request(
                    tool_call=step,
                    message=self._confirmation_message(step),
                )
                return ExecutionResult(
                    tool=step.tool,
                    status="needs_confirmation",
                    summary="This action requires your confirmation.",
                    confirmation=request,
                )

            approved, reason = self.confirmations.approve(
                token=confirmation_token,
                tool_call=step,
            )

            if not approved:
                return ExecutionResult(
                    tool=step.tool,
                    status="blocked",
                    summary=reason,
                )

        elif step.risk not in ALLOWED_RISKS:
            return ExecutionResult(
                tool=step.tool,
                status="blocked",
                summary=f"Risk level '{step.risk}' is not permitted.",
            )

        try:
            return self.handlers[step.tool](step.arguments)
        except Exception as error:
            return ExecutionResult(
                tool=step.tool,
                status="failed",
                summary=f"Tool raised an error: {error}",
            )

    @staticmethod
    def _confirmation_message(step):
        if step.tool == "window.close":
            name = step.arguments.get("window_name", "the window")
            return f"Close the window matching '{name}'? Unsaved work may be lost."

        if step.tool == "input.type_text":
            text = step.arguments.get("text", "")
            preview = (text[:35] + "...") if len(text) > 35 else text
            return f"Type '{preview}' into the active window?"

        return f"Allow Jarvis to execute '{step.tool}'?"

    # --- Tool Handlers ---

    def _open_app(self, arguments):
        requested = arguments["target"].strip()

        known = apps_skills.resolve_name(requested.casefold())
        if known in apps_skills.SITES:
            apps_skills.open_url(apps_skills.SITES[known], self.ctx)
            return ExecutionResult(
                tool="app.open",
                status="succeeded",
                summary=f"Opened website '{known}'.",
                verified=True,
            )

        resolution = self.apps.resolve(requested)

        if resolution.status == "missing":
            return ExecutionResult(
                tool="app.open",
                status="failed",
                summary=f"No locally installed app matched '{requested}'.",
            )

        if resolution.status == "ambiguous":
            names = ", ".join(record.name for record in resolution.candidates)
            return ExecutionResult(
                tool="app.open",
                status="blocked",
                summary=f"'{requested}' matches multiple apps: {names}. Please be more specific.",
            )

        record = resolution.record
        found = self.apps.launch_and_verify(record)

        if not found:
            return ExecutionResult(
                tool="app.open",
                status="failed",
                summary=f"Launched '{record.name}', but no window appeared within timeout.",
            )

        hwnd, title = found
        winapi.focus(hwnd)

        self.ctx.last_app = record.name
        self.ctx.last_hwnd = hwnd

        return ExecutionResult(
            tool="app.open",
            status="succeeded",
            summary=f"Opened and focused '{title}'.",
            verified=True,
        )

    def _list_installed_apps(self, arguments):
        query = arguments.get("query", "").strip()
        matches = self.apps.search(query=query, limit=15)
        suffix = f" matching '{query}'" if query else ""

        if not matches:
            return ExecutionResult(
                tool="app.list_installed",
                status="succeeded",
                summary=f"No locally installed apps found{suffix}.",
                verified=True,
            )

        names = ", ".join(record.name for record in matches)
        return ExecutionResult(
            tool="app.list_installed",
            status="succeeded",
            summary=f"Found {len(matches)} app(s){suffix}: {names}",
            verified=True,
        )

    def _web_search(self, arguments):
        query = arguments["query"].strip()
        if not query:
            return ExecutionResult(
                tool="web.search",
                status="failed",
                summary="Search query was empty.",
            )

        url = "https://www.google.com/search?q=" + quote_plus(query)
        apps_skills.open_url(url, self.ctx)

        return ExecutionResult(
            tool="web.search",
            status="succeeded",
            summary=f"Searched the web for '{query}'.",
            verified=True,
        )

    def _focus_window(self, arguments):
        requested_name = arguments["window_name"].strip()
        found = windowtools.find_window_fuzzy(requested_name)

        if not found:
            return ExecutionResult(
                tool="window.focus",
                status="failed",
                summary=f"Could not find an open window matching '{requested_name}'.",
            )

        hwnd, title = found
        winapi.focus(hwnd)

        return ExecutionResult(
            tool="window.focus",
            status="succeeded",
            summary=f"Focused '{title}'.",
            verified=True,
        )

    def _close_window(self, arguments):
        requested_name = arguments["window_name"].strip()
        found = windowtools.find_window_fuzzy(requested_name)

        if not found:
            return ExecutionResult(
                tool="window.close",
                status="failed",
                summary=f"Could not find an open window matching '{requested_name}'.",
            )

        hwnd, title = found
        winapi.close_window(hwnd)

        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            if not windowtools.is_valid(hwnd):
                return ExecutionResult(
                    tool="window.close",
                    status="succeeded",
                    summary=f"Closed '{title}'.",
                    verified=True,
                )
            time.sleep(0.2)

        return ExecutionResult(
            tool="window.close",
            status="succeeded",
            summary=f"Requested close for '{title}', but window is still responding.",
            verified=False,
        )

    def _window_layout(self, arguments):
        action = arguments.get("action", "").strip().lower()
        win_name = arguments.get("window_name", "").strip()

        if action in ("show_desktop", "desktop"):
            winapi.show_desktop()
            return ExecutionResult(
                tool="window.layout",
                status="succeeded",
                summary="Showed the desktop.",
                verified=True,
            )

        hwnd = None
        title = "the active window"
        if win_name:
            found = windowtools.find_window_fuzzy(win_name)
            if not found:
                return ExecutionResult(
                    tool="window.layout",
                    status="failed",
                    summary=f"Could not find window matching '{win_name}'.",
                )
            hwnd, title = found
        else:
            hwnd = winapi.foreground_window()
            if hwnd:
                title = winapi.title_of(hwnd)

        if not hwnd or not windowtools.is_valid(hwnd):
            return ExecutionResult(
                tool="window.layout",
                status="failed",
                summary="No active window found to adjust layout.",
            )

        if action == "maximize":
            winapi.maximize(hwnd)
            summary = f"Maximized '{title}'."
        elif action == "minimize":
            winapi.minimize(hwnd)
            summary = f"Minimized '{title}'."
        elif action in ("snap_left", "left"):
            winapi.snap(hwnd, "left")
            summary = f"Snapped '{title}' to the left."
        elif action in ("snap_right", "right"):
            winapi.snap(hwnd, "right")
            summary = f"Snapped '{title}' to the right."
        else:
            return ExecutionResult(
                tool="window.layout",
                status="failed",
                summary=f"Unsupported window action: '{action}'.",
            )

        return ExecutionResult(
            tool="window.layout",
            status="succeeded",
            summary=summary,
            verified=True,
        )

    def _type_text(self, arguments):
        text = arguments.get("text", "")
        if not text:
            return ExecutionResult(
                tool="input.type_text",
                status="failed",
                summary="No text provided to type.",
            )

        clean = ascii_only(text)
        pyautogui.write(clean, interval=0.02)

        return ExecutionResult(
            tool="input.type_text",
            status="succeeded",
            summary=f"Typed text ({len(clean)} characters).",
            verified=True,
        )

    def _press_key(self, arguments):
        raw_key = arguments.get("key", "").strip().lower()
        if not raw_key:
            return ExecutionResult(
                tool="input.press_key",
                status="failed",
                summary="No key specified.",
            )

        if raw_key in HOTKEYS:
            keys, _ = HOTKEYS[raw_key]
            pyautogui.hotkey(*keys)
        elif "+" in raw_key:
            parts = [p.strip() for p in raw_key.split("+")]
            pyautogui.hotkey(*parts)
        else:
            pyautogui.press(raw_key)

        return ExecutionResult(
            tool="input.press_key",
            status="succeeded",
            summary=f"Pressed key '{raw_key}'.",
            verified=True,
        )

    def _scroll(self, arguments):
        direction = arguments.get("direction", "down").strip().lower()
        amount_raw = arguments.get("amount", "500").strip().lower()

        amount_map = {"little": 200, "bit": 200, "lot": 1500}
        if amount_raw in amount_map:
            amount = amount_map[amount_raw]
        else:
            try:
                amount = int(re.sub(r"[^\d]", "", amount_raw)) or 500
            except ValueError:
                amount = 500

        clicks = amount if direction == "up" else -amount
        pyautogui.scroll(clicks)

        return ExecutionResult(
            tool="input.scroll",
            status="succeeded",
            summary=f"Scrolled {direction}.",
            verified=True,
        )

    def _take_screenshot(self, arguments):
        folder = get_data_dir() / "screenshots"
        folder.mkdir(parents=True, exist_ok=True)

        path = folder / f"screenshot-{datetime.now():%Y%m%d-%H%M%S}.png"
        ImageGrab.grab().save(path)

        if not path.exists() or path.stat().st_size == 0:
            return ExecutionResult(
                tool="system.screenshot",
                status="failed",
                summary="Screenshot file was not created successfully.",
            )

        return ExecutionResult(
            tool="system.screenshot",
            status="succeeded",
            summary=f"Saved screenshot to {path.name}.",
            verified=True,
        )

    def _create_note(self, arguments):
        text = arguments.get("text", "").strip()
        if not text:
            return ExecutionResult(
                tool="notes.create",
                status="failed",
                summary="Note text cannot be empty.",
            )

        notes = store.load("notes", [])
        notes.append({
            "text": text,
            "time": datetime.now().isoformat(timespec="minutes"),
        })
        store.save("notes", notes)

        return ExecutionResult(
            tool="notes.create",
            status="succeeded",
            summary=f"Saved note: {text}.",
            verified=True,
        )

    def _read_notes(self, arguments):
        notes = store.load("notes", [])

        if not notes:
            return ExecutionResult(
                tool="notes.read",
                status="succeeded",
                summary="No saved notes found.",
            )

        latest = notes[-5:]
        text = " | ".join(note.get("text", "") for note in latest)

        return ExecutionResult(
            tool="notes.read",
            status="succeeded",
            summary=f"Read {len(notes)} note(s). Latest notes: {text}",
            verified=True,
        )

    def _create_reminder(self, arguments):
        req = arguments.get("request", "").strip()
        if not req:
            return ExecutionResult(
                tool="reminder.create",
                status="failed",
                summary="No reminder request provided.",
            )

        is_alarm = bool(re.search(r"\balarm\b|\bwake me\b", req, re.IGNORECASE))
        now = datetime.now()
        when = find_when(req, now, bare_duration=True, prefer_am=is_alarm)

        if when is None:
            return ExecutionResult(
                tool="reminder.create",
                status="failed",
                summary=f"Could not understand the time in: '{req}'.",
            )

        kind = "timer" if when.kind == "duration" and not is_alarm else ("alarm" if is_alarm else "reminder")
        clean_msg = re.sub(
            r"^(?:please\s+)?(?:remind me|(?:set|create|make|add)\s+(?:me\s+)?(?:a\s+|an\s+)?(?:reminder|alarm|timer)|wake me up)\b\s*",
            "",
            when.rest,
            flags=re.IGNORECASE,
        ).strip(" ,.")

        SCHEDULER.add(
            kind=kind,
            due_ts=when.due.timestamp(),
            text=clean_msg,
            seconds=when.seconds if kind == "timer" else None,
        )

        time_desc = (
            f"for {spoken_duration(when.seconds)}"
            if when.kind == "duration"
            else spoken_clock(when.due, now)
        )
        msg_desc = f" ({clean_msg})" if clean_msg else ""

        return ExecutionResult(
            tool="reminder.create",
            status="succeeded",
            summary=f"Created {kind} {time_desc}{msg_desc}.",
            verified=True,
        )