import cv2
import mediapipe as mp
import csv
import math
import os
import glob
from collections import deque
from collections import Counter


   # 7–frame smoothing

SMOOTH_WINDOW = 7           # you can tune 5–15 frames
ALPHA = 0.5   # for exponential smoothing of numeric features
WARMUP_FRAMES = 5


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

    # Horizontal thresholds
    if hx < 0.41:
        h_status = "RIGHT"
    elif hx > 0.58:
        h_status = "LEFT"
    else:
        h_status = "CENTER"

        # ---- Vertical from Eyelid Opening ----
        # Lower eyelid opening means looking down
    if eyelid < 12.0:  # tune based on your dataset
        v_status = "DOWN"
    elif eyelid > 14.0:
        v_status = "UP"
    else:
        v_status = "CENTER"

        # ---- Priority ----


    if v_status == "DOWN":
        return "DOWN"
        # 2. UP overrides LEFT/RIGHT/CENTER
    if h_status in ["LEFT", "RIGHT"]:
        return h_status

        # 3. Only if horizontal is CENTER check UP
    if h_status == "CENTER" and v_status == "UP":
        return "UP"


    return h_status


# --- Main Processing Loop ---
video_files = glob.glob(os.path.join(INPUT_FOLDER, "*.mp4"))

if not video_files:
    print(f"No videos found in '{INPUT_FOLDER}' folder!")

for video_path in video_files:
    filename = os.path.basename(video_path)
    print(f"Processing: {filename}...")

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0: fps = 30.0

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
                # 1. Raw prediction
                if prev_hx is None:
                    prev_hx = hx
                    prev_eyelid = eyelid
                else:
                    prev_hx = ALPHA * hx + (1 - ALPHA) * prev_hx
                    prev_eyelid = ALPHA * eyelid + (1 - ALPHA) * prev_eyelid

                raw_gaze = classify_gaze_from_coordinates(prev_hx, prev_eyelid)
                # prefill on very first frame to avoid initial flicker:
                if len(smooth_buffer) == 0:
                    smooth_buffer.extend([raw_gaze] * SMOOTH_WINDOW)
                else:
                    smooth_buffer.append(raw_gaze)

                smooth_gaze = Counter(smooth_buffer).most_common(1)[0][0]

                # optionally skip warmup frames for logging/metrics:

                # 2. Add to smoothing buffer
               # smooth_buffer.append(raw_gaze)

                # 3. Smoothed prediction = most common gaze in last N frames
                #from statistics import mode

               # try:
                    #gaze = mode(smooth_buffer)
                #except:
                    #gaze = raw_gaze  # first few frames, buffer not filled yet




            else:
                gaze = "CENTER"
                hx, eyelid = 0.5, 0.5

                # --- CLASSIFICATION LOGIC ---
                # Priority: Check Down first, then Left/Right
                # --- STEP 1: Check Vertical INDEPENDENTLY ---
                # Note: You MUST tune this 0.51 value.
                # If your CSV says "Center" is 0.49, set this to 0.51.




            # Calculate Timestamp
            video_time = frame_count / fps
            if frame_count < WARMUP_FRAMES:
                writer.writerow([f"{video_time:.3f}", frame_count, "WARMUP", "WARMUP", f"{prev_hx:.3f}", f"{prev_eyelid:.3f}"])
            else:
                writer.writerow([f"{video_time:.3f}", frame_count, raw_gaze, smooth_gaze, f"{prev_hx:.3f}", f"{prev_eyelid:.3f}"])
            #writer.writerow([
                #f"{video_time:.3f}",
                #frame_count,
                #raw_gaze,
                #smooth_gaze,
                #f"{hx:.3f}",
                #f"{eyelid:.3f}"
            #])

            frame_count += 1

    cap.release()
    print(f" -> Completed. Saved {csv_name}")

cv2.destroyAllWindows()
print("All files processed.")