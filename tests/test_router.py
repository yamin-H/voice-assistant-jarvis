"""Tests for the speech normalization and step routing logic."""
from jarvis.router import normalize, split_steps


def test_normalize_strips_politeness_and_filler():
    # Wake word is handled upstream; router receives the core intent:
    raw = "Could you please open Chrome?"
    cleaned = normalize(raw)
    assert cleaned == "open chrome"


def test_normalize_handles_punctuation():
    raw = "What's the weather like today?!"
    cleaned = normalize(raw)
    assert cleaned == "what s the weather like today"


def test_split_steps_multiple_action_commands():
    # Actions that do not involve dictation split cleanly across steps
    command = "Open Notepad and then open Chrome and then show desktop"
    steps = split_steps(command)
    assert len(steps) == 3
    assert steps[0] == "Open Notepad"
    assert steps[1] == "open Chrome"
    assert steps[2] == "show desktop"


def test_split_steps_preserves_dictation_payload():
    # Safety feature: dictation steps preserve everything after "type" or "write"
    command = "Open Notepad and then type hello world and then press enter"
    steps = split_steps(command)
    assert len(steps) == 2
    assert steps[0] == "Open Notepad"
    assert steps[1] == "type hello world and then press enter"


def test_split_steps_single_command():
    command = "What time is it right now"
    steps = split_steps(command)
    assert len(steps) == 1
    assert steps[0] == "What time is it right now"