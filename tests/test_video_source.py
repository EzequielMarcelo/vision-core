import cv2
import time
from vision_core.video_source import VideoSource

def main():
    cap = VideoSource(camera_id=0, 
                      desired_fps=10)
    cap.start()
    
    fps = 0

    try:
        while True:
            success, frame_data = cap.get_frame()

            if not success:
                continue

            frame = frame_data.bgr
            fps = frame_data.fps

            cv2.putText(frame, 
                        f"FPS: {fps:.2f}", 
                        (50, 460), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        1, 
                        (255, 255, 255), 
                        2, 
                        cv2.LINE_AA)

            cv2.imshow("Video Test", frame)
            key = cv2.waitKey(1)

            if key == ord("q"):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()