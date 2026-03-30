import json
from segment_answers import segment_qa_with_timestamps

with open("backend/uploads/transcripts/interview_16_0_rec_1773300944112.json") as f:
    transcript = json.load(f)

qa_pairs = segment_qa_with_timestamps(transcript)

for i, qa in enumerate(qa_pairs):
    print(f"\n--- Q{i+1} ---")

    print("Q:", qa["question"])
    print("Q time:", qa["question_start"], "→", qa["question_end"])

    print("A:", qa["answer"])
    print("A time:", qa["answer_start"], "→", qa["answer_end"])


