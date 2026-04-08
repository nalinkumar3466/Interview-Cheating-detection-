def rule_based_score(answer):
    score = 0
    word_count = len(answer.split())

    if word_count > 9:
        score += 3
    if word_count > 14:
        score += 5

    if "example" in answer.lower():
        score += 2

    if "because" in answer.lower():
        score += 3

    return min(score, 10)

