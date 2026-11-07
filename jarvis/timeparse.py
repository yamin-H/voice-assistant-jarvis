"""Understands times inside sentences: "in 10 minutes", "at 5:30 pm", "tomorrow at 9"."""
import re
from dataclasses import dataclass
from datetime import datetime, timedelta

UNITS = {
    "second": 1, "seconds": 1, "sec": 1, "secs": 1,
    "minute": 60, "minutes": 60, "min": 60, "mins": 60,
    "hour": 3600, "hours": 3600, "hr": 3600, "hrs": 3600,
}
ONES = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19,
}
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
        "seventy": 70, "eighty": 80, "ninety": 90}
AND_A_HALF = ["and", "a", "half"]


@dataclass
class When:
    due: datetime
    kind: str       # "duration" or "clock"
    seconds: float  # the length, for durations
    rest: str       # the sentence with the time words taken out


# ---------- numbers and durations ----------
def number_at(words, i):
    """Reads a number at position i ("10", "ten", "twenty five", "a"). -> (value, next_i)."""
    if i >= len(words):
        return None
    w = words[i]
    if re.fullmatch(r"\d+(?:\.\d+)?", w):
        return float(w), i + 1
    if w in ("a", "an"):
        return 1.0, i + 1
    if w in TENS:
        value = TENS[w]
        if i + 1 < len(words) and words[i + 1] in ONES and 1 <= ONES[words[i + 1]] <= 9:
            return float(value + ONES[words[i + 1]]), i + 2
        return float(value), i + 1
    if w in ONES:
        return float(ONES[w]), i + 1
    return None


def _one_part(words, i):
    if words[i:i + 3] in (["half", "an", "hour"], ["half", "a", "hour"]):
        return 1800.0, i + 3
    got = number_at(words, i)
    if got is None:
        return None
    value, k = got
    if words[k:k + 3] == AND_A_HALF:  # "one and a half hours"
        value += 0.5
        k += 3
    if k >= len(words) or words[k] not in UNITS:
        return None
    per_unit = UNITS[words[k]]
    k += 1
    if words[k:k + 3] == AND_A_HALF:  # "an hour and a half"
        value += 0.5
        k += 3
    return value * per_unit, k


def duration_at(words, i):
    """Reads '10 minutes', 'half an hour', '1 hour and 30 minutes'. -> (seconds, next_i)."""
    part = _one_part(words, i)
    if part is None:
        return None
    total, j = part
    start = j + 1 if j < len(words) and words[j] == "and" else j
    more = duration_at(words, start) if start < len(words) else None
    if more:
        total += more[0]
        j = more[1]
    return total, j


# ---------- clock times ----------
def _ampm_at(words, j):
    """Reads am / pm / 'in the evening'. -> ('am' | 'pm' | None, next_j)."""
    if j >= len(words):
        return None, j
    w = words[j].replace(".", "")
    if w in ("am", "pm"):
        return w, j + 1
    if w in ("a", "p") and j + 1 < len(words) and words[j + 1].replace(".", "") == "m":
        return w + "m", j + 2
    if words[j:j + 2] == ["in", "the"] and j + 2 < len(words):
        if words[j + 2] == "morning":
            return "am", j + 3
        if words[j + 2] in ("afternoon", "evening"):
            return "pm", j + 3
    return None, j


def clock_at(words, i):
    """Reads '5', '5:30', '5 pm', 'five thirty', 'noon'. -> (hour, minute, ampm, next_i)."""
    if i >= len(words):
        return None
    w = words[i]
    if w == "noon":
        return 12, 0, "pm", i + 1
    if w == "midnight":
        return 12, 0, "am", i + 1

    m = re.fullmatch(r"(\d{1,2}):(\d{2})(am|pm)?", w)
    if m:
        hour, minute, ampm, j = int(m[1]), int(m[2]), m[3], i + 1
    else:
        m = re.fullmatch(r"(\d{1,2})(am|pm)?", w)
        if m:
            hour, ampm, j = int(m[1]), m[2], i + 1
        elif w in ONES and 1 <= ONES[w] <= 12:
            hour, ampm, j = ONES[w], None, i + 1
        else:
            return None
        minute = 0
        if j < len(words) and words[j] in ("oclock", "o'clock"):
            j += 1
        else:  # a minute may follow: "five thirty", "5 30"
            nxt = number_at(words, j)
            if nxt and words[j] not in ("a", "an") and 10 <= nxt[0] <= 59:
                minute, j = int(nxt[0]), nxt[1]

    if ampm is None:
        ampm, j = _ampm_at(words, j)
    if minute > 59 or hour > 23:
        return None
    if ampm and not 1 <= hour <= 12:
        return None
    return hour, minute, ampm, j


def _clock_due(now, hour, minute, ampm, day_offset, prefer_am=False):
    base = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=day_offset)

    def at(hour24, extra_days=0):
        return base + timedelta(days=extra_days, hours=hour24, minutes=minute)

    def guess(h):
        """Without am/pm: 7 to 11 means morning, everything else means afternoon or evening."""
        return h if 7 <= h <= 11 else h % 12 + 12

    if ampm == "pm":
        due = at(hour % 12 + 12)
    elif ampm == "am":
        due = at(hour % 12)
    elif hour == 0 or hour >= 13:
        due = at(hour)  # already a 24-hour time
    elif prefer_am and hour <= 11:
        due = at(hour)  # alarms and wake-ups: "at 7" means the morning
    elif day_offset:
        return at(guess(hour))  # "tomorrow at 5" is 5 in the afternoon
    else:
        # "at 5": the next 5 o'clock that is still ahead of us.
        options = sorted([at(hour % 12), at(hour % 12 + 12)])
        future = [o for o in options if o > now]
        return future[0] if future else at(guess(hour), 1)

    if day_offset == 0 and due <= now:
        due += timedelta(days=1)
    return due


# ---------- find the time inside a sentence ----------
def find_when(text, now=None, bare_duration=False, prefer_am=False):
    """Finds a time in a sentence. Returns When, or None.

    bare_duration=True also accepts '5 minute timer' (no 'in' or 'for' before the number).
    prefer_am=True makes a plain "at 7" mean 7 in the morning (for alarms).
    """
    now = now or datetime.now()
    spaced = text.replace("-", " ")  # same length, so the positions still match `text`
    tokens = [
        (m.group().strip(".,!?;:").lower(), m.start(), m.end())
        for m in re.finditer(r"[A-Za-z0-9.:']+", spaced)
    ]
    words = [t[0] for t in tokens]

    day_offset = 1 if "tomorrow" in words else 0
    due, kind, seconds, cuts = None, None, 0.0, []
    part_of_day = None  # "tomorrow evening at 8" -> pm
    i = 0
    while i < len(words):
        w = words[i]
        if w in ("tomorrow", "today", "tonight"):
            end = i
            if w == "tonight":
                part_of_day = "pm"
            elif i + 1 < len(words) and words[i + 1] in ("morning", "afternoon", "evening", "night"):
                end = i + 1  # also take out the word after it
                part_of_day = "am" if words[end] == "morning" else "pm"
            cuts.append((tokens[i][1], tokens[end][2]))
            i = end + 1
            continue

        if due is None:
            if w in ("in", "after", "for"):
                got = duration_at(words, i + 1)
            elif bare_duration:
                got = duration_at(words, i)
            else:
                got = None
            if got:
                seconds, j = got
                due, kind = now + timedelta(seconds=seconds), "duration"
                cuts.append((tokens[i][1], tokens[j - 1][2]))
                i = j
                continue

            if w in ("at", "for"):
                got = clock_at(words, i + 1)
                if got:
                    hour, minute, ampm, j = got
                    ampm = ampm or (part_of_day if 1 <= hour <= 12 else None)
                    due, kind = _clock_due(now, hour, minute, ampm, day_offset, prefer_am), "clock"
                    cuts.append((tokens[i][1], tokens[j - 1][2]))
                    i = j
                    continue
        i += 1

    if due is None:
        return None
    rest, last = "", 0
    for start, end in sorted(cuts):
        rest += text[last:start]
        last = end
    rest += text[last:]
    return When(due, kind, seconds, re.sub(r"\s+", " ", rest).strip(" ,.-"))


# ---------- speaking times ----------
def spoken_duration(seconds):
    seconds = int(round(seconds))
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    parts = []
    for value, name in ((hours, "hour"), (minutes, "minute"), (secs, "second")):
        if value:
            parts.append(f"{value} {name}" + ("" if value == 1 else "s"))
    if not parts:
        return "0 seconds"
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " and " + parts[-1]


def spoken_clock(due, now=None):
    now = now or datetime.now()
    hour = due.strftime("%I").lstrip("0") or "12"
    minute = due.strftime("%M")
    clock = f"{hour} {due.strftime('%p')}" if minute == "00" else f"{hour}:{minute} {due.strftime('%p')}"
    days = (due.date() - now.date()).days
    if days == 0:
        return f"at {clock}"
    if days == 1:
        return f"tomorrow at {clock}"
    return f"on {due.strftime('%A')} at {clock}"