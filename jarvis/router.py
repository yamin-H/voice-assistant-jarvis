"""The router: turns what you said into a reply and an optional action.

Returns None when no rule matches. Later, the chat brain handles those.
"""
import ctypes
import re
import subprocess
import webbrowser
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional
from urllib.parse import quote_plus

# Windows apps we can open. Add your own lines here.
APPS = {
    "chrome": ["cmd", "/c", "start", "", "chrome"],
    "google chrome": ["cmd", "/c", "start", "", "chrome"],
    "edge": ["cmd", "/c", "start", "", "msedge"],
    "notepad": ["notepad"],
    "calculator": ["calc"],
    "paint": ["mspaint"],
    "file explorer": ["explorer"],
    "settings": ["cmd", "/c", "start", "", "ms-settings:"],
}

# Websites we can open. Add your own lines here.
SITES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "github": "https://github.com",
}

VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF


@dataclass
class Reply:
    text: str                                  # what Jarvis says
    action: Optional[Callable[[], None]] = None  # what Jarvis does (optional)
    quit: bool = False                         # True = stop the program after speaking


def normalize(text):
    """lowercase, no punctuation, no filler words."""
    t = text.lower()
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    t = re.sub(r"\b(jarvis|please)\b", " ", t)
    t = re.sub(r"^\s*(can|could|would) you ", "", t)
    return re.sub(r"\s+", " ", t).strip()


def press_key(code, times=1):
    for _ in range(times):
        ctypes.windll.user32.keybd_event(code, 0, 0, 0)  # key down
        ctypes.windll.user32.keybd_event(code, 0, 2, 0)  # key up


def launch(command):
    subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW)


class Router:
    def __init__(self, cfg):
        self.name = cfg["assistant"]["name"]
        self.user = cfg["assistant"]["user_name"]

    def route(self, text):
        t = normalize(text)
        if not t:
            return None

        if re.search(r"\b(goodbye|bye bye|exit|quit|shut down|stop listening)\b", t):
            return Reply("Goodbye! See you soon.", quit=True)

        if re.search(r"\b(what time|time is it|the time|current time)\b", t):
            now = datetime.now()
            return Reply(f"It's {now.strftime('%I:%M %p').lstrip('0')}.")

        if re.search(r"\b(date|what day|which day)\b", t):
            now = datetime.now()
            return Reply(f"Today is {now.strftime('%A, %B')} {now.day}.")

        if re.fullmatch(r"(hello|hi|hey|good morning|good evening)( there)?", t):
            return Reply(f"Hello {self.user}! How can I help?")

        if re.search(r"\b(who are you|your name|what are you)\b", t):
            return Reply(f"I'm {self.name}, your voice assistant, running on your own computer.")

        if re.search(r"\b(thanks|thank you)\b", t):
            return Reply("You're welcome!")

        if re.search(r"\b(volume up|louder|increase volume|turn it up)\b", t):
            return Reply("Volume up.", lambda: press_key(VK_VOLUME_UP, 5))
        if re.search(r"\b(volume down|quieter|decrease volume|turn it down)\b", t):
            return Reply("Volume down.", lambda: press_key(VK_VOLUME_DOWN, 5))
        if re.search(r"\b(mute|unmute)\b", t):
            return Reply("Done.", lambda: press_key(VK_VOLUME_MUTE))

        m = re.match(r"^open (?:the )?(.+)$", t)
        if m:
            name = m.group(1).strip()
            if name in SITES:
                return Reply(f"Opening {name}.", lambda: webbrowser.open(SITES[name]))
            if name in APPS:
                return Reply(f"Opening {name}.", lambda: launch(APPS[name]))
            return Reply(f"Sorry, I don't know how to open {name} yet.")

        m = re.match(r"^(?:search for|search|google|look up) (.+)$", t)
        if m:
            query = m.group(1).strip()
            url = "https://www.google.com/search?q=" + quote_plus(query)
            return Reply(f"Searching for {query}.", lambda: webbrowser.open(url))

        return None