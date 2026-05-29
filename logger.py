import csv
import json
import logging
import time
from pathlib import Path
from typing import List, Optional, Union

from .toggle import Toggle, ToggleEvent

_root = logging.getLogger("toggletest")


def setup_logging(level=logging.DEBUG, log_file=None,
                  fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s"):
    _root.setLevel(level)
    formatter = logging.Formatter(fmt)
    if not _root.handlers:
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        _root.addHandler(console)
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        _root.addHandler(fh)


class ToggleLogger:
    """
    Attach to one or more Toggle objects and collect all events
    into a structured log exportable to CSV or JSON.

    Example
    -------
    >>> tlog = ToggleLogger(session_name="power_switch_test")
    >>> tlog.attach(toggle_a)
    >>> tlog.to_csv("results/run_001.csv")
    >>> tlog.print_report()
    """

    def __init__(self, session_name="session"):
        self.session_name = session_name
        self.session_start = time.monotonic()
        self.wall_start = time.time()
        self._events = []
        self._toggles = []

    def attach(self, toggle):
        """Register a toggle — all its future events will be captured."""
        toggle.on_change(self._capture)
        self._toggles.append(toggle)

    def _capture(self, event):
        self._events.append({
            "session": self.session_name,
            "label": next(
                (t.label for t in self._toggles if t.pin == event.pin),
                f"pin{event.pin}"
            ),
            "pin": event.pin,
            "state": int(event.state),
            "state_label": event.state_label,
            "timestamp": event.timestamp,
            "elapsed_s": round(event.timestamp - self.session_start, 6),
            "source": event.source,
        })

    @property
    def events(self): return list(self._events)

    @property
    def event_count(self): return len(self._events)

    def to_csv(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fields = ["session", "label", "pin", "state", "state_label",
                  "timestamp", "elapsed_s", "source"]
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(self._events)
        return path

    def to_json(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "session": self.session_name,
            "wall_start": self.wall_start,
            "event_count": self.event_count,
            "events": self._events,
        }
        with open(path, "w") as f:
            json.dump(payload, f, indent=2)
        return path

    def print_report(self):
        elapsed = time.monotonic() - self.session_start
        print(f"\n{'='*55}")
        print(f"  Toggle Test Session: {self.session_name}")
        print(f"  Duration : {elapsed:.2f}s")
        print(f"  Events   : {self.event_count}")
        print(f"{'='*55}")
        for toggle in self._toggles:
            print(toggle.summary())
            print()
        if self._events:
            print("  Event log:")
            for ev in self._events[-20:]:
                print(f"    [{ev['elapsed_s']:>8.4f}s] {ev['label']:20s} → {ev['state_label']}")
            if self.event_count > 20:
                print(f"    ... ({self.event_count - 20} earlier events not shown)")
        print(f"{'='*55}\n")