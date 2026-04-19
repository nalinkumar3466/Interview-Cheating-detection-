from ai_scoring_pipeline.llm_client import evaluate_answer_with_llm

print("🔥 Starting test...")

tests = [
    ("What is Python?", "A programming language"),
    ("What is Python?", "It is a snake"),
    ("Explain OOP", "Classes, objects, inheritance, polymorphism")
]

for q, a in tests:
    print("\n---")
    print("Q:", q)
    print("A:", a)
    print("Score:", evaluate_answer_with_llm(q, a))
