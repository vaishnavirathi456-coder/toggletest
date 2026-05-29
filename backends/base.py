from abc import ABC, abstractmethod
from typing import Optional


class HardwareBackend(ABC):
    """Abstract base class all hardware backends must implement."""

    @abstractmethod
    def connect(self) -> None:
        """Open connection to hardware."""

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection and release hardware resources."""

    @abstractmethod
    def read_pin(self, pin: int) -> bool:
        """Read digital state of a pin. Returns True=HIGH, False=LOW."""

    @abstractmethod
    def write_pin(self, pin: int, state: bool) -> None:
        """Drive a pin HIGH (True) or LOW (False)."""

    @abstractmethod
    def configure_pin(self, pin: int, mode: str) -> None:
        """Set pin direction — 'INPUT' or 'OUTPUT'."""

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.disconnect()

    @property
    def is_connected(self) -> bool:
        return False