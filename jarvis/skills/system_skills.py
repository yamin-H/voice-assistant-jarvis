"""Skills about your computer: screenshot, battery, system status, help."""
from datetime import datetime
from pathlib import Path

import psutil
from PIL import ImageGrab

from jarvis.reply import Reply
from jarvis.skills.registry import registry


def _take_screenshot():
    folder = Path.home() / "Pictures" / "Jarvis"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"screenshot-{datetime.now():%Y%m%d-%H%M%S}.png"
    ImageGrab.grab().save(path)
    print(f"  [screenshot saved] {path}")


@registry.skill("screenshot", [
    r"^(?:take |capture )?(?:a )?screenshot$",
    r"^(?:take|capture) (?:a )?(?:picture|photo|shot) of (?:my |the )?screen$",
])
def screenshot(m, ctx):
    return Reply("Taking a screenshot.", _take_screenshot)


@registry.skill("battery", [
    r"^(?:how s|what s|how is|what is) (?:my |the )?battery(?: level| life)?(?: doing)?$",
    r"^battery(?: level)?$",
    r"^how much battery(?: do i have| is left| is there)?$",
])
def battery(m, ctx):
    info = psutil.sensors_battery()
    if info is None:
        return "I can't read a battery on this computer."
    charging = ", and it is charging" if info.power_plugged else ""
    return f"Your battery is at {int(info.percent)} percent{charging}."


@registry.skill("system status", [
    r"^how s my (?:computer|pc|laptop)(?: doing)?$",
    r"^(?:cpu|ram|memory)(?: usage)?$",
    r"^how much (?:ram|memory) (?:am i using|is free|do i have)$",
    r"^(?:system|computer) status$",
])
def system_status(m, ctx):
    cpu = psutil.cpu_percent(interval=0.3)
    memory = psutil.virtual_memory()
    used, total = (memory.total - memory.available) / 1e9, memory.total / 1e9
    return f"The processor is at {cpu:.0f} percent, and you are using {used:.1f} of {total:.1f} gigabytes of memory."


@registry.skill("help", [
    r"^(?:what can you do|help|what are your (?:skills|abilities|capabilities)|how can you help(?: me)?)$"
])
def help_me(m, ctx):
    return (
        "I can answer questions, open apps and websites, snap and switch windows, "
        "type for you, press shortcuts, control your music, take screenshots, "
        "check your battery, set timers and reminders, take notes, remember things for you, "
        "and tell you what I can see through the camera."
    )