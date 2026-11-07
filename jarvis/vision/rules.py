"""Recognizes vision questions ("what do you see?") and answers them from the camera."""
import re

from jarvis.vision.describe import answer_count, answer_find, describe
from jarvis.vision.detector import COCO_NAMES

# Everyday words people use for the 80 object types.
SYNONYMS = {
    "people": "person", "persons": "person", "human": "person", "humans": "person",
    "me": "person", "myself": "person", "anyone": "person", "anybody": "person",
    "someone": "person", "somebody": "person", "man": "person", "woman": "person",
    "phone": "cell phone", "mobile": "cell phone", "smartphone": "cell phone",
    "cellphone": "cell phone", "mug": "cup", "computer": "laptop",
    "monitor": "tv", "screen": "tv", "television": "tv", "sofa": "couch",
    "table": "dining table", "plant": "potted plant", "teddy": "teddy bear",
    "bag": "handbag", "controller": "remote", "remote control": "remote",
}

DESCRIBE = re.compile(
    r"\b(what do you see|what can you see|what are you seeing|what s in front of me|"
    r"what is in front of me|what am i holding|describe what you see|"
    r"tell me what you see|look around)\b"
)
FIND = re.compile(
    r"^(?:is there|are there|do you see|can you see|do you notice) "
    r"(?:any |a |an |the |some )?(.+)$"
)
COUNT = re.compile(r"^how many (.+?)(?: are | do | can | is | in | on | at |$)")
COUNT_CONTEXT = re.compile(
    r"\b(room|here|see|camera|front of me|in view|visible|screen|table|desk)\b"
)
CUT = re.compile(r" (?:on|in|near|behind|around|here|there|at|next|over|under|beside)\b")
DETERMINERS = re.compile(r"^(?:a|an|the|my|your|any|some|this|that)\s+")

OFF_MESSAGE = "My camera is turned off. You can turn it on in the settings file."


def resolve_label(noun):
    """Turns a spoken word into one of the 80 object names (or None)."""
    noun = DETERMINERS.sub("", noun.strip())
    candidates = [noun]
    if noun.endswith("ies"):
        candidates.append(noun[:-3] + "y")
    if noun.endswith("es"):
        candidates.append(noun[:-2])
    if noun.endswith("s"):
        candidates.append(noun[:-1])
    for word in candidates:
        if word in SYNONYMS:
            return SYNONYMS[word]
        if word in COCO_NAMES:
            return word
    return None


def vision_answer(t, vision):
    """t = what you said (already cleaned). Returns the answer text, or None if it is
    not a vision question."""
    kind, label = None, None

    count_match = COUNT.match(t)
    find_match = FIND.match(t)
    if DESCRIBE.search(t):
        kind = "describe"
    elif count_match and COUNT_CONTEXT.search(t):
        label = resolve_label(count_match.group(1))
        kind = "count" if label else None
    elif find_match:
        label = resolve_label(CUT.split(find_match.group(1))[0])
        kind = "find" if label else None

    if kind is None:
        return None
    if vision is None:
        return OFF_MESSAGE

    try:
        detections = vision.look()
    except Exception as error:
        print(f"  [vision error] {error}")
        return "Sorry, I can't use the camera right now."

    if kind == "describe":
        return describe(detections, vision.sure)
    if kind == "count":
        return answer_count(detections, label, vision.sure)
    return answer_find(detections, label, vision.sure)