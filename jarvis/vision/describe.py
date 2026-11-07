"""Turns detections into spoken sentences. It only says what the detector really found."""
from collections import Counter

# How some labels are spoken.
DISPLAY = {"tv": "TV", "dining table": "table", "potted plant": "plant"}
IRREGULAR_PLURALS = {
    "person": "people", "knife": "knives", "sandwich": "sandwiches", "bus": "buses",
    "wine glass": "wine glasses", "scissors": "scissors", "skis": "skis",
    "broccoli": "broccoli", "sheep": "sheep", "TV": "TVs",
}


def plural_name(label):
    name = DISPLAY.get(label, label)
    return IRREGULAR_PLURALS.get(name, name + "s")


def phrase(label, n):
    """'a cup' or '3 cups'."""
    name = DISPLAY.get(label, label)
    if n == 1:
        article = "an" if name[0].lower() in "aeiou" else "a"
        return f"{article} {name}"
    return f"{n} {plural_name(label)}"


def join_words(parts):
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " and " + parts[-1]


def describe(detections, sure):
    """'What do you see?'"""
    confident = [d for d in detections if d.conf >= sure]
    if confident:
        items = Counter(d.label for d in confident).most_common()
        parts = [phrase(label, n) for label, n in items[:6]]
        text = "I can see " + join_words(parts)
        if len(items) > 6:
            text += " and a few other things"
        return text + "."
    if detections:
        return (
            f"I'm not sure, but it might be {phrase(detections[0].label, 1)}. "
            "Try holding it closer to the camera."
        )
    return "I don't see anything I recognize right now."


def answer_find(detections, label, sure):
    """'Is there a cup?'"""
    matches = [d for d in detections if d.label == label]
    sure_count = sum(1 for d in matches if d.conf >= sure)
    if sure_count:
        return f"Yes, I can see {phrase(label, sure_count)}."
    if matches:
        return f"I'm not sure. There might be {phrase(label, 1)}, but I can't tell."
    return f"No, I don't see {phrase(label, 1)} right now."


def answer_count(detections, label, sure):
    """'How many people are here?'"""
    count = sum(1 for d in detections if d.label == label and d.conf >= sure)
    if count:
        return f"I can see {phrase(label, count)}."
    if any(d.label == label for d in detections):
        return f"I'm not sure. There might be {phrase(label, 1)}, but I can't tell."
    return f"I don't see any {plural_name(label)}."