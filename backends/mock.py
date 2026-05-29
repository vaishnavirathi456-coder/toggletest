from collections import deque
from typing import Dict, List, Optional
from .base import HardwareBackend


class MockBackend(HardwareBackend):
    """In-memory mock backend — no hardware required."""

    def __init__(self, initial_states=None, scripted_reads=None):
        self._states = dict(initial_states or {})
        self._modes = {}
        self._scripted = {
            pin: deque(seq)
            for pin, seq in (scripted_reads or {}).items()
        }
        self._connected = False
        self.call_log = []

    def connect(self):
        self._connected = True
        self.call_log.append(("connect",))

    def disconnect(self):
        self._connected = False
        self.call_log.append(("disconnect",))

    @property
    def is_connected(self): return self._connected

    def configure_pin(self, pin, mode):
        mode = mode.upper()
        if mode not in ("INPUT", "OUTPUT"):
            raise ValueError(f"mode must be 'INPUT' or 'OUTPUT', got '{mode}'")
        self._modes[pin] = mode
        if pin not in self._states:
            self._states[pin] = False
        self.call_log.append(("configure_pin", pin, mode))

    def read_pin(self, pin):
        self.call_log.append(("read_pin", pin))
        if pin in self._scripted and self._scripted[pin]:
            return self._scripted[pin].popleft()
        return self._states.get(pin, False)

    def write_pin(self, pin, state):
        self.call_log.append(("write_pin", pin, state))
        self._states[pin] = state

    def set_state(self, pin, state):
        """Directly set a pin state (simulates external toggle event)."""
        self._states[pin] = state

    def inject_sequence(self, pin, sequence):
        """Queue a sequence of states for scripted reads."""
        self._scripted[pin] = deque(sequence)

    def get_write_history(self, pin):
        """Return all states written to a specific pin."""
        return [
            args[1] for name, *args in self.call_log
            if name == "write_pin" and args[0] == pin
        ]

    def reset(self):
        self._states.clear()
        self._modes.clear()
        self._scripted.clear()
        self.call_log.clear()

    def __repr__(self):
        return f"MockBackend(states={self._states}, connected={self._connected})"