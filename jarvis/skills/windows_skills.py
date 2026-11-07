"""Skills that manage windows: snap, maximize, minimize, switch, close, list."""
from jarvis.reply import Reply
from jarvis.skills import winapi, windowtools
from jarvis.skills.registry import registry

THIS = {"this", "this window", "it", "window", "the window", "current window",
        "that", "that window", "there"}


def short_name(title):
    """'Untitled - Notepad' -> 'Notepad'."""
    return title.rsplit(" - ", 1)[-1].strip()[:30]


def target_window(name, ctx):
    name = (name or "this").strip()
    if name in THIS:
        if ctx.in_chain and windowtools.is_valid(ctx.last_hwnd):
            return ctx.last_hwnd, winapi.title_of(ctx.last_hwnd)
        hwnd = winapi.foreground_window()
        return (hwnd, winapi.title_of(hwnd)) if hwnd else None
    return windowtools.find_window_fuzzy(name)


@registry.skill("snap two windows", [
    r"^(?:snap|put|move) (?P<a>.+?) (?:(?:to|on) the )?(?P<sa>left|right)(?: side)? "
    r"(?:and|then) (?:snap |put |move )?(?P<b>.+?) (?:(?:to|on) the )?(?P<sb>left|right)(?: side)?$"
])
def snap_two(m, ctx):
    first, second = target_window(m["a"], ctx), target_window(m["b"], ctx)
    if not first:
        return f"I can't find {m['a']} open."
    if not second:
        return f"I can't find {m['b']} open."

    def act():
        winapi.snap(first[0], m["sa"])
        winapi.snap(second[0], m["sb"])

    return Reply(f"Snapping {short_name(first[1])} {m['sa']} and {short_name(second[1])} {m['sb']}.", act)


@registry.skill("snap window", [
    r"^(?:snap|put|move) (?P<app>.+?) (?:(?:to|on) the )?(?P<side>left|right)(?: side| half)?$"
])
def snap_one(m, ctx):
    win = target_window(m["app"], ctx)
    if not win:
        return f"I can't find {m['app']} open."
    return Reply(
        f"Snapping {short_name(win[1])} to the {m['side']}.",
        lambda: winapi.snap(win[0], m["side"]),
    )


@registry.skill("show desktop", [
    r"^(?:show|go to) (?:the )?desktop$",
    r"^minimi[sz]e (?:all|everything)(?: windows)?$",
])
def show_desktop(m, ctx):
    return Reply("Showing the desktop.", winapi.show_desktop)


@registry.skill("maximize", [r"^maximi[sz]e(?: (?P<app>.+))?$"])
def maximize(m, ctx):
    win = target_window(m["app"], ctx)
    if not win:
        return f"I can't find {m['app']} open."
    return Reply(f"Maximizing {short_name(win[1])}.", lambda: winapi.maximize(win[0]))


@registry.skill("minimize", [r"^minimi[sz]e(?: (?P<app>.+))?$"])
def minimize(m, ctx):
    win = target_window(m["app"], ctx)
    if not win:
        return f"I can't find {m['app']} open."
    return Reply(f"Minimizing {short_name(win[1])}.", lambda: winapi.minimize(win[0]))


@registry.skill("switch to window", [r"^(?:switch to|go to|focus on|focus|bring up) (?P<app>.+)$"])
def switch_to(m, ctx):
    win = windowtools.find_window_fuzzy(m["app"])
    if not win:
        return None  # not a window we know, so let something else handle it
    return Reply(f"Switching to {short_name(win[1])}.", lambda: winapi.focus(win[0]))


@registry.skill("close window", [r"^close (?P<app>.+)$"])
def close(m, ctx):
    if m["app"] in ("tab", "this tab", "the tab"):
        return None
    win = target_window(m["app"], ctx)
    if not win:
        return None
    name = short_name(win[1])

    def do_close():
        winapi.close_window(win[0])
        return f"Closed {name}."

    return Reply(f"Do you want me to close {name}?", on_yes=do_close)


@registry.skill("list windows", [
    r"^(?:what|which) (?:windows|apps|programs|applications)(?: do i have| are)?(?: open| running)?$",
    r"^what (?:do i have|s) open$",
])
def list_open(m, ctx):
    names = []
    for _, title in winapi.list_windows():
        name = short_name(title)
        if name not in names:
            names.append(name)
    if not names:
        return "I don't see any open windows."
    shown = names[:6]
    listing = shown[0] if len(shown) == 1 else ", ".join(shown[:-1]) + " and " + shown[-1]
    return f"You have {listing} open."