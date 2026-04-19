from ai_scoring_pipeline.rule_engine import rule_based_score

print("🔥 Testing Rule Engine...\n")

answers = [
    "Short answer",
    "This is a longer answer because it explains something clearly.",
    "This answer includes an example because it demonstrates the concept. For example, using lists in Python."
]

for ans in answers:
    score = rule_based_score(ans)
    print(f"Answer: {ans}")
    print(f"Score: {score}\n")