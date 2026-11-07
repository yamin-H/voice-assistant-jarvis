"""The router: turns what you said into a reply and an optional action.

Order: yes/no answers -> quit -> steps ("do this and then that") -> a single command.
Returns None when nothing matches. Then the chat brain answers.
"""
import re
from datetime import datetime

from jarvis import skills  # noqa: F401  (loading this registers all skills)
from jarvis.reply import Reply
from jarvis.skills.control import CANCEL
from jarvis.skills.registry import Context, registry
from jarvis.skills.winapi import (
    VK_VOLUME_DOWN,
    VK_VOLUME_MUTE,
    VK_VOLUME_UP,
    press_key,
)
from jarvis.vision.rules import vision_answer

YES = re.compile(r"^(?:yes|yeah|yep|yup|sure|okay|ok|do it|go ahead|confirm|affirmative)$")
NO = re.compile(r"^(?:no|nope|nah|cancel|stop|never mind|nevermind|don t|do not)$")
QUIT = re.compile(r"^(?:goodbye|bye bye|bye|exit|quit|shut down|stop listening|that s all|see you)$")

# A step starts at "and", "then" or "and then", but only when a command word follows.
STEP_VERBS = (
    r"(?:open|launch|start|run|type|write|dictate|search|google|look up|go to|snap|switch|close|"
    r"maximi[sz]e|minimi[sz]e|scroll|press|copy|paste|cut|take|play|pause|resume|save|select|"
    r"undo|redo|show|refresh|reload|next|previous|skip|put|move|focus|new|"
    r"set|remind|cancel|snooze|read|delete|clear)"
)
STEP_SPLIT = re.compile(
    r"\s*,?\s*\b(?:and then|and|then|after that|afterwards)\b\s+(?=" + STEP_VERBS + r"\b)",
    re.IGNORECASE,
)
TYPE_START = re.compile(
    r"^\s*(?:type|write|dictate|remind|remember|note|take a note|make a note|add a note|jot|don'?t forget)\b",
    re.IGNORECASE,
)


def normalize(text):
    """lowercase, no punctuation, no filler words."""
    t = text.lower()
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    t = re.sub(r"\b(jarvis|please)\b", " ", t)
    t = re.sub(r"^\s*(can|could|would) you ", "", t)
    return re.sub(r"\s+", " ", t).strip()


def split_steps(raw):
    """'Open Notepad and write hello' -> ['Open Notepad', 'write hello']."""
    # Prevent splitting "open youtube and play/search X" into two separate tabs
    if re.match(r"^\s*open youtube and (?:play|search)\b", raw, re.IGNORECASE):
        return [raw.strip()]

    steps, start = [], 0
    for match in STEP_SPLIT.finditer(raw):
        # Once a step is "type ..." or "write ...", the rest of the sentence belongs to it.
        if TYPE_START.match(raw[start:]):
            break
        steps.append(raw[start:match.start()].strip(" ,"))
        start = match.end()
    steps.append(raw[start:].strip(" ,"))
    return [s for s in steps if s]


class Router:
    def __init__(self, cfg, vision=None, brain=None):
        self.name = cfg["assistant"]["name"]
        self.user = cfg["assistant"]["user_name"]
        self.vision = vision
        self.ctx = Context(cfg=cfg, vision=vision, brain=brain, user=self.user)
        self.pending = None      # a yes/no question we are waiting for an answer to
        self.last_match = None   # name of the skill that handled the last sentence

    def route(self, text):
        raw = text.strip()
        t = normalize(raw)
        self.last_match = None
        if not t:
            return None

        # 1) An answer to a question we just asked.
        if self.pending is not None:
            pending, self.pending = self.pending, None
            if YES.match(t):
                return Reply(pending() or "Done.")
            if NO.match(t):
                return Reply("Okay, I won't.")
            # Anything else: forget the question and treat it as a new command.

        if QUIT.match(t):
            return Reply("Goodbye! See you soon.", quit=True)

        # 2) Several steps in one sentence.
        steps = split_steps(raw)
        if len(steps) > 1:
            self.last_match = "steps"
            return Reply("On it.", lambda: self._run_steps(steps))

        # 3) One command.
        reply = self._route_one(raw)
        if reply is not None and reply.on_yes:
            self.pending = reply.on_yes
        return reply

    def _run_steps(self, steps):
        """Runs the steps one after another. Returns a sentence to speak, or None."""
        ctx = self.ctx
        ctx.in_chain, ctx.last_hwnd = True, None
        messages = []
        try:
            for number, step in enumerate(steps, 1):
                if CANCEL.is_set():
                    return None
                print(f"  [step {number}/{len(steps)}] {step}")
                reply = self._route_one(step)
                if reply is None:
                    return " ".join(messages + [f"Sorry, I didn't understand: {step}."])
                if reply.on_yes:
                    return " ".join(messages + ["That needs your confirmation, so please ask me separately."])
                if reply.action:
                    problem = reply.action()
                    if isinstance(problem, str) and problem:
                        return " ".join(messages + [problem])  # a step failed: stop here
                else:
                    messages.append(reply.text)
            return " ".join(messages) or None
        finally:
            ctx.in_chain = False

    def _route_one(self, raw):
        t = normalize(raw)
        if not t:
            return None

        # Questions about what the camera sees.
        answer = vision_answer(t, self.vision)
        if answer:
            return Reply(answer)

        # Skills.
        hit = registry.match(t, raw, self.ctx)
        if hit:
            self.last_match, reply = hit
            return reply

        # Basic built-ins.
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

        return None