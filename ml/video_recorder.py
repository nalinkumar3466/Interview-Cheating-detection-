import cv2
import time

# Configuration
FILENAME = "samples/down.mp4"  # Change this name for each test
DURATION = 5.0  # Seconds to record
FPS = 10.0

cap = cv2.VideoCapture(0)

# Define the codec and create VideoWriter object
# 'mp4v' is a standard codec for .mp4 files
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
out = cv2.VideoWriter(FILENAME, fourcc, FPS, (w, h))

print(f"Recording start in 3 seconds... Get ready!")
time.sleep(3)
print(f"Recording... Action!")

start_time = time.time()
while (time.time() - start_time) < DURATION:
    ret, frame = cap.read()
    if ret:
        frame = cv2.flip(frame, 1)  # Optional: Mirror the recording
        out.write(frame)

        # Show specific countdown on screen
        elapsed = int(time.time() - start_time)
        remaining = DURATION - elapsed
        cv2.putText(frame, f"Rec: {remaining}s", (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow('Recording...', frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC to stop early
            break
    else:
        break

cap.release()
out.release()
cv2.destroyAllWindows()
print(f"Saved to {FILENAME}")