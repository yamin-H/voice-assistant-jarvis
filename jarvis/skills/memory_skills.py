"""Memory: "remember that my exam is on Friday", then later "when is my exam?"."""
import re
from datetime import datetime

from jarvis import store
from jarvis.reply import Reply
from jarvis.skills.registry import registry
from jarvis.textutil import keywords, to_second_person, upper_first

ALL_WORDS = {"everything", "all", "it all", "everything you know", "all of it", "all of that",
             "everything about me", "all of them"}


def _load():
    return store.load("memory", [])


def _tidy(text):
    return text.strip().rstrip(".!?").strip()


def _sentence(fact):
    return to_second_person(_tidy(fact["text"]))


def _best(words, facts):
    """The facts that share the most keywords with `words`. -> (facts, number of shared words)."""
    scored = [(len(words & keywords(f["text"])), f) for f in facts]
    best = max((s for s, _ in scored), default=0)
    if best == 0:
        return [], 0
    return [f for s, f in scored if s == best][:2], best


@registry.skill("remember", [
    r"^(?:please\s+)?(?:remember|keep in mind)(?:\s+that)?\s*[:,]?\s+(?P<text>.+)$",
    r"^(?:please\s+)?don'?t forget(?:\s+that)?\s*[:,]?\s+(?P<text>.+)$",
], use_raw=True)
def remember(m, ctx):
    text = _tidy(m["text"])
    if len(text.split()) < 2:
        return None
    facts = _load()
    if any(_tidy(f["text"]).lower() == text.lower() for f in facts):
        return "I already know that."
    facts.append({"text": text, "time": datetime.now().isoformat(timespec="minutes")})
    store.save("memory", facts)
    return f"Okay, I'll remember that {to_second_person(text)}."


@registry.skill("forget", [r"^forget(?: about| that)?\s+(?P<what>.+)$"])
def forget(m, ctx):
    what = m["what"].strip()
    facts = _load()
    if not facts:
        return "I don't have anything saved yet."

    if what in ALL_WORDS:
        def clear_all():
            store.save("memory", [])
            return "Okay, I've forgotten everything."
        return Reply(f"Do you want me to forget all {len(facts)} things I remember?", on_yes=clear_all)

    matches, _ = _best(keywords(what), facts)
    if not matches:
        return "I don't have anything saved about that."
    target = matches[0]

    def forget_one():
        store.save("memory", [f for f in _load() if f["text"] != target["text"]])
        return "Okay, forgotten."

    return Reply(f"Do you want me to forget that {_sentence(target)}?", on_yes=forget_one)


@registry.skill("list memory", [
    r"^what do you (?:remember|know)(?: about me)?$",
    r"^what have i told you$",
])
def list_memory(m, ctx):
    facts = _load()
    if not facts:
        return "I don't remember anything yet. Tell me: remember that, and then what you want me to know."
    shown = facts[-5:]
    intro = f"I remember {len(facts)} thing{'s' if len(facts) != 1 else ''}."
    if len(facts) > 5:
        intro += " Here are the latest 5."
    return intro + " " + " ".join(f"{upper_first(_sentence(f))}." for f in shown)


@registry.skill("memory about topic", [r"^what do you (?:remember|know) about (?P<topic>.+)$"])
def memory_topic(m, ctx):
    words = keywords(m["topic"])
    if not words:
        return None
    matches, _ = _best(words, _load())
    if not matches:
        return f"I don't remember anything about {m['topic']}."
    return " ".join(f"{upper_first(_sentence(f))}." for f in matches)


@registry.skill("do you remember", [r"^do you (?:remember|know) (?:what |when |where |who )?(?P<topic>.+)$"])
def do_you_remember(m, ctx):
    words = keywords(m["topic"])
    if not words:
        return None
    matches, _ = _best(words, _load())
    if not matches:
        return None  # not something we saved, so let the chat brain answer ("do you know python?")
    return "Yes. " + " ".join(f"{upper_first(_sentence(f))}." for f in matches)


@registry.skill("recall", [
    r"^(?:when|what|where|who|which|how|do|did|am|is|are|was|were|whats)\b.*"
    r"\b(?:my|i|me|mine|myself|i m|i ve)\b.*$",
])
def recall(m, ctx):
    words = keywords(m.string)
    if not words:
        return None
    matches, shared = _best(words, _load())
    if not matches or not (shared >= 2 or shared / len(words) >= 0.6):
        return None  # nothing saved about this, so let the chat brain answer
    first = f"You told me that {_sentence(matches[0])}."
    if len(matches) > 1:
        return first + f" Also, {_sentence(matches[1])}."
    return first