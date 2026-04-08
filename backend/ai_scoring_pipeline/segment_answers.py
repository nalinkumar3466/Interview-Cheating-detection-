from collections import defaultdict
import math

def segment_qa_fixed_windows(transcript, question_duration=2, cycle_duration=9):

    qa_dict = defaultdict(lambda: {
        "question": [],
        "answer": [],
        "question_start": None,
        "question_end": None,
        "answer_start": None,
        "answer_end": None
    })

    # 🔹 Find total duration
    max_time = max(seg["end"] for seg in transcript)
    total_buckets = math.ceil(max_time / cycle_duration)

    # 🔹 Assign segments to buckets
    for segment in transcript:
        text = segment["text"]
        start = segment["start"]
        end = segment["end"]

        bucket = int(start // cycle_duration)

        q_start_time = bucket * cycle_duration
        q_end_time = q_start_time + question_duration

        # QUESTION WINDOW
        if q_start_time <= start < q_end_time:

            if qa_dict[bucket]["question_start"] is None:
                qa_dict[bucket]["question_start"] = start

            qa_dict[bucket]["question"].append(text)
            qa_dict[bucket]["question_end"] = end

        # ANSWER WINDOW
        else:
            if qa_dict[bucket]["answer_start"] is None:
                qa_dict[bucket]["answer_start"] = start

            qa_dict[bucket]["answer"].append(text)
            qa_dict[bucket]["answer_end"] = end

    # 🔹 Build ALL buckets (even empty ones)
    qa_pairs = []

    for bucket in range(total_buckets):

        q = qa_dict[bucket]

        qa_pairs.append({
            "question": " ".join(q["question"]) if q["question"] else "",
            "question_start": q["question_start"],
            "question_end": q["question_end"],
            "answer": " ".join(q["answer"]) if q["answer"] else "",
            "answer_start": q["answer_start"],
            "answer_end": q["answer_end"]
        })

    return qa_pairs




