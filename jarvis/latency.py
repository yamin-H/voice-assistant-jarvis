"""Tiny tool to measure how long each stage takes (in milliseconds)."""
import time
from contextlib import contextmanager


class LatencyLog:
    def __init__(self, show=True):
        self.show = show
        self.records = []  # list of (stage_name, milliseconds)

    @contextmanager
    def measure(self, stage):
        start = time.perf_counter()
        try:
            yield
        finally:
            ms = (time.perf_counter() - start) * 1000
            self.records.append((stage, ms))
            if self.show:
                print(f"  [latency] {stage}: {ms:.0f} ms")

    def summary(self):
        print("\nLatency summary:")
        for stage, ms in self.records:
            print(f"  {stage:<25} {ms:>8.0f} ms")