import cv2

from vision_core.oak_v2 import OakV2

def main():
    cap = OakV2()
    cap.start()
    scale = 0.5

    print("[TEST] Starting OAK V2 test...")

    try:
        while True:
            success, frame_data = cap.get_frame()
            frame = frame_data.bgr
            if success:
                frame = cv2.resize(frame, None, fx=scale, fy=scale)
                cv2.putText(frame,
                            f"FPS: {frame_data.fps:.2f}",
                            (50,460),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (255,255,255),
                            2,
                            cv2.LINE_AA)
                
                cv2.imshow("OAK V2", frame)

            key = cv2.waitKey(1)
            if key == ord("q"):
                break

    except KeyboardInterrupt:
        pass

    finally:
        print("[TEST] Releasing camera...")
        cap.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()