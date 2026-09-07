import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

# Only call the AI for cases the rule-based system isn't confident about.
# Below this = probably fine, above this = rules are already confident it's a scam.
BORDERLINE_LOW = 25
BORDERLINE_HIGH = 70


def is_borderline(score):
    return BORDERLINE_LOW <= score <= BORDERLINE_HIGH


def get_ai_verdict(evidence_type, content_summary, rule_score, rule_reasons):
    """
    evidence_type: "Screenshot" | "Email" | "Audio"
    content_summary: the extracted text / transcript / email body to reason about
    rule_score: the score the rule-based system gave (0-100)
    rule_reasons: list of reasons the rule-based system found
    """
    prompt = f"""You are a fraud detection expert analyzing potential scam evidence.

Evidence type: {evidence_type}
Content to analyze:
---
{content_summary[:3000]}
---

A rule-based system gave this a preliminary risk score of {rule_score}/100 for these reasons:
{chr(10).join('- ' + r for r in rule_reasons)}

Carefully assess whether this content shows signs of being a scam, phishing attempt, fraudulent
payment, or social engineering. Consider things a keyword list would miss: tone, plausibility,
psychological pressure tactics, whether claims make logical sense, and subtle inconsistencies.

Respond with ONLY valid JSON, no other text, no markdown code fences, in this exact format:
{{
  "ai_score": <integer 0-100>,
  "ai_level": "<Low Risk|Medium Risk|High Risk>",
  "confidence": "<Low|Medium|High>",
  "reasons": ["<specific reason 1>", "<specific reason 2>", "<up to 4 reasons>"]
}}"""

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=500,
            )
        )
        text = response.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
        result["ai_available"] = True
        return result
    except Exception as e:
        # If the API fails for any reason, fall back gracefully to the rule-based result
        return {
            "ai_score": rule_score,
            "ai_level": None,
            "confidence": "Low",
            "reasons": [f"AI verification unavailable: {str(e)}"],
            "ai_available": False
        }


def combine_rule_and_ai(rule_score, rule_reasons, ai_result):
    """
    Blends rule-based and AI scores when AI was consulted.
    AI gets more weight since it can reason about content the rules can't.
    """
    if not ai_result.get("ai_available"):
        return rule_score, rule_reasons

    final_score = round((rule_score * 0.4) + (ai_result["ai_score"] * 0.6))
    combined_reasons = rule_reasons + [f"AI check: {r}" for r in ai_result.get("reasons", [])]
    return final_score, combined_reasons