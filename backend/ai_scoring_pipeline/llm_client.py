from openai import OpenAI

client = OpenAI()

def evaluate_answer_with_llm(question, answer):
    print("🚀 Function started")

    prompt = f"""
    Evaluate the candidate's answer.

    Question: {question}
    Answer: {answer}

    Score from 0 to 10 based on:
    - correctness
    - clarity
    - completeness

    Return only a number.
    """

    try:
        print("📡 Sending request to OpenAI...")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        print("✅ Response received")

        raw_output = response.choices[0].message.content.strip()
        print("🧠 Raw output:", raw_output)

        score = float(raw_output)
        return score

    except Exception as e:
        print("❌ ERROR:", e)
        return None
    
    