import csv
import json
from collections import deque

class SuspiciousEventManager:
    def __init__(self):
        self.events = []

    def add_event(self, name, start, end, details=""):
        self.events.append({
            "event": name,
            "start": round(start, 3),
            "end": round(end, 3),
            "details": details
        })

    def save(self, filename):
        with open(filename, "w") as f:
            json.dump(self.events, f, indent=4)


from collections import deque

class BehaviorRulesFromCSV:

    def __init__(self, fps, event_manager):

        self.fps = fps
        self.event_manager = event_manager

        # ----------------------------------------------------
        # Continuous Gaze State Tracking
        # ----------------------------------------------------
        self.current_state = None
        self.state_start_time = None
        self.last_time = None
        self.last_gaze = None


        # ----------------------------------------------------
        # Reading Pattern Detection
        # ----------------------------------------------------
        self.READING_WINDOW = 20
        self.reading_buffer = deque(maxlen=self.READING_WINDOW)

        self.reading_start_time = None
        self.reading_segments = []
        self.MAX_READING_GAZE_DURATION = 1.2  # seconds
        self.MIN_READING_SEGMENTS = 3

        # Allowed reading transitions
        self.READING_TRANSITIONS = {
            ("LEFT", "UP"), ("UP", "LEFT"),
            ("RIGHT", "UP"), ("UP", "RIGHT"),
            ("LEFT", "RIGHT"), ("RIGHT", "LEFT"),
            ("LEFT", "DOWN"), ("DOWN", "LEFT"),
            ("RIGHT", "DOWN"), ("DOWN", "RIGHT")
        }
        self.reading_flips = 0
        self.reading_seq = deque(maxlen=3)
        self.SEQ_READING_MIN = 2  # number of sequences required
        self.seq_reading_count = 0

        # ----------------------------------------------------
        # Long Gaze Away Detection (LEFT or RIGHT)
        # ----------------------------------------------------
        self.AWAY_DIRECTIONS = ["LEFT", "RIGHT", "DOWN", "UP"]
        self.AWAY_TIME_SEC = 1.0
        self.away_frame_limit = int(self.AWAY_TIME_SEC * fps)
        self.away_counter = 0
        self.away_start_time = None
        self.away_direction = None

        # ----------------------------------------------------
        # Downward Gaze Frequency Detection
        # ----------------------------------------------------
        self.DOWN_WINDOW = int(5 * fps)     # 5 seconds
        self.down_buffer = deque(maxlen=self.DOWN_WINDOW)
        self.down_event_active = False
        self.down_event_start = None
        self.last_down_ratio = 0.0

        # -------- Frequent Distraction Rule --------
        self.DISTRACTION_TIME_THRESHOLD = 2.0  # seconds
        self.MIN_DISTRACTION_COUNT = 3  # how many rapid switches = suspicious

        self.last_gaze = None
        self.last_change_time = None
        self.distraction_count = 0
        self.distraction_start_time = None


    # =====================================================================
    # Main Update Function — called once per CSV row
    # =====================================================================
    def update(self, gaze, t, blink_flag="NONE"):

        # Keep track of last timestamp

        if gaze == "BLINK":
            self.last_time = t
            self.reading_seq.clear()
            self.seq_reading_count = 0
            return
        # ----------------------------------------------------
        # Ignore blink frames completely
        # ----------------------------------------------------
        if blink_flag == "BLINK":
            self.away_counter = 0
            self.down_buffer.append(0)
            self.reading_buffer.append("CENTER")
            return

        # ----------------------------------------------------
        # 1. Continuous Gaze Segment Detection
        # ----------------------------------------------------
        if self.current_state is None:
            # first frame
            self.current_state = gaze
            self.state_start_time = t

        elif gaze != self.current_state:
            # end previous segment
            duration = t - self.state_start_time
            self.event_manager.add_event(
                f"{self.current_state} Gaze",
                self.state_start_time,
                t,
                details=f"Duration {duration:.2f} sec"
            )

            # start new one
            self.current_state = gaze
            self.state_start_time = t

        # ----------------------------------------------------
        # 2. Long Gaze Away (LEFT/RIGHT for >1 sec)
        # ----------------------------------------------------
        # ----------------------------------------------------
        # 2. Long Gaze Away (NOT CENTER for > X sec)
        # ----------------------------------------------------
        if gaze in self.AWAY_DIRECTIONS:
            if self.away_counter == 0:
                self.away_start_time = t
                self.away_direction = gaze  # track direction
            self.away_counter += 1
        else:
            # Gaze returned to CENTER → close event if valid
            if self.away_counter >= self.away_frame_limit:
                end = t
                self.event_manager.add_event(
                    "Long Gaze Away",
                    self.away_start_time,
                    end,
                    details=f"{self.away_direction} for {(end - self.away_start_time):.2f} sec"
                )

            self.away_counter = 0
            self.away_start_time = None
            self.away_direction = None

        # ----------------------------------------------------
        # 3. Reading Pattern Detection (rapid direction switches)
        # ----------------------------------------------------
        # --------------------------------------------------
        # READING PATTERN (time-aware)
        # --------------------------------------------------
        if gaze in ["LEFT", "RIGHT", "UP", "DOWN"] and gaze != self.current_state:

            # Close previous state
            if self.current_state is not None:
                duration = time - self.state_start_time

                if duration <= self.MAX_READING_GAZE_DURATION:
                    self.reading_segments.append((self.current_state, duration))

                    if self.reading_start_time is None:
                        self.reading_start_time = self.state_start_time

                        # --------- 3-step reading pattern detection ----------
                        self.reading_seq.append(prev_gaze)

                        if len(self.reading_seq) == 3:
                            if list(self.reading_seq) in [
                                ["LEFT", "CENTER", "RIGHT"],
                                ["RIGHT", "CENTER", "LEFT"],
                                ["LEFT", "DOWN", "RIGHT"],
                                ["RIGHT", "DOWN", "LEFT"]
                            ]:
                                self.seq_reading_count += 1
                else:
                    # Break reading if gaze held too long
                    if (
                        len(self.reading_segments) >= self.MIN_READING_SEGMENTS
                        or self.seq_reading_count >= self.SEQ_READING_MIN
                    ):
                        self.event_manager.add_event(
                            "Reading Pattern",
                            self.reading_start_time,
                            self.last_time,
                            details=(
                                f"{len(self.reading_segments)} short gaze shifts, "
                                f"{self.seq_reading_count} scan sequences"
                            )
                        )

                    self.reading_segments.clear()
                    self.reading_seq.clear()
                    self.reading_flips = 0
                    self.seq_reading_count = 0
                    self.reading_start_time = None


        # ----------------------------------------------------
        # 4. Downward Gaze Frequency
        # ----------------------------------------------------
        # -----------------------------------------
        # Downward Gaze Frequency (MERGED EVENT)
        # -----------------------------------------
        self.down_buffer.append(1 if gaze == "DOWN" else 0)

        if len(self.down_buffer) == self.DOWN_WINDOW:
            down_ratio = sum(self.down_buffer) / len(self.down_buffer)

            # ---- START downward event ----
            if down_ratio > 0.30 and not self.down_event_active:
                self.down_event_active = True
                self.down_event_start = t
                self.last_down_ratio = down_ratio

            # ---- CONTINUE downward event ----
            elif down_ratio > 0.30 and self.down_event_active:
                self.last_down_ratio = max(self.last_down_ratio, down_ratio)

            # ---- END downward event ----
            elif down_ratio <= 0.30 and self.down_event_active:
                self.event_manager.add_event(
                    "Frequent Downward Gaze",
                    self.down_event_start,
                    t,
                    details=f"Peak downward ratio: {self.last_down_ratio:.2f}"
                )

                self.down_event_active = False
                self.down_event_start = None

                self.last_down_ratio = 0.0

        # ----------------------------------------------------
        # Frequent Distraction Detection
        # ----------------------------------------------------
        if gaze not in ["BLINK"]:

            if self.last_gaze is None:
                self.last_gaze = gaze
                self.last_change_time = t

            elif gaze != self.last_gaze:
                time_diff = t - self.last_change_time

                if time_diff < self.DISTRACTION_TIME_THRESHOLD:
                    # Rapid gaze switch
                    if self.distraction_count == 0:
                        self.distraction_start_time = self.last_change_time

                    self.distraction_count += 1
                else:
                    # Reset if switch is slow
                    self.distraction_count = 0
                    self.distraction_start_time = None

                self.last_gaze = gaze
                self.last_change_time = t

            # ------------------------------------
            # 2. 🚨 EVENT EMISSION (ADD HERE)
            # ------------------------------------
            if self.distraction_count >= self.MIN_DISTRACTION_COUNT:
                self.event_manager.add_event(
                    "Frequent Distraction",
                    self.distraction_start_time,
                    t,
                    details=(
                        f"{self.distraction_count} rapid gaze switches "
                        f"(<{self.DISTRACTION_TIME_THRESHOLD}s)"
                    )
                )

                # Reset AFTER logging one event
                self.distraction_count = 0
                self.distraction_start_time = None

            # ------------------------------------
            # 3. Bookkeeping
            # ------------------------------------
            self.last_time = t

    # =====================================================================
    # Called at end of CSV to close the last open segment
    # =====================================================================

    def finalize(self):
        """
        Close any ongoing gaze or reading event at end of CSV
        """

        # Nothing to finalize
        if (
                self.current_state is None
                or self.state_start_time is None
                or self.last_time is None
        ):
            return

        duration = self.last_time - self.state_start_time
        if duration <= 0:
            return

        # 1. Final gaze segment
        if self.current_state in ["LEFT", "RIGHT", "UP", "DOWN", "CENTER"]:
            self.event_manager.add_event(
                f"{self.current_state} Gaze",
                self.state_start_time,
                self.last_time,
                details=f"Duration {duration:.2f} sec"
            )

        # 2. Final reading pattern (if pending)
        if len(self.reading_segments) >= self.MIN_READING_SEGMENTS:
            self.event_manager.add_event(
                "Reading Pattern",
                self.reading_start_time,
                self.last_time,
                details=f"{len(self.reading_segments)} short gaze shifts"
            )
