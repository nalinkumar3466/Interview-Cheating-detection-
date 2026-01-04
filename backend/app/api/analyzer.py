import cv2
import mediapipe as mp
import math

mp_face_mesh = mp.solutions.face_mesh

# helper math

def euclidean(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _get_horizontal_ratio(lm, w, h):
    # indices: RIGHT eye corners 33,133 iris 468 | LEFT 362,263 iris 473
    def eye_ratio(p1_idx, p2_idx, iris_idx):
        p1, p2, iris = lm[p1_idx], lm[p2_idx], lm[iris_idx]
        p1p = (p1.x * w, p1.y * h)
        p2p = (p2.x * w, p2.y * h)
        irp = (iris.x * w, iris.y * h)
        eye_w = euclidean(p1p, p2p)
        if eye_w == 0:
            return 0.5
        return euclidean(p1p, irp) / eye_w

    r = eye_ratio(33, 133, 468)
    l = eye_ratio(362, 263, 473)
    return (r + l) / 2


def _get_vertical_ratio(lm, w, h):
    top_r = lm[159]
    bot_r = lm[145]
    top_l = lm[386]
    bot_l = lm[374]
    dr = euclidean((top_r.x * w, top_r.y * h), (bot_r.x * w, bot_r.y * h))
    dl = euclidean((top_l.x * w, top_l.y * h), (bot_l.x * w, bot_l.y * h))
    return (dr + dl) / 2


def _classify(h_ratio, v_ratio, horiz_left_thresh=0.42, horiz_right_thresh=0.58, vert_down_thresh=0.45):
    if v_ratio is not None and v_ratio < vert_down_thresh:
        return "DOWN"
    if h_ratio < horiz_left_thresh:
        return "LEFT"
    if h_ratio > horiz_right_thresh:
        return "RIGHT"
    return "CENTER"


def analyze_video(video_path: str, min_event_seconds: float = 0.6):
    """Analyze a video file and return an analysis dict:
    {recording_path, duration, events: [{timestamp, label}, ...]}

    This is a lightweight analyzer using MediaPipe FaceMesh to estimate gaze.
    """
    events = []
    try:
        face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, refine_landmarks=True, max_num_faces=1,
                                          min_detection_confidence=0.4, min_tracking_confidence=0.4)
    except Exception as e:
        raise RuntimeError("Failed to initialize MediaPipe FaceMesh: %s" % e)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("Unable to open video: %s" % video_path)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = frames / fps if fps and frames else None

    current_label = None
    label_start_time = None

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        label = "UNKNOWN"
        h_ratio = None
        v_ratio = None
        if results.multi_face_landmarks:
            lm = results.multi_face_landmarks[0].landmark
            try:
                h_ratio = _get_horizontal_ratio(lm, w, h)
                v_ratio = _get_vertical_ratio(lm, w, h)
                label = _classify(h_ratio, v_ratio)
            except Exception:
                label = "UNKNOWN"
        else:
            label = "NO_FACE"

        timestamp = frame_idx / fps if fps else 0.0

        # event detection: when label deviates from CENTER for > min_event_seconds create event
        is_suspicious = label not in ("CENTER", "UNKNOWN")
        if is_suspicious:
            if current_label is None:
                # start of suspicious
                current_label = label
                label_start_time = timestamp
            elif label != current_label:
                # label changed; check duration of previous
                if label_start_time is not None and (timestamp - label_start_time) >= min_event_seconds:
                    events.append({"timestamp": round(label_start_time, 2), "label": current_label})
                # start new
                current_label = label
                label_start_time = timestamp
        else:
            # if currently in suspicious, check and close
            if current_label is not None and label_start_time is not None:
                if (timestamp - label_start_time) >= min_event_seconds:
                    events.append({"timestamp": round(label_start_time, 2), "label": current_label})
            current_label = None
            label_start_time = None

        frame_idx += 1

    # final flush
    if current_label is not None and label_start_time is not None and duration and (duration - label_start_time) >= min_event_seconds:
        events.append({"timestamp": round(label_start_time, 2), "label": current_label})

    cap.release()
    face_mesh.close()

    analysis = {"recording_path": video_path, "duration": duration, "events": events}
    return analysis
