import json

def segment_qa_with_timestamps(transcript, silence_threshold=5):

    qa_pairs = []

    current_question = []
    current_answer = []

    q_start, q_end = None, None
    a_start, a_end = None, None

    mode = "question"   # first segment assumed as question

    for i in range(len(transcript)):

        segment = transcript[i]
        text = segment["text"]
        start = segment["start"]
        end = segment["end"]

        # ---------------------------
        # QUESTION MODE
        # ---------------------------
        if mode == "question":

            if q_start is None:
                q_start = start

            current_question.append(text)
            q_end = end

            mode = "answer"
            continue

        # ---------------------------
        # ANSWER MODE
        # ---------------------------
        if mode == "answer":

            if a_start is None:
                a_start = start

            current_answer.append(text)
            a_end = end

            # Check silence gap
            if i < len(transcript) - 1:
                next_start = transcript[i+1]["start"]
                gap = next_start - end

                if gap >= silence_threshold:
                    qa_pairs.append({
                        "question": " ".join(current_question),
                        "question_start": q_start,
                        "question_end": q_end,
                        "answer": " ".join(current_answer),
                        "answer_start": a_start,
                        "answer_end": a_end
                    })

                    # Reset everything
                    current_question = []
                    current_answer = []

                    q_start, q_end = None, None
                    a_start, a_end = None, None

                    mode = "question"

    # अंतिम pair (last one)
    if current_question and current_answer:
        qa_pairs.append({
            "question": " ".join(current_question),
            "question_start": q_start,
            "question_end": q_end,
            "answer": " ".join(current_answer),
            "answer_start": a_start,
            "answer_end": a_end
        })

    return qa_pairs
