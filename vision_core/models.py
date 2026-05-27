from dataclasses import dataclass
from typing import Optional
import numpy as np

from . import utils as ut

@dataclass
class CameraFrame:
    bgr: Optional[np.ndarray] = None
    mono_l: Optional[np.ndarray] = None
    mono_r: Optional[np.ndarray] = None
    timestamp_us: Optional[int] = None
    fps: Optional[float] = None

    def copy(self) -> "CameraFrame":
        return CameraFrame(
            bgr=ut.safe_copy(self.bgr),
            mono_l=ut.safe_copy(self.mono_l),
            mono_r=ut.safe_copy(self.mono_r),
            timestamp_us=self.timestamp_us,
            fps=self.fps,
        )