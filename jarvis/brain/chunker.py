"""Turns a stream of tokens into short speakable pieces."""
import re

BOUNDARY = re.compile(r"[.!?]\s")
JUNK = re.compile(r"[*_#`~>|]|[\U0001F300-\U0001FAFF\u2600-\u27BF]")


def clean(text):
    """Removes symbols and emojis that sound strange when spoken."""
    return JUNK.sub("", text)


def speakable_pieces(tokens, first_min=40):
    """Yields a piece each time a sentence ends.

    The very first piece may end at a comma, so speech starts sooner.
    """
    buffer = ""
    first = True
    for token in tokens:
        buffer += token
        while True:
            match = BOUNDARY.search(buffer)
            comma = buffer.rfind(",")
            if match:
                end = match.start() + 1
            elif first and len(buffer) >= first_min and comma >= 15:
                end = comma + 1
            else:
                break
            piece = clean(buffer[:end]).strip()
            buffer = buffer[end:]
            if piece:
                yield piece
                first = False
    rest = clean(buffer).strip()
    if rest:
        yield rest