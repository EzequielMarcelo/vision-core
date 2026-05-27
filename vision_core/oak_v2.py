from queue import Queue, Empty, Full
from threading import Thread, Event
from enum import Enum, auto
import time
import depthai as dai

from .source_base import SourceBase
from .models import CameraFrame

class OakV2(SourceBase):
    class CAMERA_STATE(Enum):
        SETUP = auto()
        CONNECT = auto()
        LOOP = auto()
        OFFLINE = auto()

    def __init__(self):
        self._is_running = False
        self._is_connected = False
        self._boot_time_sec = 30
        self._desired_fps = 10
        self._frame_time = 1 / self._desired_fps
        self._fps = 0
        self._time_last_fps_calc = time.monotonic()
        self._frame_count = 0

        self.device = None
        self.q_color_image_stream: dai.DataOutputQueue = None

        self._current_camera_state = self.CAMERA_STATE.SETUP

        self._queue = Queue(maxsize=2)
        self._kill_event = Event()
        self._thread: Thread = None

    def start(self):
        self._is_running = True
        self._kill_event.clear()
        self._thread = Thread(target=self._reader, daemon=True)
        self._thread.start()
    
    def _inicialize(self):
        self.pipeline = dai.Pipeline()
        self._setupColorCamera()
    
    def _setupColorCamera(self):
        color_cam = self.pipeline.create(dai.node.ColorCamera)
        color_image_stream = self.pipeline.create(dai.node.XLinkOut)
        color_cam.setBoardSocket(dai.CameraBoardSocket.CAM_A)
        color_cam.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        color_cam.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
        color_cam.setFps(self._desired_fps)
        color_image_stream.setStreamName("colorImgStream")
        color_cam.video.link(color_image_stream.input)
    
    def _reader(self):
        while self._is_running:  
            match self._current_camera_state:                    
                case self.CAMERA_STATE.SETUP:
                    self._is_connected = False
                    self._inicialize()
                    self._current_camera_state = self.CAMERA_STATE.CONNECT
                
                case self.CAMERA_STATE.CONNECT:
                    if self._connect():
                        self._current_camera_state = self.CAMERA_STATE.LOOP   

                case self.CAMERA_STATE.LOOP:
                    if not self._loop():
                        self._current_camera_state = self.CAMERA_STATE.CONNECT

                    
    def _connect(self) -> bool:
        try:
            self.device = dai.Device(self.pipeline)
            self._is_connected = True
            self.q_color_image_stream = self.device.getOutputQueue(name="colorImgStream", blocking=False, maxSize=1)
            print("[OAK V2] Camera connection sucessfull.")                    
            print(f"Name:, {self.device.getDeviceName()}")
            print(f"MxID:, {self.device.getDeviceInfo().getMxId()}")
            print(f"Connected cameras:, {self.device.getConnectedCameras()}")         
            return True

        except Exception as e:
            print(f"[OAK V2] Connection error: {e}.")
            print(f"[OAK V2] Waiting reboot time {self._boot_time_sec} sec before retrying connection with camera...")
              
            if self.device is not None:
                self.device.close()

            self._is_connected = False
            self._kill_event.wait(self._boot_time_sec)
            return False
        
    def _loop(self) -> bool:
        try:
            bgr_frame = None
            bgr_timestamp = 0
            start = time.monotonic()

            if self.q_color_image_stream is not None:
                inImg: dai.ImgFrame = self.q_color_image_stream.get()
                bgr_frame = inImg.getCvFrame()
                bgr_timestamp = int(inImg.getTimestampDevice().total_seconds() * 1_000_000)
            
            self._frame_count += 1

            now = time.monotonic()
            delta_time = now - self._time_last_fps_calc

            if delta_time >= 1.0:
                self._fps = self._frame_count / delta_time
                self._time_last_fps_calc = now
                self._frame_count = 0
        
            out_frame = CameraFrame(bgr=bgr_frame,
                                    timestamp_us=bgr_timestamp,
                                    fps=self._fps)
            
            self._put(out_frame)
            elapsed = time.monotonic() - start
            remaining = self._frame_time - elapsed

            if remaining > 0:
                time.sleep(remaining)
            return True
        except Exception as e:
            self._is_connected = False
            
            if self.device is not None:
                self.device.close()
            
            print(f"[OAK V2] Loop error: {e}.")
            return False

    def _put(self, out_frame: CameraFrame):
        try:
            self._queue.put(out_frame, timeout=0.01)
        except Full:
            self._queue.get(timeout=0.01)
            self._queue.put(out_frame, timeout=0.01)

    def get_frame(self) -> tuple[bool, CameraFrame]:
        try:
            frame = self._queue.get(timeout=0.01)
            return True, frame
        except Empty:
            return False, CameraFrame()       

    def stop(self):
        self._is_running = False
        if self.device is not None:
            self.device.close()

        if self._thread is not None:
            self._kill_event.set()
            self._thread.join(timeout=1)
    