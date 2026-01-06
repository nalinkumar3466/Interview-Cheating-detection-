import cv2
import mediapipe as mp
import math
import csv
import time
import os


# --- 1. CONFIGURATION (Adjust these for your specific test) ---
# Set to 0 for Webcam, or a filename string like 'reading_sample.mp4'
VIDEO_SOURCE = 0
OUTPUT_LOG_FILE = "gaze_logs.csv"

# --- 2. SETUP MEDIAPIPE (Using logic from eyecont.py) ---
mp_face_mesh = mp.solutions.face_mesh
# refine_landmarks=True is ESSENTIAL for Iris points (from eyecont.py)
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# --- 3. LANDMARK INDICES ---
# Eye corners (from new eye contolled mouse.py)
RIGHT_EYE_CORNERS = [33, 133]  # [Right, Left] (in image coordinates)
LEFT_EYE_CORNERS = [362, 263]
RIGHT_EYE_VERTICAL = [159, 145] # Top, Bottom
LEFT_EYE_VERTICAL = [386, 374]

# Iris Centers (Specific to refine_landmarks=True)
RIGHT_IRIS = 468
LEFT_IRIS = 473


# --- 4. MATH HELPER FUNCTIONS (From new eye contolled mouse.py) ---
def euclidean_distance(p1, p2):
    # Calculates distance between two points (x, y)
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def get_gaze_ratio(eye_points, iris_point, landmarks, frame_w, frame_h):
    """
    Calculates the horizontal position of the iris relative to eye corners.
    Returns a value between 0.0 (Looking Left) and 1.0 (Looking Right).
    """
    # Get coordinates of eye corners
    corner_1 = landmarks[eye_points[0]]
    corner_2 = landmarks[eye_points[1]]
    iris = landmarks[iris_point]

    # Convert to pixel coordinates
    p1 = (int(corner_1.x * frame_w), int(corner_1.y * frame_h))
    p2 = (int(corner_2.x * frame_w), int(corner_2.y * frame_h))
    p_iris = (int(iris.x * frame_w), int(iris.y * frame_h))

    # Calculate total eye width
    eye_width = euclidean_distance(p1, p2)

    # Calculate distance from the 'left' corner (screen left) to iris
    # Note: We use the point with smaller X as the left reference
    left_most_point = p1 if p1[0] < p2[0] else p2
    dist_to_iris = euclidean_distance(left_most_point, p_iris)

    if eye_width == 0:
        return 0.5  # Safety for closed eyes/errors

    ratio = dist_to_iris / eye_width
    return ratio

def get_vertical_ratio(lm, top_idx, bottom_idx, iris_idx, w, h):
    # Extract points
    top = lm[top_idx]
    bottom = lm[bottom_idx]
    iris = lm[iris_idx]

    # Calculate vertical distance (Y-axis only is usually sufficient, but hypot is safer)
    # Total eye opening height
    eye_height = math.hypot((top.x - bottom.x) * w, (top.y - bottom.y) * h)

    # Distance from Top Eyelid to Iris
    dist_to_iris = math.hypot((top.x - iris.x) * w, (top.y - iris.y) * h)

    # Avoid division by zero (if eye is closed/blinking)
    if eye_height < 4.0:  # Threshold in pixels
        return 0.5  # Default to center

    return dist_to_iris / eye_height


# --- 5. MAIN EXECUTION LOOP ---
cap = cv2.VideoCapture(VIDEO_SOURCE)

# Prepare CSV file
with open(OUTPUT_LOG_FILE, mode='w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Timestamp', 'Frame', 'Gaze_Direction', 'Gaze_Ratio'])

    print(f"Starting Collection... Press ESC to quit.")
    start_time = time.time()
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)  # Mirror frame for easier self-testing
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)

        gaze_dir = "Not Detected"
        avg_ratio = 0.5

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark

            # 1. Calculate Ratio for Both Eyes
            ratio_r = get_gaze_ratio(RIGHT_EYE_CORNERS, RIGHT_IRIS, landmarks, w, h)
            ratio_l = get_gaze_ratio(LEFT_EYE_CORNERS, LEFT_IRIS, landmarks, w, h)
            r_vert = get_vertical_ratio(landmarks, 159, 145, 468, w, h)
            l_vert = get_vertical_ratio(landmarks, 386, 374, 473, w, h)

            # 2. Average them for stability
            avg_ratio = (ratio_r + ratio_l) / 2
            avg_vert_ratio = (r_vert + l_vert) / 2

            # 3. Determine Direction (The "Kashvi" Classification)
            # Thresholds: < 0.42 is Left, > 0.58 is Right (Adjust based on testing)
            if avg_ratio < 0.42:
                gaze_dir = "LEFT"
            elif avg_ratio > 0.58:
                gaze_dir = "RIGHT"
            else:
                gaze_dir = "CENTER"
            if avg_vert_ratio < 0.45:  # Thresholds need tuning per user
                vertical_gaze = "UP"
            elif avg_vert_ratio > 0.55:
                vertical_gaze = "DOWN"
            else:
                vertical_gaze = "CENTER"

            # 4. Visualization (Drawing Iris)
            p_iris_r = (int(landmarks[RIGHT_IRIS].x * w), int(landmarks[RIGHT_IRIS].y * h))
            p_iris_l = (int(landmarks[LEFT_IRIS].x * w), int(landmarks[LEFT_IRIS].y * h))
            cv2.circle(frame, p_iris_r, 3, (0, 255, 0), -1)
            cv2.circle(frame, p_iris_l, 3, (0, 255, 0), -1)

        # Log Data
        timestamp = time.time() - start_time
        writer.writerow([f"{timestamp:.2f}", frame_count, gaze_dir, f"{avg_ratio:.3f}"])

        # Display GUI
        cv2.putText(frame, f"Gaze: {gaze_dir}", (30, 50), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 255), 2)
        cv2.putText(frame, f"Ratio: {avg_ratio:.2f}", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

        cv2.imshow("Berribot Gaze Collector", frame)
        frame_count += 1

        # Exit
        if cv2.waitKey(1) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()
print(f"Data saved to {OUTPUT_LOG_FILE}")