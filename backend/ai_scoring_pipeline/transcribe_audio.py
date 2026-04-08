import os
import json
from faster_whisper import WhisperModel

model = WhisperModel("base", device="cpu", compute_type="int8_float32")

AUDIO_DIR = "uploads/audio"
TRANSCRIPT_DIR = "uploads/transcripts"

os.makedirs(TRANSCRIPT_DIR, exist_ok=True)

def transcribe(audio_path):

    segments, _ = model.transcribe(audio_path)

    transcript = []

    for segment in segments:

        transcript.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip()
        })

    return transcript

def process_new_audio():

    for file in os.listdir(AUDIO_DIR):

        if not file.endswith(".wav"):
            continue

        audio_path = os.path.join(AUDIO_DIR, file)

        transcript_name = os.path.splitext(file)[0] + ".json"
        transcript_path = os.path.join(TRANSCRIPT_DIR, transcript_name)

        # Skip if transcript already exists
        if os.path.exists(transcript_path):
            print(f"Transcript already exists for {file}, skipping.")
            continue

        print(f"Transcribing {file}...")

        result = transcribe(audio_path)

        with open(transcript_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        print(f"Saved transcript: {transcript_name}")


if __name__ == "__main__":
    process_new_audio()