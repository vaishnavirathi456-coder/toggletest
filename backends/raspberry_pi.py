from .base import HardwareBackend

try:
    import RPi.GPIO as GPIO
    RPI_AVAILABLE = True
except ImportError:
    RPI_AVAILABLE = False


class RaspberryPiBackend(HardwareBackend):
    """
    Hardware backend for Raspberry Pi using RPi.GPIO.

    Parameters
    ----------
    numbering : str
        'BCM' (GPIO numbers) or 'BOARD' (physical pin numbers).
    """

    def __init__(self, numbering="BCM"):
        if not RPI_AVAILABLE:
            raise ImportError(
                "RPi.GPIO is required. Install with: pip install RPi.GPIO"
            )
        self._numbering = numbering.upper()
        self._connected = False

    def connect(self):
        mode = GPIO.BCM if self._numbering == "BCM" else GPIO.BOARD
        GPIO.setmode(mode)
        GPIO.setwarnings(False)
        self._connected = True

    def disconnect(self):
        GPIO.cleanup()
        self._connected = False

    @property
    def is_connected(self): return self._connected

    def configure_pin(self, pin, mode):
        mode = mode.upper()
        if mode == "INPUT":
            GPIO.setup(pin, GPIO.IN)
        elif mode == "OUTPUT":
            GPIO.setup(pin, GPIO.OUT)
        else:
            raise ValueError(f"mode must be 'INPUT' or 'OUTPUT', got '{mode}'")

    def read_pin(self, pin): return bool(GPIO.input(pin))

    def write_pin(self, pin, state):
        GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)

    def __repr__(self):
        return f"RaspberryPiBackend(numbering={self._numbering!r})"