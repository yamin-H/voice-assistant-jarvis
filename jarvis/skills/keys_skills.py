"""Skills that press keys for you: type, write with the brain, shortcuts, media keys."""
import re
import time

import pyautogui

from jarvis.reply import Reply
from jarvis.skills import apps_skills, winapi, windowtools
from jarvis.skills.control import CANCEL
from jarvis.skills.registry import registry

pyautogui.PAUSE = 0.02
# Safety: slam the mouse into a screen corner to stop any typing or shortcut.

# What you say -> (keys to press, what Jarvis says)
HOTKEYS = {
    "copy": (("ctrl", "c"), "Copied."),
    "paste": (("ctrl", "v"), "Pasted."),
    "cut": (("ctrl", "x"), "Cut."),
    "undo": (("ctrl", "z"), "Undone."),
    "redo": (("ctrl", "y"), "Redone."),
    "select all": (("ctrl", "a"), "Selected everything."),
    "save": (("ctrl", "s"), "Saved."),
    "new tab": (("ctrl", "t"), "New tab."),
    "close tab": (("ctrl", "w"), "Tab closed."),
    "next tab": (("ctrl", "tab"), "Next tab."),
    "previous tab": (("ctrl", "shift", "tab"), "Previous tab."),
    "reopen tab": (("ctrl", "shift", "t"), "Reopened."),
    "refresh": (("f5",), "Refreshing."),
    "reload": (("f5",), "Reloading."),
    "go back": (("alt", "left"), "Going back."),
    "go forward": (("alt", "right"), "Going forward."),
    "enter": (("enter",), "Done."),
    "escape": (("esc",), "Done."),
    "new line": (("enter",), "Done."),
}
_names = "|".join(sorted((re.escape(k) for k in HOTKEYS), key=len, reverse=True))

# --- typing helpers ---
TARGET_END = re.compile(
    r"^(?P<body>.*?)\s*\b(?:in|into|on|inside)\s+(?P<app>[a-z0-9 ]+?)[.!?]*$",
    re.IGNORECASE | re.DOTALL,
)
IT_WORDS = {"it", "there", "that", "this", "the window", "this window", "that window"}
GENERIC = {"", "something", "anything", "something nice", "anything you like", "whatever",
           "something cool", "something interesting", "something good"}
GENERATE_HINT = re.compile(
    r"^(?:me |us )?(?:a|an|some)\b|^about\b|"
    r"\b(?:poem|story|email|letter|essay|paragraphs?|joke|summary|song|speech|caption|haiku|sentences?)\b",
    re.IGNORECASE,
)
FANCY = {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
         "\u2013": "-", "\u2014": "-", "\u2026": "..."}


def ascii_only(text):
    """pyautogui can only type keys that exist on the keyboard."""
    for fancy, plain in FANCY.items():
        text = text.replace(fancy, plain)
    return "".join(c for c in text if c == "\n" or 32 <= ord(c) < 127)


def clean_generated(text):
    return ascii_only(re.sub(r"[*_#`~>|]", "", text))


def type_now(text):
    """Types like a person. Returns False if you interrupted."""
    for i in range(0, len(text), 4):
        if CANCEL.is_set():
            return False
        pyautogui.write(text[i:i + 4], interval=0.02)
    return True


def prepare_target(target, ctx):
    """Brings the right window to the front.

    Returns a sentence describing a problem, or None when we are ready to type.
    """
    hwnd = None
    if target == "last":
        if not windowtools.is_valid(ctx.last_hwnd):
            return "I lost track of that window, so I didn't type."
        hwnd = ctx.last_hwnd
    elif isinstance(target, tuple):
        hwnd = apps_skills.open_app(target[1], ctx)
        if hwnd is None:
            return f"I couldn't open {target[1]}, so I didn't type."
    if hwnd is None:
        return None  # no target: type into whatever window is in front

    for _ in range(2):
        winapi.focus(hwnd)
        time.sleep(0.5)
        if winapi.foreground_window() == hwnd:
            ctx.last_hwnd = hwnd
            return None
    return "I couldn't bring that window to the front, so I didn't type."


def type_literal(text, target, ctx):
    problem = prepare_target(target, ctx)
    if problem:
        return problem
    type_now(text)
    return None


def write_with_brain(prompt, target, ctx):
    problem = prepare_target(target, ctx)
    if problem:
        return problem
    for chunk in ctx.brain.write_stream(prompt):
        if CANCEL.is_set():
            break
        if not type_now(clean_generated(chunk)):
            break
    return None


@registry.skill("type or write", [r"^(?P<verb>type|write|dictate)\b[:,]?\s*(?P<rest>.*)$"], use_raw=True)
def type_or_write(m, ctx):
    verb = m["verb"].lower()
    body, target = m["rest"].strip(), None

    # Where to type: "... in notepad", "... on it".
    ending = TARGET_END.match(body)
    if ending:
        app = ending["app"].strip().lower()
        if app in IT_WORDS:
            target, body = "last", ending["body"]
        elif apps_skills.resolve_name(app) in apps_skills.APPS or windowtools.find_window_fuzzy(app, strict=True):
            target, body = ("app", app), ending["body"]

    if target is None and ctx.in_chain and windowtools.is_valid(ctx.last_hwnd):
        target = "last"
    if target is None and ctx.in_chain:
        return "I don't know which window to type in, so I didn't type."
    if target is None and verb != "type":
        return None  # "write ..." with nowhere to write: let the chat brain answer

    body = body.strip(" ,")
    generic = body.lower().strip(" .!") in GENERIC
    generate = verb == "write" and (generic or bool(GENERATE_HINT.search(body)))

    if generate:
        if ctx.brain is None:
            return "My writing brain isn't available right now."
        prompt = "Write a short, friendly paragraph of two or three sentences." if generic else "Write " + body
        return Reply("Okay, writing it now.", lambda: write_with_brain(prompt, target, ctx))

    if not body:
        return "Tell me what to type, for example: type hello world."
    if body.endswith(".") and not re.search(r"[.!?]", body[:-1]):
        body = body[:-1]  # speech recognition adds a full stop to short phrases
    text = ascii_only(body)
    return Reply("Typing.", lambda: type_literal(text, target, ctx))


@registry.skill("shortcut", [rf"^(?:press |do |hit )?(?P<name>{_names})(?: that| it| this)?$"])
def shortcut(m, ctx):
    keys, message = HOTKEYS[m["name"].lower()]
    return Reply(message, lambda: pyautogui.hotkey(*keys))


@registry.skill("scroll", [r"^scroll (?P<direction>up|down)(?: a (?P<amount>little|bit|lot))?$"])
def scroll(m, ctx):
    amount = {"little": 200, "bit": 200, "lot": 1500, None: 500}[m["amount"]]
    clicks = amount if m["direction"] == "up" else -amount
    return Reply(f"Scrolling {m['direction']}.", lambda: pyautogui.scroll(clicks))


@registry.skill("play or pause", [r"^(?:play|pause|resume)(?: the)?(?: music| song| video| media)?$"])
def play_pause(m, ctx):
    return Reply("Okay.", lambda: winapi.press_key(winapi.VK_MEDIA_PLAY_PAUSE))


@registry.skill("next track", [r"^(?:next|skip)(?: the)?(?: song| track)?$"])
def next_track(m, ctx):
    return Reply("Next track.", lambda: winapi.press_key(winapi.VK_MEDIA_NEXT))


@registry.skill("previous track", [r"^(?:previous|last)(?: song| track)$"])
def previous_track(m, ctx):
    return Reply("Previous track.", lambda: winapi.press_key(winapi.VK_MEDIA_PREV))