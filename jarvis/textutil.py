"""Small text helpers shared by the productivity skills."""
import re

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "am", "be", "been", "do", "does", "did",
    "my", "me", "i", "you", "your", "yours", "mine", "myself", "to", "of", "in", "on", "at",
    "for", "and", "or", "with", "from", "by", "as", "so", "if", "then", "there", "here", "it",
    "its", "that", "this", "these", "those", "what", "when", "where", "who", "which", "how",
    "why", "s", "im", "ive", "whats", "about", "tell", "remember", "know", "should", "can",
    "could", "will", "would", "have", "has", "had", "told", "said", "much", "many", "any",
    "some", "please", "again", "anything", "anyone", "something", "someone", "everything",
}


def to_second_person(text):
    """'my exam is on Friday' -> 'your exam is on Friday'."""
    text = text.replace("\u2019", "'")
    swaps = [
        (r"\bI'm\b", "you're"), (r"\bI am\b", "you are"), (r"\bI was\b", "you were"),
        (r"\bI've\b", "you've"), (r"\bI'll\b", "you'll"), (r"\bI'd\b", "you'd"),
        (r"\bmyself\b", "yourself"), (r"\bmine\b", "yours"), (r"\bmy\b", "your"),
        (r"\bme\b", "you"), (r"\bI\b", "you"),
    ]
    for pattern, new in swaps:
        text = re.sub(pattern, new, text, flags=re.IGNORECASE)
    return text


def keywords(text):
    """The meaningful words of a sentence (no filler words, plurals made singular)."""
    words = re.findall(r"[a-z0-9]+", text.lower().replace("'", "").replace("\u2019", ""))
    result = set()
    for word in words:
        if word in STOPWORDS:
            continue
        if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
            word = word[:-1]
        result.add(word)
    return result


def upper_first(text):
    """'your exam is on Friday' -> 'Your exam is on Friday' (the rest stays as it is)."""
    return text[:1].upper() + text[1:]