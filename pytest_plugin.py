import time
import logging
from typing import Optional

try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

from .toggle import Toggle, ToggleEvent
from .logger import ToggleLogger


if PYTEST_AVAILABLE:

    def pytest_configure(config):
        config.addinivalue_line("markers", "hardware: requires real hardware")
        config.addinivalue_line("markers", "arduino: requires Arduino connection")

    def pytest_addoption(parser):
        parser.addoption("--no-hardware", action="store_true", default=False)
        parser.addoption("--arduino-port", default=None)
        parser.addoption("--toggle-pin", type=int, default=2)

    def pytest_collection_modifyitems(config, items):
        if config.getoption("--no-hardware"):
            skip = pytest.mark.skip(reason="--no-hardware flag set")
            for item in items:
                if "hardware" in item.keywords or "arduino" in item.keywords:
                    item.add_marker(skip)

    @pytest.fixture
    def mock_backend():
        from .backends.mock import MockBackend
        backend = MockBackend()
        backend.connect()
        yield backend
        backend.disconnect()

    @pytest.fixture
    def mock_toggle(request, mock_backend):
        params = getattr(request, "param", {})
        toggle = Toggle(
            backend=mock_backend,
            pin=params.get("pin", 2),
            mode=params.get("mode", "INPUT"),
            debounce_ms=params.get("debounce_ms", 50.0),
            label=params.get("label", "mock_toggle"),
        )
        yield toggle

    @pytest.fixture
    def toggle_logger(request):
        tlog = ToggleLogger(session_name=request.node.name)
        yield tlog
        if request.session.testsfailed:
            tlog.print_report()

    @pytest.fixture
    def arduino_toggle(request):
        pytest.importorskip("serial", reason="pyserial not installed")
        from .backends.arduino import ArduinoBackend
        port = request.config.getoption("--arduino-port")
        pin = request.config.getoption("--toggle-pin")
        params = getattr(request, "param", {})
        backend = ArduinoBackend(port=port)
        backend.connect()
        toggle = Toggle(backend=backend, pin=pin,
                        mode=params.get("mode", "INPUT"), label="arduino_toggle")
        yield toggle
        backend.disconnect()


# ------------------------------------------------------------------
# Assertion helpers — work with or without pytest
# ------------------------------------------------------------------

def assert_state(toggle, expected, msg=""):
    actual = toggle.read()
    label = "HIGH" if expected else "LOW"
    assert actual == expected, (
        f"[{toggle.label}] Expected {label}, got {'HIGH' if actual else 'LOW'}. {msg}"
    )

def assert_changed(toggle, times, msg=""):
    actual = toggle.change_count
    assert actual == times, (
        f"[{toggle.label}] Expected {times} change(s), recorded {actual}. {msg}"
    )

def assert_at_least_n_changes(toggle, n, msg=""):
    actual = toggle.change_count
    assert actual >= n, (
        f"[{toggle.label}] Expected >= {n} changes, recorded {actual}. {msg}"
    )

def assert_no_bounce(toggle, window_ms=50.0, msg=""):
    events = toggle.history
    window_s = window_ms / 1000.0
    for i in range(1, len(events)):
        gap = events[i].timestamp - events[i - 1].timestamp
        assert gap >= window_s, (
            f"[{toggle.label}] Bounce detected: {gap*1000:.2f}ms apart "
            f"(window={window_ms}ms). {msg}"
        )

def assert_transition(toggle, from_state, to_state, msg=""):
    events = toggle.history
    from_label = "HIGH" if from_state else "LOW"
    to_label = "HIGH" if to_state else "LOW"
    for i in range(1, len(events)):
        if events[i-1].state == from_state and events[i].state == to_state:
            return
    raise AssertionError(
        f"[{toggle.label}] Transition {from_label}→{to_label} not found "
        f"in {toggle.change_count} recorded events. {msg}"
    )

def assert_reached_state(toggle, target, timeout=5.0, poll_hz=100.0, msg=""):
    reached = toggle.wait_for_state(target, timeout=timeout, poll_hz=poll_hz)
    label = "HIGH" if target else "LOW"
    assert reached, (
        f"[{toggle.label}] Did not reach {label} within {timeout}s. {msg}"
    )