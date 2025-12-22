import cv2
import mediapipe as mp
import csv
import math
import os
import glob
from collections import deque
from collections import Counter
from event_manager import SuspiciousEventManager
from behavior_rules import BehaviorRules


SMOOTH_WINDOW = 7           # you can tune 5–15 frames
ALPHA = 0.5   # for exponential smoothing of numeric features
WARMUP_FRAMES = 5

BLINK_THRESHOLD = 7.5
MIN_BLINK_FRAMES = 2

blink_active = False
blink_frame_count = 0
total_blinks = 0

smooth_buffer = deque(maxlen=SMOOTH_WINDOW)
prev_hx = None
prev_eyelid = None

# --- Configuration ---
INPUT_FOLDER = "samples"
OUTPUT_FOLDER = "logs"

# Initialize MediaPipe
face_mesh = mp.solutions.face_mesh.FaceMesh(
    static_image_mode=False,
    refine_landmarks=True,
    max_num_faces=1,
    min_detection_confidence=0.5
)
# --- Math Helpers ---
def get_horizontal_pos(lm, w):
    # Iris and corners
    iris = lm[468]  # or use LM 473 for left eye
    left_corner = lm[33]
    right_corner = lm[133]

    iris_x = iris.x * w
    lx = left_corner.x * w
    rx = right_corner.x * w

    return (iris_x - lx) / (rx - lx)


def get_eyelid_opening(lm, h):
    """
    Measures vertical distance between top & bottom eyelids.
    Lower value means looking DOWN.
    """
    top = lm[159].y * h
    bottom = lm[145].y * h

    return abs(bottom - top)

def classify_gaze_from_coordinates(hx, eyelid):

        # ----- 1. Horizontal FIRST -----
    if hx < 0.44:  # adjust when we see your RIGHT data
        return "RIGHT"

    if hx > 0.56:  # from your LEFT dataset: hx > 0.588–0.620
        return "LEFT"

        # ----- 2. Vertical SECOND (only when horizontal is CENTER) -----
    if eyelid < 12.0:
        return "DOWN"

    if eyelid > 14.0:
        return "UP"

        # ----- 3. If no threshold breaks -----
    return "CENTER"


#----Main Processing Loop----

def analyze_single_video(video_path, output_folder=OUTPUT_FOLDER):


    filename = os.path.basename(video_path)
    print(f"Processing: {filename}...")

    event_manager = SuspiciousEventManager()

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0: fps = 30.0


    behavior = BehaviorRules(fps, event_manager)

    csv_name = filename.replace(".mp4", ".csv")
    csv_path = os.path.join(OUTPUT_FOLDER, csv_name)

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        # Added 'Vert_Ratio' to columns
        writer.writerow(["Timestamp", "Frame", "Raw_gaze", "Smooth_gaze", "Horiz_Pos", "Vert_Pos", "Warmup_Frames"])

        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break

            frame = cv2.flip(frame, 1)

            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb)


            if results.multi_face_landmarks:
                lm = results.multi_face_landmarks[0].landmark

                # Calculate both ratios
                # New coordinate-based gaze extraction
                hx = get_horizontal_pos(lm, w)
                eyelid = get_eyelid_opening(lm, h)



                if eyelid < BLINK_THRESHOLD:
                    blink_frame_count += 1

                    if not blink_active and blink_frame_count >= MIN_BLINK_FRAMES:
                        blink_active = True
                else:
                    if blink_active:
                        total_blinks += 1
                        print(f"Blink detected at frame {frame_count}")
                    blink_active = False
                    blink_frame_count = 0

                blink_flag = "BLINK" if blink_active else "NONE"

                # 1. Raw prediction
                if prev_hx is None:
                    prev_hx = hx
                    prev_eyelid = eyelid
                else:
                    prev_hx = ALPHA * hx + (1 - ALPHA) * prev_hx
                    prev_eyelid = ALPHA * eyelid + (1 - ALPHA) * prev_eyelid


                raw_gaze = classify_gaze_from_coordinates(prev_hx, prev_eyelid)
                # prefill on very first frame to avoid initial flicker:
                smooth_buffer.append(raw_gaze)

                smooth_gaze = Counter(smooth_buffer).most_common(1)[0][0]


            else:
                gaze = "CENTER"
                hx, eyelid = 0.5, 0.5

            # Calculate Timestamp
            video_time = frame_count / fps


            behavior.update(smooth_gaze, video_time)

            if frame_count < WARMUP_FRAMES:
                writer.writerow([f"{video_time:.3f}", frame_count, "WARMUP", "WARMUP", f"{prev_hx:.3f}", f"{prev_eyelid:.3f}",blink_flag])
            else:
                writer.writerow([f"{video_time:.3f}", frame_count, raw_gaze, smooth_gaze, f"{prev_hx:.3f}", f"{prev_eyelid:.3f}", blink_flag])

            frame_count += 1

    cap.release()
    print(f" -> Completed. Saved {csv_name}")
    event_manager.save("suspicious_events.json")

    cv2.destroyAllWindows()
    print("All files processed.")
    behavior.finalize()
    return event_manager.events

if __name__ == "__main__":
    video_files = glob.glob(os.path.join(INPUT_FOLDER, "*.mp4"))

    for video in video_files:
        events = analyze_single_video(video)
        print(f"{video}: {len(events)} events")




