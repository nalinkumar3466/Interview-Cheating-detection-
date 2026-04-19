from ai_scoring_pipeline.scoring import score_segments

print("🔥 Testing full scoring pipeline...\n")

# Dummy segments (simulate your pipeline output)
segments = [
    {
        "question": "What is Python?",
        "answer": "Python is a programming language because it is easy to use. For example, beginners use it."
    },
    {
        "question": "Explain OOP",
        "answer": "OOP uses classes and objects."
    }
]

results = score_segments(segments)

for i, res in enumerate(results, 1):
    print(f"\n--- Segment {i} ---")
    print("Question:", res["question"])
    print("Answer:", res["answer"])
    print("LLM Score:", res["llm_score"])
    print("Rule Score:", res["rule_score"])
    print("Final Score:", res["final_score"])