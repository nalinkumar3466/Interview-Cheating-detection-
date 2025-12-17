import os
import glob
import csv
from process_behavior_from_csv import BehaviorRulesFromCSV
from event_manager import SuspiciousEventManager


LOG_FOLDER = "logs"
OUTPUT_FOLDER = "events"
FPS = 30   # Update if needed

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def process_csv(csv_path):
    filename = os.path.basename(csv_path)
    base = filename.replace(".csv", "")
    print(f"\n🔍 Processing {filename} ...")

    # Initialize event engine
    event_mgr = SuspiciousEventManager()
    rules = BehaviorRulesFromCSV(FPS, event_mgr)

    last_time = 0

    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                t = float(row["Timestamp"])
            except:
                continue

            gaze = row["Smooth_gaze"]
            rules.update(gaze, t)
            last_time = t

    # Close any open events
    rules.finalize()

    # Save JSON
    output_json = os.path.join(OUTPUT_FOLDER, f"{base}_events.json")
    event_mgr.save(output_json)

    print(f"   ➤ Saved events to {output_json}")


def main():
    csv_files = glob.glob(os.path.join(LOG_FOLDER, "*.csv"))

    if not csv_files:
        print("⚠ No CSV files found in logs/ folder.")
        return

    print(f"📁 Found {len(csv_files)} CSV files.")
    for csv_path in csv_files:
        process_csv(csv_path)

    print("\n🎉 All event analysis completed.")


if __name__ == "__main__":
    main()
