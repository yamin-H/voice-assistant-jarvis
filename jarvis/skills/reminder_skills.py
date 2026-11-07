"""Timers, alarms and reminders: "set a timer for 5 minutes", "remind me at 5 to call mom"."""
import re
import time
from datetime import datetime

from jarvis.scheduler import SCHEDULER
from jarvis.skills.registry import registry
from jarvis.textutil import to_second_person, upper_first
from jarvis.timeparse import find_when, spoken_clock, spoken_duration

MAX_SECONDS = 7 * 24 * 3600
KINDS = {"timer": ["timer"], "alarm": ["alarm"], "reminder": ["reminder"]}
HELP_REMIND = "I couldn't tell when. Try saying: remind me in 10 minutes to drink water."
HELP_TIMER = "How long should it be? Try saying: set a timer for 5 minutes."
PREFIX = re.compile(
    r"^(?:please\s+)?(?:remind me|(?:set|create|make|add)\s+(?:me\s+)?(?:a\s+|an\s+)?(?:reminder|alarm)|wake me up)"
    r"\b\s*(?:to|that|about|of|for|called|named)?\s*",
    re.IGNORECASE,
)


def _kind_word(text):
    match = re.search(r"\b(timer|alarm|reminder)s?\b", text)
    return match.group(1) if match else "timer"


@registry.skill("cancel timers", [
    r"^(?:cancel|stop|delete|remove|clear|turn off|dismiss)\b.*?\b(?:timer|alarm|reminder)s?\b.*$",
])
def cancel(m, ctx):
    word = _kind_word(m.string)
    removed = SCHEDULER.cancel(KINDS[word])
    if removed == 0:
        return f"You don't have any {word}s."
    return f"Cancelled {removed} {word}{'s' if removed != 1 else ''}."


def _describe_item(item):
    due = item["due"]
    if item["kind"] == "timer":
        return f"timer, {spoken_duration(max(1, due - time.time()))} left"
    when = spoken_clock(datetime.fromtimestamp(due))
    if item["text"]:
        return f"{item['kind']}, {to_second_person(item['text'])}, {when}"
    return f"{item['kind']}, {when}"


@registry.skill("list timers", [
    r"^(?:what|which|how many|list|show|tell me|do i have)\b.*\b(?:my|the|current|active|pending|running|set)\b.*\b(?P<what>timer|alarm|reminder)s?\b.*$",
    r"^(?:what|which|how many|list|show|tell me)\b.*\b(?P<what>timer|alarm|reminder)s?\b.*\b(?:do i have|have i|i have|i set|are running|are set|are there|are active|are pending)\b.*$",
    r"^do i have (?:any|a|an)\b.*\b(?P<what>timer|alarm|reminder)s?\b.*$",
])
def list_items(m, ctx):
    word = m["what"]
    items = SCHEDULER.pending(KINDS[word])
    if not items:
        return f"You don't have any {word}s."
    shown = items[:4]
    intro = f"You have {len(items)} {word}{'s' if len(items) != 1 else ''}."
    return intro + " " + ". ".join(upper_first(_describe_item(i)) for i in shown) + "."


@registry.skill("time left", [
    r"^how (?:much time|long) (?:is )?(?:left|remaining)(?: on| for)?(?: my| the)?(?: timer)?$",
    r"^how much time (?:do i have )?left$",
    r"^how long (?:is )?(?:left )?(?:on|for) (?:my|the) timer$",
])
def time_left(m, ctx):
    timers = SCHEDULER.pending(["timer"])
    if not timers:
        return "You don't have a timer running."
    left = spoken_duration(max(1, timers[0]["due"] - time.time()))
    return f"{'Your timer has' if len(timers) == 1 else 'The next timer has'} {left} left."


@registry.skill("snooze", [r"^snooze(?: it| that| the alarm| the reminder)?(?: for (?P<dur>.+))?$"])
def snooze(m, ctx):
    last = SCHEDULER.last_fired
    if not last or time.time() - SCHEDULER.last_fired_at > 900:
        return "There's nothing to snooze right now."
    seconds = 300.0
    if m["dur"]:
        when = find_when("in " + m["dur"])
        if when is None or when.kind != "duration":
            return "How long should I snooze? Try: snooze for 10 minutes."
        seconds = when.seconds
    SCHEDULER.add(last["kind"], time.time() + seconds, last["text"], last.get("seconds"))
    return f"Snoozed for {spoken_duration(seconds)}."


@registry.skill("reminder or alarm", [
    r"^(?:please\s+)?remind me\b.*$",
    r"^(?:please\s+)?(?:set|create|make|add)\s+(?:me\s+)?(?:a\s+|an\s+)?(?:reminder|alarm)\b.*$",
    r"^(?:please\s+)?wake me up\b.*$",
], use_raw=True)
def reminder(m, ctx):
    raw = m.group(0)
    is_alarm = bool(re.search(r"\balarm\b|\bwake me\b", raw, re.IGNORECASE))
    now = datetime.now()
    when = find_when(raw, now, prefer_am=is_alarm)
    if when is None:
        return HELP_REMIND
    if (when.due - now).total_seconds() > MAX_SECONDS:
        return "That's too far away for me. Try something within a week."

    message = PREFIX.sub("", when.rest).strip(" ,.")
    kind = "alarm" if is_alarm else "reminder"
    SCHEDULER.add(kind, when.due.timestamp(), message)

    when_text = f"in {spoken_duration(when.seconds)}" if when.kind == "duration" else spoken_clock(when.due, now)
    if is_alarm:
        return f"Okay, alarm set {when_text}." + (f" I'll say: {to_second_person(message)}." if message else "")
    if message:
        return f"Okay, I'll remind you {when_text} to {to_second_person(message)}."
    return f"Okay, I'll remind you {when_text}."


@registry.skill("set timer", [
    r"^(?:please\s+)?(?:(?:set|start|create|make|begin)\s+)?(?:a\s+|an\s+|the\s+|my\s+)?(?:.*\s)?timer\b.*$",
], use_raw=True)
def set_timer(m, ctx):
    raw = m.group(0)
    if re.search(r"\b(?:cancel|stop|delete|remove|clear|how|what|left|remaining|snooze)\b", raw, re.IGNORECASE):
        return None
    when = find_when(raw, bare_duration=True)
    if when is None or when.kind != "duration":
        started = re.match(r"^(?:please\s+)?(?:set|start|create|make|begin)\b", raw, re.IGNORECASE)
        return HELP_TIMER if started else None
    if when.seconds > MAX_SECONDS:
        return "That's too long for me. Try something within a week."
    SCHEDULER.add("timer", when.due.timestamp(), "", when.seconds)
    return f"Timer set for {spoken_duration(when.seconds)}."