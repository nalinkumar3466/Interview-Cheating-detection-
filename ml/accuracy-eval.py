import csv
import os

CSV_FOLDER = "logs"

GROUND_TRUTH = {
    "left.mp4": "LEFT",
    "right.mp4": "RIGHT",
    "center.mp4": "CENTER",
    "down.mp4": "DOWN",
    "up.mp4": "UP",

}

def compute_accuracy(csv_path, true_label):
    correct = 0
    total = 0

    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pred = row["Direction"].strip()
            if pred == true_label:
                correct += 1
            total += 1

    accuracy = correct / total if total > 0 else 0
    return accuracy

def main():
    for csv_name in os.listdir(CSV_FOLDER):
        if not csv_name.endswith(".csv"):
            continue

        video_name = csv_name.replace(".csv", ".mp4")

        if video_name not in GROUND_TRUTH:
            print(f"No ground truth for {video_name}, skipping.")
            continue

        truth = GROUND_TRUTH[video_name]
        csv_path = os.path.join(CSV_FOLDER, csv_name)

        acc = compute_accuracy(csv_path, truth)
        print(f"{video_name}: {acc:.2%} accuracy")

if __name__ == "__main__":
    main()
