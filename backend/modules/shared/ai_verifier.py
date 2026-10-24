import os
import json
import time
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

def _generate_with_retry(max_retries=2, delay_seconds=3, **kwargs):
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return client.models.generate_content(**kwargs)
        except Exception as e:
            last_error = e
            error_text = str(e)
            if "503" in error_text or "UNAVAILABLE" in error_text or "overloaded" in error_text.lower():
                if attempt < max_retries:
                    time.sleep(delay_seconds)
                    continue
            raise last_error
    raise last_error

MODEL_NAME = "gemini-3.6-flash"

BORDERLINE_LOW = 25
BORDERLINE_HIGH = 70

class ImageVerdict(BaseModel):
    ai_score: int
    ai_level: str
    confidence: str
    reasons: list[str]

def is_borderline(score):
    return BORDERLINE_LOW <= score <= BORDERLINE_HIGH


def get_ai_verdict(evidence_type, content_summary, rule_score, rule_reasons):

    prompt = f"""
You are a fraud detection expert analyzing potential scam evidence.

Evidence type: {evidence_type}

Content to analyze:
---
{content_summary[:3000]}
---

A rule-based system gave this a preliminary risk score of {rule_score}/100
for these reasons:

{chr(10).join('- ' + r for r in rule_reasons)}

Carefully assess whether this content shows signs of:
- scam
- phishing
- fraudulent payment
- social engineering
- impersonation
- urgency or psychological pressure
- suspicious requests
- inconsistencies

Do not blindly agree with the rule-based score.
Perform your own assessment.

Respond with ONLY valid JSON.

Use exactly this format:

{{
  "ai_score": <integer 0-100>,
  "ai_level": "<Low Risk|Medium Risk|High Risk>",
  "confidence": "<Low|Medium|High>",
  "reasons": [
    "<specific reason 1>",
    "<specific reason 2>",
    "<up to 4 reasons>"
  ]
}}
"""

    try:

        response = _generate_with_retry(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=1024,
                thinking_config=types.ThinkingConfig(thinking_level="low")
            )
        )

        text = response.text.strip()

        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

        result = json.loads(text)

        result["ai_available"] = True

        return result

    except Exception as e:

        print("GEMINI TEXT ERROR:", repr(e))

        return {
            "ai_score": rule_score,
            "ai_level": None,
            "confidence": "Low",
            "reasons": [
                f"AI verification unavailable: {str(e)}"
            ],
            "ai_available": False
        }


def get_image_ai_verdict(
    image_path,
    extracted_text,
    rule_score,
    rule_reasons
):

    prompt = f"""
You are a fraud detection expert examining a screenshot submitted
as potential scam evidence.

IMPORTANT:
Examine the ACTUAL IMAGE carefully.
Do not rely only on OCR text.

OCR-extracted text:
---
{extracted_text[:3000]}
---

A rule-based system gave this screenshot a preliminary risk score
of {rule_score}/100 for these reasons:

{chr(10).join('- ' + r for r in rule_reasons)}

Analyze the actual screenshot for:

1. Whether the screenshot looks like a genuine banking,
UPI, or payment application.

2. Visual inconsistencies such as:
- unusual fonts
- inconsistent font sizes
- incorrect spacing
- strange icons
- inconsistent logos
- distorted graphics
- unnatural UI elements
- suspicious alignment
- fake-looking branding

3. Signs of image manipulation or synthetic generation.

4. Whether the payment information looks internally consistent.

5. Whether the screenshot contains a suspicious payment claim.

6. Whether transaction details appear suspicious,
generic, fabricated, or inconsistent.

IMPORTANT SECURITY PRINCIPLE:

A screenshot claiming that money was transferred is NOT proof
that money was actually received.

The recipient should verify the transaction directly inside
their own bank or UPI application.

Do not blindly agree with the rule-based score.
Perform your own independent assessment.

Return ONLY the requested structured fields.
"""

    try:

        image = Image.open(image_path)

        response = _generate_with_retry(
            model=MODEL_NAME,
            contents=[
                prompt,
                image
            ],
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=1024,
                thinking_config=types.ThinkingConfig(thinking_level="low"),
                response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "ai_score": {
                            "type": "INTEGER"
                        },
                        "ai_level": {
                            "type": "STRING"
                        },
                        "confidence": {
                            "type": "STRING"
                        },
                        "reasons": {
                            "type": "ARRAY",
                            "items": {
                                "type": "STRING"
                            }
                        }
                    },
                    "required": [
                        "ai_score",
                        "ai_level",
                        "confidence",
                        "reasons"
                    ]
                }
            )
        )

        print("RAW GEMINI RESPONSE:")
        print(repr(response.text))

        text = response.text.strip()

        result = json.loads(text)

        # Safety checks
        result["ai_score"] = max(
            0,
            min(100, int(result["ai_score"]))
        )

        result["ai_available"] = True

        return result

    except Exception as e:

        print("GEMINI IMAGE ERROR:", repr(e))

        return {
            "ai_score": rule_score,
            "ai_level": None,
            "confidence": "Low",
            "reasons": [
                f"AI visual verification unavailable: {str(e)}"
            ],
            "ai_available": False
        }
    
def combine_rule_and_ai(rule_score, rule_reasons, ai_result):
    if not ai_result.get("ai_available"):
        return rule_score, rule_reasons

    ai_score = ai_result["ai_score"]
    ai_confidence = str(ai_result.get("confidence", "Medium")).strip().lower()

    # A confident AI verdict should carry more weight than a fixed 60% -
    # Gemini can reason about things (visual fakes, implausible claims,
    # tone) that the rule-based score structurally cannot see.
    weight_by_confidence = {"high": 0.75, "medium": 0.6, "low": 0.5}
    ai_weight = weight_by_confidence.get(ai_confidence, 0.6)
    rule_weight = 1 - ai_weight

    final_score = round((rule_score * rule_weight) + (ai_score * ai_weight))

    # Don't let a confidently High Risk AI verdict get diluted down into a
    # different risk tier by an unrelated, more cautious rule score.
    if ai_confidence == "high" and ai_score >= 70:
        final_score = max(final_score, 70)

    combined_reasons = rule_reasons + [f"AI check: {r}" for r in ai_result.get("reasons", [])]
    return final_score, combined_reasons