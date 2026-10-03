from openai import OpenAI
from ..utils.config import OPENAI_API_KEY
import json

client = OpenAI(api_key=OPENAI_API_KEY)


def classify_warm_lead(text: str) -> dict:
    """
    Classifies a lead reply into:
    - intent: cold | neutral | warm | hot
    - score: 0-100
    - reason: str
    """

    prompt = f"""
Respond ONLY with a VALID JSON dictionary. No explanations.

Analyze the sales intent of this reply:

\"\"\"{text}\"\"\"

Return EXACTLY this structure:

{{
  "intent": "cold | neutral | warm | hot",
  "score": <0-100>,
  "reason": "<one short sentence>"
}}
"""

    try:
        # NEW API CALL (correct one)
        response = client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
            max_output_tokens=150,
        )

        output = response.output_text.strip()

        # Try parsing normally
        return json.loads(output)

    except Exception as e:
        print("⚠️ JSON parsing failed:", e)
        print("Raw output:", output if 'output' in locals() else "None")

        # SECOND ATTEMPT — force extract JSON with regex
        try:
            import re
            json_str = re.search(r"\{.*\}", output, flags=re.S).group(0)
            return json.loads(json_str)
        except:
            # FINAL FALLBACK
            return {
                "intent": "neutral",
                "score": 40,
                "reason": "fallback parsing"
            }
