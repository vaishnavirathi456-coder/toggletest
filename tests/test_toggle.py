import pytest
from toggletest import Toggle, MockBackend


def test_write_on_input_raises():
    with MockBackend() as hw:
        t = Toggle(hw, pin=2, mode="INPUT")
        with pytest.raises(RuntimeError):
            t.write(True)


def test_invalid_mode_raises():
    with MockBackend() as hw:
        with pytest.raises(ValueError):
            Toggle(hw, pin=2, mode="SIDEWAYS")


def test_context_manager_connects_and_disconnects():
    hw = MockBackend()
    with hw:
        assert hw.is_connected
    assert not hw.is_connected
    assert hw.call_log[0] == ("connect",)
    assert hw.call_log[-1] == ("disconnect",)


def test_scripted_reads_return_in_order():
    with MockBackend(scripted_reads={2: [True, False, True]}) as hw:
        assert [hw.read_pin(2) for _ in range(3)] == [True, False, True]


def test_write_history_for_output_pin():
    with MockBackend() as hw:
        t = Toggle(hw, pin=3, mode="OUTPUT")
        t.write(True)
        t.write(False)
        assert hw.get_write_history(3) == [True, False]


def test_change_count_ignores_init_event():
    with MockBackend(initial_states={2: False}) as hw:
        t = Toggle(hw, pin=2, mode="INPUT", debounce_ms=0)
        t.read()               # init event
        hw.set_state(2, True)
        t.read()               # real change
        assert t.change_count == 1