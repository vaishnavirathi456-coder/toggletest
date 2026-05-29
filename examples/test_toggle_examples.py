"""
Example pytest tests — run without hardware using MockBackend.

    pytest examples/test_toggle_examples.py --no-hardware -v
"""

pytest_plugins = ["toggletest.pytest_plugin"]

from toggletest import (
    Toggle, MockBackend,
    assert_state, assert_changed, assert_no_bounce,
    assert_transition, assert_reached_state,
)


class TestToggleBasics:

    def test_initial_state_is_low(self, mock_toggle):
        assert_state(mock_toggle, False, "initial state should be LOW")

    def test_mock_set_state_high(self, mock_toggle, mock_backend):
        mock_backend.set_state(mock_toggle.pin, True)
        assert_state(mock_toggle, True)

    def test_no_changes_when_stable(self, mock_toggle):
        for _ in range(10):
            mock_toggle.read()
        assert_changed(mock_toggle, 0)

    def test_change_recorded_on_transition(self, mock_toggle, mock_backend):
        mock_backend.set_state(mock_toggle.pin, True)
        mock_toggle.read()
        assert_changed(mock_toggle, 1)

    def test_two_transitions_recorded(self, mock_toggle, mock_backend):
        mock_backend.set_state(mock_toggle.pin, True)
        mock_toggle.read()
        mock_backend.set_state(mock_toggle.pin, False)
        mock_toggle.read()
        assert_changed(mock_toggle, 2)


import pytest

@pytest.mark.parametrize("mock_toggle", [{"mode": "OUTPUT", "pin": 3}], indirect=True)
class TestToggleOutput:

    def test_write_high(self, mock_toggle, mock_backend):
        mock_toggle.write(True)
        assert mock_backend.read_pin(3) is True

    def test_write_low(self, mock_toggle, mock_backend):
        mock_toggle.write(True)
        mock_toggle.write(False)
        assert mock_backend.read_pin(3) is False

    def test_toggle_flips_state(self, mock_toggle):
        mock_toggle.write(False)
        assert mock_toggle.toggle() is True

    def test_pulse_returns_to_low(self, mock_toggle, mock_backend):
        mock_toggle.pulse(duration_ms=10)
        assert mock_backend.read_pin(3) is False

    def test_write_history_tracked(self, mock_toggle, mock_backend):
        mock_toggle.write(True)
        mock_toggle.write(False)
        mock_toggle.write(True)
        assert mock_backend.get_write_history(3) == [True, False, True]


class TestDebounce:

    def test_bounce_suppressed(self):
        backend = MockBackend(
            initial_states={2: False},
            scripted_reads={2: [True, False, True, True, True]},
        )
        backend.connect()
        t = Toggle(backend, pin=2, mode="INPUT", debounce_ms=50, label="bouncy")
        for _ in range(5):
            t.read()
        assert t.change_count <= 2
        backend.disconnect()


class TestTransitions:

    def test_low_to_high(self, mock_toggle, mock_backend):
        mock_backend.set_state(mock_toggle.pin, True)
        mock_toggle.read()
        assert_transition(mock_toggle, from_state=False, to_state=True)

    def test_missing_transition_raises(self, mock_toggle):
        import pytest
        with pytest.raises(AssertionError):
            assert_transition(mock_toggle, from_state=False, to_state=True)


class TestToggleLogger:

    def test_logger_captures_events(self, mock_toggle, mock_backend, toggle_logger):
        toggle_logger.attach(mock_toggle)
        mock_backend.set_state(mock_toggle.pin, True)
        mock_toggle.read()
        mock_backend.set_state(mock_toggle.pin, False)
        mock_toggle.read()
        assert toggle_logger.event_count == 2

    def test_csv_export(self, mock_toggle, mock_backend, toggle_logger, tmp_path):
        toggle_logger.attach(mock_toggle)
        mock_backend.set_state(mock_toggle.pin, True)
        mock_toggle.read()
        csv_path = tmp_path / "events.csv"
        toggle_logger.to_csv(csv_path)
        assert csv_path.exists()
        assert "state_label" in csv_path.read_text()


@pytest.mark.hardware
@pytest.mark.arduino
class TestArduinoHardware:
    """Requires Arduino with toggle_bridge.ino uploaded.
    Run: pytest --arduino-port /dev/ttyUSB0 --toggle-pin 2
    """

    def test_ping(self, arduino_toggle):
        assert arduino_toggle is not None

    def test_read_returns_bool(self, arduino_toggle):
        assert isinstance(arduino_toggle.read(), bool)