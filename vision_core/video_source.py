import cv2
from queue import Queue, Empty, Full
from threading import Thread
import time

from .source_base import SourceBase
from .models import CameraFrame

class VideoSource(SourceBase):
    def __init__(self, 
                 camera_id=0, 
                 desired_fps=30):
        self._camera_id = camera_id
        self._desired_fps = desired_fps
        self._cap = None
        self._queue = Queue(maxsize=2)

        self._is_running = False
        self._thread: Thread = None        
    
    def start(self):
        self._cap = cv2.VideoCapture(self._camera_id)
        if not self._cap.isOpened():
            raise RuntimeError(
                f"Failed to connect to the camera: {self._camera_id}"
            )
        
        self._is_running = True
        self._thread = Thread(target=self._reader, daemon=True)
        self._thread.start()

    def _reader(self):
        fps = 0
        prev = time.monotonic()
        frame_count = 0
        while self._is_running:
            success, bgr_frame = self._cap.read()

            if success:
                mono_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
                frame_count += 1

                now = time.monotonic()
                delta_time = now - prev

                if delta_time >= 1.0:
                    fps = frame_count / delta_time
                    prev = now
                    frame_count = 0

                data = CameraFrame(
                    bgr=bgr_frame,
                    mono_l=mono_frame,
                    mono_r=mono_frame,
                    fps=fps
                )
                

                if self._queue.full():
                    try:
                        self._queue.get_nowait()
                    except Empty:
                        pass

                try:
                    self._queue.put_nowait(data)
                except Full:
                    pass

    def get_frame(self) -> tuple[bool, CameraFrame]:
        try:
            frame = self._queue.get(timeout=0.01)
            return True, frame

        except Empty:
            return False, CameraFrame()       

    def stop(self):
        self._is_running = False
        if self._thread is not None:
            self._thread.join(timeout=1)
        
        if self._cap is not None:
            self._cap.release()
    
    
        