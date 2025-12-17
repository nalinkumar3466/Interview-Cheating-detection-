# event_manager.py

import json

class SuspiciousEventManager:
    def __init__(self):
        self.events = []

    def add_event(self, event_type, start_time, end_time, details=None):
        self.events.append({
            "event": event_type,
            "start": round(start_time, 3),
            "end": round(end_time, 3),
            "details": details,
        })

    def save(self, path="suspicious_events.json"):
        with open(path, "w") as f:
            json.dump(self.events, f, indent=4)
