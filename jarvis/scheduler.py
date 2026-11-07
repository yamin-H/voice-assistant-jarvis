"""Timers and reminders. Saved to disk, so they survive restarts."""
import threading
import time

from jarvis import store


class Scheduler:
    def __init__(self):
        self._lock = threading.RLock()
        self.items = store.load("reminders", [])
        self.last_fired = None
        self.last_fired_at = 0.0

    def _save(self):
        store.save("reminders", self.items)

    def add(self, kind, due_ts, text="", seconds=None):
        """kind = 'timer', 'reminder' or 'alarm'. due_ts = when it goes off (time.time())."""
        with self._lock:
            item = {"id": int(time.time() * 1000), "kind": kind, "due": due_ts,
                    "text": text, "seconds": seconds}
            self.items.append(item)
            self._save()
            return item

    def pending(self, kinds=None):
        """Waiting items, soonest first."""
        with self._lock:
            found = [i for i in self.items if kinds is None or i["kind"] in kinds]
            return sorted(found, key=lambda i: i["due"])

    def cancel(self, kinds=None):
        """Removes waiting items. Returns how many were removed."""
        with self._lock:
            keep = [i for i in self.items if kinds is not None and i["kind"] not in kinds]
            removed = len(self.items) - len(keep)
            self.items = keep
            if removed:
                self._save()
            return removed

    def pop_due(self):
        """Returns the items whose time has come (and removes them)."""
        now = time.time()
        with self._lock:
            if not any(i["due"] <= now for i in self.items):
                return []
            due = sorted((i for i in self.items if i["due"] <= now), key=lambda i: i["due"])
            self.items = [i for i in self.items if i["due"] > now]
            self._save()
            self.last_fired, self.last_fired_at = due[-1], now
            return due


SCHEDULER = Scheduler()


def spoken(item):
    """The sentence Jarvis says when an item goes off."""
    from jarvis.textutil import to_second_person
    from jarvis.timeparse import spoken_duration

    late = time.time() - item["due"] > 90  # it went off while Jarvis was not running
    text = (item.get("text") or "").strip()
    if item["kind"] == "timer":
        seconds = item.get("seconds")
        sentence = f"Your timer for {spoken_duration(seconds)} is done." if seconds else "Your timer is done."
    elif item["kind"] == "alarm":
        sentence = f"Alarm: {to_second_person(text)}." if text else "Your alarm is going off."
    else:
        sentence = f"Reminder: {to_second_person(text)}." if text else "This is your reminder."
    return ("Sorry, I missed this while I was off. " + sentence) if late else sentence