"""Notes: "note this down: buy milk", "read my notes", "show my notes"."""
import re
from datetime import datetime

from jarvis import store
from jarvis.config import get_data_dir
from jarvis.reply import Reply
from jarvis.skills.registry import registry

NOTES_FILE = get_data_dir() / "notes.txt"


def _tidy(text):
    return text.strip().rstrip(".!?").strip()


def _spoken_notes(notes):
    if not notes:
        return "You don't have any notes yet."
    shown = notes[-5:]
    first = len(notes) - len(shown) + 1
    if len(notes) == 1:
        intro = "You have one note."
    elif len(notes) <= 5:
        intro = f"You have {len(notes)} notes."
    else:
        intro = f"You have {len(notes)} notes. Here are the last 5."
    body = " ".join(f"Note {first + i}: {_tidy(n['text'])}." for i, n in enumerate(shown))
    return f"{intro} {body}"


@registry.skill("add note", [
    r"^(?:please\s+)?(?:take|make|add|create|save)\s+(?:a\s+|an\s+)?note(?:\s+(?:that|saying|to))?\s*[:,]?\s+(?P<text>.+)$",
    r"^(?:please\s+)?(?:note|jot|write)\s+(?:this\s+|that\s+|it\s+)?down\s*[:,]?\s*(?:that\s+)?(?P<text>.+)$",
    r"^(?:please\s+)?note\s+that\s+(?P<text>.+)$",
    r"^note\s*[:,]\s*(?P<text>.+)$",
], use_raw=True)
def add_note(m, ctx):
    if ctx.in_chain and m.string.lower().startswith("write"):
        return None  # "open notepad and write down ..." means type it, not save a note
    text = _tidy(m["text"])
    if not text:
        return None
    notes = store.load("notes", [])
    notes.append({"text": text, "time": datetime.now().isoformat(timespec="minutes")})
    store.save("notes", notes)
    return f"Noted: {text}." if len(text) <= 90 else "Noted."


@registry.skill("note help", [r"^(?:take|make|add)\s+(?:a\s+)?note$"])
def note_help(m, ctx):
    return "Say it together, like: note this down, buy milk."


@registry.skill("read notes", [
    r"^(?:read|tell)(?: me)?(?: back)?(?: all)?(?: of)?(?: my| the)? notes?$",
    r"^what(?: s| is| are)?(?: in)?(?: my| the)? notes?(?: are| say)?$",
    r"^what did i (?:note|write down|jot down)(?: down)?$",
])
def read_notes(m, ctx):
    return _spoken_notes(store.load("notes", []))


@registry.skill("read last note", [
    r"^(?:read|what s|what is|tell me)(?: me)?(?: my| the)? (?:last|latest|previous|recent) note$",
])
def read_last_note(m, ctx):
    notes = store.load("notes", [])
    if not notes:
        return "You don't have any notes yet."
    return f"Your last note says: {_tidy(notes[-1]['text'])}."


@registry.skill("count notes", [r"^how many notes(?: do i have| have i (?:saved|made|written))?$"])
def count_notes(m, ctx):
    n = len(store.load("notes", []))
    return "You don't have any notes." if n == 0 else f"You have {n} note{'s' if n != 1 else ''}."


@registry.skill("show notes", [
    r"^(?:show|open|display)(?: me)?(?: all)?(?: of)?(?: my| the)? notes?(?: file| list)?$",
])
def show_notes(m, ctx):
    notes = store.load("notes", [])
    if not notes:
        return "You don't have any notes yet."

    def act():
        from jarvis.skills import winapi  # Windows only, so we load it only when needed
        lines = [f"{i}. [{n['time'].replace('T', ' ')}] {n['text']}" for i, n in enumerate(notes, 1)]
        NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)
        NOTES_FILE.write_text("YOUR NOTES\n\n" + "\n".join(lines) + "\n", encoding="utf-8")
        winapi.launch(["notepad", str(NOTES_FILE)])

    return Reply("Opening your notes.", act)


@registry.skill("delete last note", [r"^(?:delete|remove|erase)(?: my| the)? (?:last|latest) note$"])
def delete_last_note(m, ctx):
    notes = store.load("notes", [])
    if not notes:
        return "You don't have any notes."
    last = _tidy(notes[-1]["text"])

    def do_it():
        current = store.load("notes", [])
        if current:
            current.pop()
            store.save("notes", current)
        return "Deleted."

    return Reply(f"Do you want me to delete your last note: {last}?", on_yes=do_it)


@registry.skill("clear notes", [r"^(?:delete|clear|erase|remove)(?: all)?(?: of)?(?: my| the)? notes$"])
def clear_notes(m, ctx):
    n = len(store.load("notes", []))
    if n == 0:
        return "You don't have any notes."

    def do_it():
        store.save("notes", [])
        return "All notes deleted."

    return Reply(f"Do you want me to delete all {n} note{'s' if n != 1 else ''}?", on_yes=do_it)