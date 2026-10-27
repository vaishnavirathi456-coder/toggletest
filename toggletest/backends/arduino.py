import time
from typing import Optional

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

from .base import HardwareBackend


class ArduinoBackend(HardwareBackend):
    """
    Hardware backend for Arduino boards connected via USB-serial.

    Parameters
    ----------
    port : str
        Serial port (e.g. '/dev/ttyUSB0', 'COM3').
        Pass None to auto-detect the first available Arduino.
    baud_rate : int
        Must match the baud rate in your Arduino sketch (default 9600).
    timeout : float
        Serial read timeout in seconds.
    """

    def __init__(self, port=None, baud_rate=9600, timeout=2.0):
        if not SERIAL_AVAILABLE:
            raise ImportError(
                "pyserial is required for ArduinoBackend. "
                "Install it with: pip install pyserial"
            )
        self._port = port or self._auto_detect_port()
        self._baud_rate = baud_rate
        self._timeout = timeout
        self._serial = None

    def connect(self):
        self._serial = serial.Serial(
            port=self._port,
            baudrate=self._baud_rate,
            timeout=self._timeout,
        )
        time.sleep(2.0)
        self._serial.reset_input_buffer()
        self._ping()

    def disconnect(self):
        if self._serial and self._serial.is_open:
            self._serial.close()
        self._serial = None

    @property
    def is_connected(self):
        return self._serial is not None and self._serial.is_open

    def configure_pin(self, pin, mode):
        mode = mode.upper()
        if mode not in ("INPUT", "OUTPUT"):
            raise ValueError(f"mode must be 'INPUT' or 'OUTPUT', got '{mode}'")
        response = self._send_command(f"CONFIG:{pin}:{mode}")
        self._expect_ok(response, f"CONFIG:{pin}:{mode}")

    def read_pin(self, pin):
        self._assert_connected()
        response = self._send_command(f"READ:{pin}")
        if not response.startswith("STATE:"):
            raise RuntimeError(f"Unexpected response to READ:{pin} — got '{response}'")
        value = response.split(":")[1].strip()
        return value == "1"

    def write_pin(self, pin, state):
        self._assert_connected()
        value = 1 if state else 0
        response = self._send_command(f"WRITE:{pin}:{value}")
        self._expect_ok(response, f"WRITE:{pin}:{value}")

    def _send_command(self, command):
        self._assert_connected()
        self._serial.reset_input_buffer()
        self._serial.write(f"{command}\n".encode("ascii"))
        raw = self._serial.readline()
        return raw.decode("ascii", errors="replace").strip()

    def _ping(self):
        response = self._send_command("PING")
        if response != "PONG":
            raise ConnectionError(
                f"Arduino did not respond to PING (got '{response}'). "
                "Check that toggle_bridge.ino is uploaded."
            )

    def _expect_ok(self, response, command):
        if response != "OK":
            raise RuntimeError(f"Expected 'OK' for '{command}', got '{response}'")

    def _assert_connected(self):
        if not self.is_connected:
            raise ConnectionError(
                "ArduinoBackend is not connected. Call connect() first."
            )

    @staticmethod
    def _auto_detect_port():
        ports = serial.tools.list_ports.comports()
        arduino_keywords = ("Arduino", "CH340", "FTDI", "USB Serial")
        for port in ports:
            description = (port.description or "") + (port.manufacturer or "")
            if any(kw.lower() in description.lower() for kw in arduino_keywords):
                return port.device
        if ports:
            return ports[0].device
        raise RuntimeError(
            "No serial ports found. Connect your Arduino or pass port= explicitly."
        )

    def __repr__(self):
        status = "connected" if self.is_connected else "disconnected"
        return f"ArduinoBackend(port={self._port!r}, baud={self._baud_rate}, {status})"