"""The skill registry: every skill is a function plus the phrases that trigger it."""
import re
from dataclasses import dataclass
from typing import Callable

from jarvis.reply import Reply


@dataclass
class Context:
    """Things a skill may need."""
    cfg: dict
    vision: object = None
    brain: object = None
    user: str = "friend"
    last_hwnd: object = None  # the window we opened last (this is what "it" means)
    last_app: str = None      # the app we opened last, like "chrome"
    in_chain: bool = False    # True while running steps like "open X and type Y"


@dataclass
class Skill:
    name: str
    patterns: list
    handler: Callable
    use_raw: bool  # True = match the exact words you said (keeps capitals and punctuation)


class Registry:
    def __init__(self):
        self.skills = []

    def skill(self, name, patterns, use_raw=False):
        """Decorator. The function gets (match, ctx) and returns a Reply, a string, or None."""
        def decorator(function):
            compiled = [re.compile(p, re.IGNORECASE) for p in patterns]
            self.skills.append(Skill(name, compiled, function, use_raw))
            return function
        return decorator

    def match(self, clean, raw, ctx):
        """Returns (skill name, Reply) for the first skill that handles it, or None."""
        for skill in self.skills:
            text = raw.strip() if skill.use_raw else clean
            for pattern in skill.patterns:
                found = pattern.match(text)
                if not found:
                    continue
                try:
                    result = skill.handler(found, ctx)
                except Exception as error:
                    print(f"  [skill error in '{skill.name}'] {error}")
                    return skill.name, Reply("Sorry, something went wrong with that.")
                if result is None:
                    continue  # the skill declined, so try the next one
                if isinstance(result, str):
                    result = Reply(result)
                return skill.name, result
        return None


registry = Registry()