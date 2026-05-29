import time
import threading
import logging
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from .backends.base import HardwareBackend

logger = logging.getLogger("toggletest.toggle")


@dataclass
class ToggleEvent:
    pin: int
    state: bool
    timestamp: float
    source: str = "read"

    @property
    def state_label(self) -> str:
        return "HIGH" if self.state else "LOW"

    def __repr__(self) -> str:
        return f"ToggleEvent(pin={self.pin}, state={self.state_label}, t={self.timestamp:.4f}s, source={self.source!r})"


class Toggle:
    def __init__(self, backend, pin, mode="INPUT", debounce_ms=50.0, label=None):
        self._backend = backend
        self._pin = pin
        self._mode = mode.upper()
        self._debounce_s = debounce_ms / 1000.0
        self.label = label or f"toggle_pin{pin}"
        self._last_state = None
        self._last_change_time = 0.0
        self._callbacks = []
        self._history = []
        self._monitor_thread = None
        self._stop_event = threading.Event()
        self._backend.configure_pin(pin, self._mode)

    @property
    def pin(self): return self._pin

    @property
    def mode(self): return self._mode

    def read(self):
        raw = self._backend.read_pin(self._pin)
        now = time.monotonic()
        if self._last_state is None:
            self._last_state = raw
            self._last_change_time = now
            event = ToggleEvent(pin=self._pin, state=raw, timestamp=now, source="init")
            self._history.append(event)
            self._fire_callbacks(event)
        elif self._debounce_s > 0:
            if raw != self._last_state:
                if (now - self._last_change_time) >= self._debounce_s:
                    self._record_change(raw, now, source="debounced")
        else:
            if raw != self._last_state:
                self._record_change(raw, now, source="read")
        return self._last_state if self._last_state is not None else raw

    def read_raw(self): return self._backend.read_pin(self._pin)

    def write(self, state):
        if self._mode != "OUTPUT":
            raise RuntimeError(f"Toggle '{self.label}' is INPUT — cannot write.")
        self._backend.write_pin(self._pin, state)
        event = ToggleEvent(pin=self._pin, state=state, timestamp=time.monotonic(), source="write")
        self._history.append(event)
        self._last_state = state
        self._fire_callbacks(event)

    def toggle(self):
        current = self._last_state if self._last_state is not None else False
        new_state = not current
        self.write(new_state)
        return new_state

    def pulse(self, duration_ms=100.0):
        self.write(True)
        time.sleep(duration_ms / 1000.0)
        self.write(False)

    def on_change(self, callback): self._callbacks.append(callback)

    def monitor(self, duration=None, poll_hz=100.0, background=False):
        self._stop_event.clear()
        interval = 1.0 / poll_hz
        def _run():
            deadline = (time.monotonic() + duration) if duration else None
            while not self._stop_event.is_set():
                self.read()
                if deadline and time.monotonic() >= deadline:
                    break
                time.sleep(interval)
        if background:
            self._monitor_thread = threading.Thread(target=_run, daemon=True)
            self._monitor_thread.start()
            return []
        _run()
        return list(self._history)

    def stop_monitor(self):
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)

    @property
    def history(self): return list(self._history)

    @property
    def change_count(self):
        return sum(1 for e in self._history if e.source != "init")

    def wait_for_state(self, target, timeout=5.0, poll_hz=100.0):
        deadline = time.monotonic() + timeout
        interval = 1.0 / poll_hz
        while time.monotonic() < deadline:
            if self.read() == target:
                return True
            time.sleep(interval)
        return False

    def clear_history(self):
        self._history.clear()
        self._last_state = None
        self._last_change_time = 0.0

    def summary(self):
        highs = sum(1 for e in self._history if e.state)
        lows = sum(1 for e in self._history if not e.state)
        duration = (self._history[-1].timestamp - self._history[0].timestamp) if len(self._history) >= 2 else 0.0
        return (f"Toggle '{self.label}' (pin {self._pin})\n"
                f"  Total changes : {self.change_count}\n"
                f"  HIGH events   : {highs}\n"
                f"  LOW events    : {lows}\n"
                f"  Span          : {duration:.3f}s\n"
                f"  Mode          : {self._mode}\n"
                f"  Debounce      : {self._debounce_s * 1000:.1f}ms")

    def _record_change(self, state, timestamp, source):
        event = ToggleEvent(pin=self._pin, state=state, timestamp=timestamp, source=source)
        self._history.append(event)
        self._last_state = state
        self._last_change_time = timestamp
        self._fire_callbacks(event)

    def _fire_callbacks(self, event):
        for cb in self._callbacks:
            try: cb(event)
            except Exception as exc: logger.warning("Callback error: %s", exc)

    def __repr__(self):
        return f"Toggle(label={self.label!r}, pin={self._pin}, mode={self._mode}, changes={self.change_count})"