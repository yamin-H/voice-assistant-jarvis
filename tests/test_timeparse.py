from datetime import datetime
from jarvis.timeparse import find_when, spoken_clock, spoken_duration


def test_duration_parsing_minutes():
    now = datetime(2026, 1, 1, 12, 0, 0)
    result = find_when("set a timer for 10 minutes", now=now)
    assert result is not None
    assert result.kind == "duration"
    assert result.seconds == 600.0
    assert result.due == datetime(2026, 1, 1, 12, 10, 0)


def test_duration_parsing_hours_and_half():
    now = datetime(2026, 1, 1, 12, 0, 0)
    result = find_when("remind me in an hour and a half to call mom", now=now)
    assert result is not None
    assert result.kind == "duration"
    assert result.seconds == 5400.0
    assert "call mom" in result.rest


def test_clock_parsing_pm():
    now = datetime(2026, 1, 1, 10, 0, 0)
    result = find_when("remind me at 5:30 pm to stretch", now=now)
    assert result is not None
    assert result.kind == "clock"
    assert result.due == datetime(2026, 1, 1, 17, 30, 0)
    assert "stretch" in result.rest


def test_spoken_duration_formatting():
    assert spoken_duration(60) == "1 minute"
    assert spoken_duration(3600) == "1 hour"
    assert spoken_duration(3665) == "1 hour, 1 minute and 5 seconds"
    assert spoken_duration(0) == "0 seconds"


def test_spoken_clock_formatting():
    ref = datetime(2026, 1, 1, 10, 0, 0)
    due_today = datetime(2026, 1, 1, 15, 30, 0)
    due_tomorrow = datetime(2026, 1, 2, 9, 0, 0)

    assert spoken_clock(due_today, now=ref) == "at 3:30 PM"
    assert spoken_clock(due_tomorrow, now=ref) == "tomorrow at 9 AM"