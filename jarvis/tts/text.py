"""Splits text into short pieces so the first sound starts quickly."""
import re


def split_for_speech(text, max_len=70):
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    pieces = []
    for sentence in sentences:
        if len(sentence) <= max_len:
            pieces.append(sentence)
            continue
        # Long sentence: break it at commas, but keep pieces reasonably long.
        parts = re.split(r"(?<=[,;:])\s+", sentence)
        current = ""
        for part in parts:
            if current and len(current) + len(part) + 1 > max_len:
                pieces.append(current)
                current = part
            else:
                current = (current + " " + part).strip()
        if current:
            pieces.append(current)
    return [p for p in pieces if p]