"""Skills that open apps, websites, and search or play YouTube videos with smart tab reuse."""
import difflib
import re
import time
import urllib.request
import webbrowser
from urllib.parse import quote_plus

import pyautogui
import pyperclip

from jarvis.reply import Reply
from jarvis.skills import winapi, windowtools
from jarvis.skills.registry import registry

# Windows apps we can open.
APPS = {
    "browser": ["cmd", "/c", "start", "", "chrome"],
    "chrome": ["cmd", "/c", "start", "", "chrome"],
    "google chrome": ["cmd", "/c", "start", "", "chrome"],
    "edge": ["cmd", "/c", "start", "", "msedge"],
    "microsoft edge": ["cmd", "/c", "start", "", "msedge"],
    "notepad": ["notepad"],
    "calculator": ["calc"],
    "paint": ["mspaint"],
    "file explorer": ["explorer"],
    "settings": ["cmd", "/c", "start", "", "ms-settings:"],
    "task manager": ["taskmgr"],
    "command prompt": ["cmd", "/c", "start", "", "cmd"],
}

# Websites we can open directly.
SITES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "github": "https://github.com",
}

BROWSER_NAMES = {"chrome", "google chrome", "edge", "microsoft edge", "browser", "firefox", "brave", "opera"}
GENERIC_MEDIA_WORDS = {"music", "song", "video", "media", "the music", "the song", "the video"}
KNOWN_SERVICES = ["youtube", "google", "gmail", "github", "reddit", "wikipedia", "amazon", "twitter", "netflix"]


def is_browser_window(hwnd):
    """True if this window handle belongs to a known web browser."""
    if not hwnd or not windowtools.is_valid(hwnd):
        return False
    title = winapi.title_of(hwnd).lower()
    return any(b in title for b in ["chrome", "edge", "firefox", "brave", "opera", "vivaldi"])


def get_active_or_open_browser():
    """Returns handle of the foreground browser, or the first open browser found."""
    fg = winapi.foreground_window()
    if is_browser_window(fg):
        return fg

    for hwnd, _ in winapi.list_windows():
        if is_browser_window(hwnd):
            return hwnd

    return None


def extract_site_keyword(text: str) -> str:
    """Finds what major website/service a title or URL belongs to."""
    t = text.lower()
    for site in KNOWN_SERVICES:
        if site in t:
            return site
    return ""


def should_open_new_tab(current_title: str, target_url: str) -> bool:
    """Determines whether to navigate the current tab or open a new tab."""
    title = current_title.lower()

    # 1. If currently on a blank / new tab page, ALWAYS reuse it
    if any(b in title for b in ["new tab", "about:blank", "start page", "speed dial"]):
        return False

    current_site = extract_site_keyword(title)
    target_site = extract_site_keyword(target_url)

    # 2. If you are on Google Search, navigating or searching stays in the same tab
    if "google" in title and "search" in title:
        return False

    # 3. Same service (e.g. YouTube -> playing a video on YouTube): reuse tab
    if current_site and target_site and current_site == target_site:
        return False

    # 4. Completely different service (e.g. listening to YouTube, and opening GitHub):
    # Open in a new tab so you don't lose the existing page
    if current_site and target_site and current_site != target_site:
        return True

    # Default for continuous browsing in a single session: reuse current tab
    return False


def resolve_name(name):
    """Turns what you said into an app or site name we know."""
    name = re.sub(r"\s+for me$", "", name.strip()).lower()
    known = list(APPS) + list(SITES)

    if name in known:
        return name
    if "browser" in name or "internet" in name or "web" in name:
        return "browser"

    squeezed = name.replace(" ", "")
    for key in known:
        if key.replace(" ", "") == squeezed:
            return key

    close = difflib.get_close_matches(name, known, n=1, cutoff=0.72)
    return close[0] if close else None


def open_app(key, ctx):
    """Starts an app or focuses it if already running."""
    if key in BROWSER_NAMES:
        browser_hwnd = get_active_or_open_browser()
        if browser_hwnd:
            winapi.focus(browser_hwnd)
            ctx.last_app = key
            ctx.last_hwnd = browser_hwnd
            return browser_hwnd

    before = windowtools.handles()
    winapi.launch(APPS[key])
    hwnd = windowtools.wait_for_new_window(before)
    if hwnd is None:
        found = windowtools.find_window_fuzzy(key, strict=True)
        hwnd = found[0] if found else None

    ctx.last_app = key
    if hwnd is not None:
        ctx.last_hwnd = hwnd
        winapi.focus(hwnd)
    return hwnd


def open_url(url, ctx, force_new_tab=False):
    """Navigates the browser intelligently without creating unwanted tabs."""
    browser_hwnd = get_active_or_open_browser()

    if browser_hwnd:
        winapi.focus(browser_hwnd)
        time.sleep(0.12)

        current_title = winapi.title_of(browser_hwnd)
        open_new = force_new_tab or should_open_new_tab(current_title, url)

        if open_new:
            # Open a new tab in the same window
            pyautogui.hotkey("ctrl", "t")
            time.sleep(0.08)
        else:
            # Reuse the current tab (Ctrl+L focuses and highlights the address bar)
            pyautogui.hotkey("ctrl", "l")
            time.sleep(0.05)

        # Fast clipboard paste avoids dropped characters
        pyperclip.copy(url)
        pyautogui.hotkey("ctrl", "v")
        pyautogui.press("enter")

        ctx.last_hwnd = browser_hwnd
        ctx.last_app = "browser"
        return

    # No browser running at all: launch with system default
    webbrowser.open(url)


def _open_action(key, ctx, force_new_tab=False):
    if key in SITES:
        open_url(SITES[key], ctx, force_new_tab=force_new_tab)
        return None
    if open_app(key, ctx) is None:
        return f"I started {key}, but I couldn't see its window."
    return None


def get_first_youtube_video_url(query):
    """Finds the first matching YouTube video URL, or falls back to search page."""
    search_url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
    try:
        req = urllib.request.Request(
            search_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        video_ids = re.findall(r"/watch\?v=([a-zA-Z0-9_-]{11})", html)
        if video_ids:
            return f"https://www.youtube.com/watch?v={video_ids[0]}"
    except Exception:
        pass
    return search_url


# --- Skills ---

@registry.skill("open", [
    r"^(?P<verb>open|launch|start|run|go to|take me to)(?: up)? (?:the |my )?(?P<name>.+?)(?: in a new tab)?$"
])
def open_thing(m, ctx):
    raw_text = m.string.lower()
    force_new = "in a new tab" in raw_text

    raw_name = m["name"].strip()
    if re.match(r"^youtube and (?:play|search)\b", raw_name, re.IGNORECASE):
        return None

    key = resolve_name(raw_name)
    goto = m["verb"] in ("go to", "take me to")
    if key is None:
        return None

    if key in SITES:
        url = SITES[key]
        return Reply(f"Opening {key}.", lambda: open_url(url, ctx, force_new_tab=force_new))
    if goto:
        return None
    return Reply(f"Opening {key}.", lambda: _open_action(key, ctx, force_new_tab=force_new))


@registry.skill("play or search youtube", [
    r"^(?:open youtube and )?play (?P<q>.+?)(?: on youtube)?$",
    r"^(?:search|look up|find) (?P<q>.+?) on youtube$",
    r"^search youtube for (?P<q>.+)$",
])
def play_or_search_youtube(m, ctx):
    query = m["q"].strip()
    if query.lower() in GENERIC_MEDIA_WORDS:
        return None

    def act():
        target_url = get_first_youtube_video_url(query)
        open_url(target_url, ctx)

    return Reply(f"Playing {query} on YouTube.", act)


@registry.skill("web search", [r"^(?:search for|search|google|look up) (?P<q>.+?)(?: in a new tab)?$"])
def web_search(m, ctx):
    force_new = "in a new tab" in m.string.lower()
    url = "https://www.google.com/search?q=" + quote_plus(m["q"])
    return Reply(f"Searching for {m['q']}.", lambda: open_url(url, ctx, force_new_tab=force_new))