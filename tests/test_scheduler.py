import time
from jarvis.scheduler import Scheduler


def test_scheduler_add_and_pending(mock_data_dir):
    sched = Scheduler()
    sched.items.clear()

    future_ts = time.time() + 300
    sched.add(kind="timer", due_ts=future_ts, text="Tea timer", seconds=300)

    pending = sched.pending(["timer"])
    assert len(pending) == 1
    assert pending[0]["text"] == "Tea timer"


def test_scheduler_pop_due(mock_data_dir):
    sched = Scheduler()
    sched.items.clear()

    past_ts = time.time() - 10
    future_ts = time.time() + 600

    sched.add(kind="timer", due_ts=past_ts, text="Past")
    sched.add(kind="timer", due_ts=future_ts, text="Future")

    due = sched.pop_due()
    assert len(due) == 1
    assert due[0]["text"] == "Past"

    # Only future item remains
    assert len(sched.pending()) == 1


def test_scheduler_cancel(mock_data_dir):
    sched = Scheduler()
    sched.items.clear()

    sched.add(kind="timer", due_ts=time.time() + 100, text="Timer 1")
    sched.add(kind="alarm", due_ts=time.time() + 200, text="Alarm 1")

    removed = sched.cancel(["timer"])
    assert removed == 1

    remaining = sched.pending()
    assert len(remaining) == 1
    assert remaining[0]["kind"] == "alarm"