from .llm_client import evaluate_answer_with_llm
from .rule_engine import rule_based_score


def score_segments(segments):
    scored = []

    for seg in segments:
        question = seg.get("question", "")
        answer = seg.get("answer", "")

        # LLM score
        llm_score = evaluate_answer_with_llm(question, answer)

        # Rule-based score
        rule_score = rule_based_score(answer)

        # Final score
        final_score = (llm_score + rule_score) / 2

        scored.append({
            **seg,
            "llm_score": llm_score,
            "rule_score": rule_score,
            "final_score": final_score
        })

    return scored

