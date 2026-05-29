from .toggle import Toggle, ToggleEvent
from .logger import ToggleLogger, setup_logging
from .backends.arduino import ArduinoBackend
from .backends.mock import MockBackend

try:
    from .backends.raspberry_pi import RaspberryPiBackend
except ImportError:
    pass

from .pytest_plugin import (
    assert_state,
    assert_changed,
    assert_at_least_n_changes,
    assert_no_bounce,
    assert_transition,
    assert_reached_state,
)

__version__ = "1.0.0"
__all__ = [
    "Toggle",
    "ToggleEvent",
    "ToggleLogger",
    "setup_logging",
    "ArduinoBackend",
    "MockBackend",
    "RaspberryPiBackend",
    "assert_state",
    "assert_changed",
    "assert_at_least_n_changes",
    "assert_no_bounce",
    "assert_transition",
    "assert_reached_state",
]