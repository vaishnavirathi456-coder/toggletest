# toggletest

Universal Python library for hardware toggle switch testing automation.

Supports Arduino (USB-serial), Raspberry Pi (GPIO), and a software Mock backend — all through the same API.

**Built by:** Vaishnavi Rathi | MS ECE @ Northeastern University

---

## Install

```bash
pip install toggletest              # core only (mock backend)
pip install toggletest[arduino]     # + pyserial for Arduino
pip install toggletest[rpi]         # + RPi.GPIO for Raspberry Pi
pip install toggletest[all]         # everything including pytest
```

## Arduino setup

Upload `examples/arduino_firmware/toggle_bridge.ino` to your Arduino before using `ArduinoBackend`.

---

## Quick start

### With Arduino (hardware)
```python
from toggletest import Toggle, ArduinoBackend

with ArduinoBackend(port='/dev/ttyUSB0') as hw:
    t = Toggle(hw, pin=2, mode='INPUT', debounce_ms=50, label='power_switch')
    events = t.monitor(duration=10.0, poll_hz=100)
    print(t.summary())
```

### With MockBackend (no hardware — great for CI)
```python
from toggletest import Toggle, MockBackend

with MockBackend(initial_states={2: False}) as hw:
    t = Toggle(hw, pin=2, mode='INPUT', debounce_ms=50)
    hw.set_state(2, True)   # simulate switch press
    print(t.read())         # True
    print(t.change_count)   # 1
```

### Driving an output toggle
```python
with ArduinoBackend() as hw:
    t = Toggle(hw, pin=3, mode='OUTPUT', label='relay')
    t.write(True)
    t.pulse(duration_ms=200)
    t.toggle()
```

---

## pytest integration

Add to `conftest.py`:
```python
pytest_plugins = ["toggletest.pytest_plugin"]
```

```python
from toggletest import assert_state, assert_changed, assert_no_bounce, assert_transition

def test_power_switch(mock_toggle, mock_backend, toggle_logger):
    toggle_logger.attach(mock_toggle)
    mock_backend.set_state(mock_toggle.pin, True)
    mock_toggle.read()
    assert_state(mock_toggle, True)
    assert_changed(mock_toggle, 1)
    assert_transition(mock_toggle, from_state=False, to_state=True)
    assert_no_bounce(mock_toggle, window_ms=50)
```

Run without hardware:
```bash
pytest --no-hardware
```

Run with Arduino:
```bash
pytest --arduino-port /dev/ttyUSB0 --toggle-pin 2
```

---

## CLI

```bash
toggletest scan
toggletest ping --port /dev/ttyUSB0
toggletest read --port /dev/ttyUSB0 --pin 2
toggletest write --port /dev/ttyUSB0 --pin 3 --state high
toggletest pulse --port /dev/ttyUSB0 --pin 3 --duration-ms 500
toggletest monitor --port /dev/ttyUSB0 --pin 2 --duration 10 --output results.csv
toggletest report  --port /dev/ttyUSB0 --pin 2 --duration 10 --output-csv run.csv
```

---

## Adding a new backend

```python
from toggletest.backends.base import HardwareBackend

class MyCustomBackend(HardwareBackend):
    def connect(self): ...
    def disconnect(self): ...
    def configure_pin(self, pin, mode): ...
    def read_pin(self, pin) -> bool: ...
    def write_pin(self, pin, state): ...
```

---

## Project structure
---

## License

MIT