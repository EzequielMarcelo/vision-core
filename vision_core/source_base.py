from abc import ABC, abstractmethod
from .models import CameraFrame

class SourceBase(ABC):
    def __init__(self):
        self._is_connected = False
        self._is_running = False

    @abstractmethod
    def start(self) -> None:
        """
        Start acquisition.
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """
        Stop acquisition.
        """
        pass

    @abstractmethod
    def get_frame(self) -> CameraFrame:
        """
        Return latest frame.
        """
        pass

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def is_running(self) -> bool:
        return self._is_running