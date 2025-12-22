# Gaze state tracking
self.current_state = None
self.state_start_time = None

# Reading pattern
self.read_buffer = deque(maxlen=20)

# Downward gaze frequency
self.down_buffer = deque(maxlen=int(5 * fps))


class BehaviorRulesFromCSV:
    def __init__(self, fps, event_manager):
        self.fps = fps
        self.event_manager = event_manager

        # ---- CONTINUOUS GAZE STATE ----
        self.current_state = None
        self.state_start_time = None
        self.last_time = 0

        self.READING_WINDOW = 20  # same as behavior_rules.py
        self.read_buffer = deque(maxlen=self.READING_WINDOW)

        # ---------- Long Gaze Away ----------
        self.AWAY_DIRECTIONS = ["LEFT", "RIGHT"]
        self.AWAY_TIME_SEC = 1.0
        self.away_frame_limit = int(self.AWAY_TIME_SEC * fps)
        self.away_counter = 0
        self.away_start_time = None

        # ---------- Downward Gaze Frequency ----------
        self.DOWN_WINDOW = int(5 * fps)
        self.down_buffer = deque(maxlen=self.DOWN_WINDOW)

    # ---------------------------------------------------------
    def update(self, gaze, time):

        # --------------------------
        # 1. Track duration per gaze
        # --------------------------
        if self.current_state is None:
            self.current_state = gaze
            self.state_start_time = time

        elif gaze != self.current_state:
            # Close old event
            duration = time - self.state_start_time
            if duration >= 0.4:  # 400ms minimum to avoid jitter
                self.events.add_event(
                    f"{self.current_state} Gaze",
                    self.state_start_time,
                    time,
                    details=f"Duration {duration:.2f} sec"
                )
            # Start new event
            self.current_state = gaze
            self.state_start_time = time

        # --------------------------
        # 2. Reading Pattern
        # --------------------------
        # ==========================================
        # 2. Reading Pattern (all directional flips)
        # ==========================================

        READING_TRANSITIONS = {
            ("LEFT", "UP"), ("UP", "LEFT"),
            ("RIGHT", "UP"), ("UP", "RIGHT"),
            ("LEFT", "RIGHT"), ("RIGHT", "LEFT"),
            ("LEFT", "DOWN"), ("DOWN", "LEFT"),
            ("RIGHT", "DOWN"), ("DOWN", "RIGHT")
        }

        self.read_buffer.append(gaze)

        reading_flips = 0
        for i in range(1, len(self.read_buffer)):
            prev = self.read_buffer[i - 1]
            curr = self.read_buffer[i]
            if (prev, curr) in READING_TRANSITIONS:
                reading_flips += 1

        if reading_flips >= 3:
            start_t = time - (self.READING_WINDOW / self.fps)
            self.event_manager.add_event(
                "Reading Pattern Detected",
                start_t,
                time,
                details=f"{reading_flips} directional changes"
            )

        # --------------------------
        # 3. Downward gaze frequency
        # --------------------------
        self.down_buffer.append(1 if gaze == "DOWN" else 0)

        if len(self.down_buffer) == self.down_buffer.maxlen:
            ratio = sum(self.down_buffer) / len(self.down_buffer)
            if ratio > 0.30:
                self.events.add_event(
                    "Frequent Downward Gaze",
                    time - 5,
                    time,
                    details=f"Down ratio {ratio:.2f}"
                )

    # ---------------------------------------------------------
    def finalize(self, last_time):
        """Close the last open gaze event"""
        if self.current_state is not None:
            self.events.add_event(
                f"{self.current_state} Gaze",
                self.state_start_time,
                last_time,
                details=f"Duration {last_time - self.state_start_time:.2f} sec"
            )




self.reading_buffer.append(gaze)

        reading_flips = 0
        for i in range(1, len(self.reading_buffer)):
            prev = self.reading_buffer[i - 1]
            curr = self.reading_buffer[i]
            if (prev, curr) in self.READING_TRANSITIONS:
                reading_flips += 1

        if reading_flips >= 3:
            start_t = t - (self.READING_WINDOW / self.fps)
            self.event_manager.add_event(
                "Reading Pattern Detected",
                start_t,
                t,
                details=f"{reading_flips} directional transitions"
            )


def finalize(self):
    if self.current_state is not None:
        self.event_manager.add_event(
            f"{self.current_state} Gaze",
            self.state_start_time,
            self.last_time,
            details=f"Duration {(self.last_time - self.state_start_time):.2f} sec"
        )
    # --------------------------------------------------
    # Flush reading pattern if still active
    # --------------------------------------------------
    if len(self.reading_segments) >= self.MIN_READING_SEGMENTS:
        self.event_manager.add_event(
            "Reading Pattern",
            self.reading_start_time,
            self.last_time,
            details=f"{len(self.reading_segments)} short gaze shifts"
        )




        self.down_buffer.append(1 if gaze == "DOWN" else 0)

        if len(self.down_buffer) == self.DOWN_WINDOW:
            down_ratio = sum(self.down_buffer) / len(self.down_buffer)
            if down_ratio > 0.30:
                start_t = t - 5
                self.event_manager.add_event(
                    "Frequent Downward Gaze",
                    start_t,
                    t,
                    details=f"Downward ratio: {down_ratio:.2f}"
                )

