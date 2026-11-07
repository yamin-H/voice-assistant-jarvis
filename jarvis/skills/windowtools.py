"""Extra window helpers: wait for a new window, find windows even with typos."""
import difflib
import time
from ctypes import wintypes

from jarvis.skills import winapi

winapi.user32.IsWindow.argtypes = [wintypes.HWND]


def is_valid(hwnd):
    """True if this window still exists."""
    return bool(hwnd) and bool(winapi.user32.IsWindow(hwnd))


def handles():
    """The set of all visible windows right now."""
    return {hwnd for hwnd, _ in winapi.list_windows()}


def wait_for_new_window(before, timeout=8.0):
    """Waits for a window that was not in `before`. Returns its handle, or None."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        for hwnd, _ in winapi.list_windows():  # topmost window first
            if hwnd not in before:
                return hwnd
        time.sleep(0.25)
    return None


def find_window_fuzzy(name, strict=False):
    """Finds an open window by app name. Returns (handle, title) or None.

    strict=True only accepts windows whose title ENDS with the app name
    (like 'Untitled - Notepad'), so a file called notepad.py will not match.
    """
    name = name.lower().strip()
    needles = winapi.ALIASES.get(name, [name])
    windows = winapi.list_windows()

    for hwnd, title in windows:
        if any(title.lower().endswith(n) for n in needles):
            return hwnd, title
    if not strict:
        for hwnd, title in windows:
            if any(n in title.lower() for n in needles):
                return hwnd, title

    # Last chance: the closest match, which fixes speech typos like "nodepad".
    short = {title.rsplit(" - ", 1)[-1].strip().lower(): (hwnd, title) for hwnd, title in windows}
    close = difflib.get_close_matches(name, list(short), n=1, cutoff=0.75)
    return short[close[0]] if close else None