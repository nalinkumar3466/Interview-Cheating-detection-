import os
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
AUDIO_DIR = os.path.join(UPLOADS_DIR, "audio")

VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv", ".webm")


def ensure_audio_directory():
    if not os.path.exists(AUDIO_DIR):
        os.makedirs(AUDIO_DIR)


def extract_audio(video_path, output_path):
    command = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        output_path
    ]

    try:
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.DEVNULL
        )

        if os.path.exists(output_path):
            print(f"✅ Audio saved: {output_path}")
            return output_path
        else:
            print("❌ Audio file not created")
            return None

    except subprocess.CalledProcessError:
        print(f"❌ FFmpeg failed for: {video_path}")
        return None

def process_videos():
    ensure_audio_directory()

    print("Scanning uploads folder:")
    print(UPLOADS_DIR)

    for root, dirs, files in os.walk(UPLOADS_DIR):
        for file in files:
            if file.lower().endswith(VIDEO_EXTENSIONS):

                video_path = os.path.join(root, file)
                
                if os.path.getsize(video_path) < 10000:
                    print(f"Skipping invalid video: {file}")
                    continue

                audio_file_name = os.path.splitext(file)[0] + ".wav"
                audio_path = os.path.join(AUDIO_DIR, audio_file_name)

                if os.path.exists(audio_path):
                    print(f"Audio already exists for {file}, skipping...")
                    continue

                print(f"Extracting audio from {file}...")
                extract_audio(video_path, audio_path)
                print(f"Saved: {audio_file_name}")

    print("Done.")


if __name__ == "__main__":
    process_videos()

