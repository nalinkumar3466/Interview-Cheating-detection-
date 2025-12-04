import cv2
import mediapipe as mp
import csv
import math
import os
import glob

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
def get_horizontal_ratio(lm, w, h):
    # Indices: Right[33, 133, 468], Left[362, 263, 473]
    def eye_ratio(p1_idx, p2_idx, iris_idx):
        p1, p2, iris = lm[p1_idx], lm[p2_idx], lm[iris_idx]
        eye_width = math.hypot((p1.x - p2.x) * w, (p1.y - p2.y) * h)
        dist_iris = math.hypot((p1.x - iris.x) * w, (p1.y - iris.y) * h)
        return dist_iris / eye_width if eye_width > 0 else 0.5

    r_ratio = eye_ratio(33, 133, 468)
    l_ratio = eye_ratio(362, 263, 473)
    return (r_ratio + l_ratio) / 2


def get_vertical_ratio(lm, w, h):
    # Eyelid distance for RIGHT eye
    top_r = lm[159]
    bot_r = lm[145]
    dist_r = math.hypot((top_r.x - bot_r.x) * w, (top_r.y - bot_r.y) * h)

    # Eyelid distance for LEFT eye
    top_l = lm[386]
    bot_l = lm[374]
    dist_l = math.hypot((top_l.x - bot_l.x) * w, (top_l.y - bot_l.y) * h)

    # Return average eyelid opening
    return (dist_r + dist_l) / 2


def classify_gaze(h_ratio, v_ratio):
    """
    Convert ratios into gaze direction (clean + modular version).
    """
    # Horizontal classification
    if h_ratio < 0.45:
        h_status = "RIGHT"
    elif h_ratio > 0.60:
        h_status = "LEFT"
    else:
        h_status = "CENTER"

    # Vertical classification
    eye_opening = get_vertical_ratio(lm, w, h)

    if eye_opening < 11.6:
        v_status = "DOWN"
    else:
        v_status = "CENTER"

    # Priority: Down gaze overrides horizontal
    if v_status == "DOWN":
        return "DOWN"

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
        writer.writerow(["Timestamp", "Frame", "Direction", "Horiz_Ratio", "Vert_Ratio"])

        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break

            frame = cv2.flip(frame, 1)

            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb)

            gaze = "CENTER"
            h_ratio = 0.5
            v_ratio = 0.5

            if results.multi_face_landmarks:
                lm = results.multi_face_landmarks[0].landmark

                # Calculate both ratios
                h_ratio = get_horizontal_ratio(lm, w, h)
                v_ratio = get_vertical_ratio(lm, w, h)
                gaze = classify_gaze(h_ratio, v_ratio)

                # --- CLASSIFICATION LOGIC ---
                # Priority: Check Down first, then Left/Right
                # --- STEP 1: Check Vertical INDEPENDENTLY ---
                # Note: You MUST tune this 0.51 value.
                # If your CSV says "Center" is 0.49, set this to 0.51.




            # Calculate Timestamp
            video_time = frame_count / fps

            writer.writerow([f"{video_time:.3f}", frame_count, gaze, f"{h_ratio:.3f}", f"{v_ratio:.3f}"])
            frame_count += 1

    cap.release()
    print(f" -> Completed. Saved {csv_name}")

cv2.destroyAllWindows()
print("All files processed.")




