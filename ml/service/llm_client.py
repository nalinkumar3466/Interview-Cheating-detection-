from openai import OpenAI
from openai import RateLimitError
import json
import os

# Initialize client only when needed
def get_openai_client():
    try:
        return OpenAI()
    except Exception:
        return None

def generate_llm_analysis(event_percentages, risk_level):
    """
    Send suspicious behavior summary to OpenAI and return analysis.
    """

    if not event_percentages:
        return "No suspicious behaviors detected.\n\nOverall Risk Level: Low"

    prompt_lines = [
        "Suspicious behavior summary (percentage of interview duration):"
    ]

    for e in event_percentages:
        prompt_lines.append(
            f"- {e['event_name']}: {e['percentage_in_video']}%"
        )

    prompt_lines.append(
        "\nAnalyze the behaviors above and explain what they indicate in 3 lines only."
    )
    prompt_lines.append(
        f"End the response with: Overall Risk Level: {risk_level}"
    )

    prompt = "\n".join(prompt_lines)

    try:
        client = get_openai_client()
        if client is None:
            return fallback_analysis(event_percentages)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        # Use fallback analysis when OpenAI is not available
        return fallback_analysis(event_percentages)


def fallback_analysis(event_percentages):
    """
    Rule-based backup when LLM is unavailable.
    """

    risk_score = 0

    for e in event_percentages:
        if e["event_name"] == "Frequent Downward Gaze" and e["percentage_in_video"] > 20:
            risk_score += 2
        elif e["percentage_in_video"] > 10:
            risk_score += 1

    if risk_score >= 3:
        level = "High"
    elif risk_score == 2:
        level = "Medium"
    else:
        level = "Low"

    return (
        "Automated analysis based on behavioral statistics.\n"
        f"Overall risk level: {level}."
    )
