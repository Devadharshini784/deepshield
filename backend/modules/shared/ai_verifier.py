import os
import json
import PIL.Image
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

BORDERLINE_LOW = 25
BORDERLINE_HIGH = 70


def is_borderline(score):
    return BORDERLINE_LOW <= score <= BORDERLINE_HIGH


def get_ai_verdict(evidence_type, content_summary, rule_score, rule_reasons):
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
            generation_config=genai.types.GenerationConfig(temperature=0.2, max_output_tokens=500)
        )
        text = response.text.strip().replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
        result["ai_available"] = True
        return result
    except Exception as e:
        return {
            "ai_score": rule_score,
            "ai_level": None,
            "confidence": "Low",
            "reasons": [f"AI verification unavailable: {str(e)}"],
            "ai_available": False
        }


def get_image_ai_verdict(image_path, extracted_text, rule_score, rule_reasons):
    """
    Sends the ACTUAL screenshot image (not just OCR'd text) to Gemini's vision model.
    This catches things text-only keyword matching structurally cannot: unnatural fonts,
    inconsistent UI elements, fake app branding, and known scam patterns like someone
    claiming they "overpaid by mistake" and demanding a refund based on an unverifiable image.
    """
    prompt = f"""You are a fraud detection expert examining a screenshot submitted as scam evidence.
Look carefully at the actual image provided, not just the OCR text below.

OCR-extracted text from the image:
---
{extracted_text[:2000]}
---

A rule-based system gave this a preliminary risk score of {rule_score}/100 for these reasons:
{chr(10).join('- ' + r for r in rule_reasons)}

Examine the image itself for:
- Signs of AI generation: unnatural fonts, inconsistent icon rendering, blurry/warped logos,
  impossible or generic UI layouts, wrong app branding, inconsistent shadows or spacing
- Signs of manual editing: mismatched fonts or sizes, misaligned text, obvious copy-paste seams
- Whether this genuinely looks like a real phone screenshot of a banking/UPI/payment app
- The scam pattern in the text: a very common scam is someone claiming they "sent money by
  mistake" or "overpaid" and asking the recipient to refund it, using a fabricated screenshot as
  fake proof. Treat this pattern as HIGH RISK regardless of how convincing the image looks,
  because a screenshot can never prove money actually moved — only the recipient's own bank/UPI
  app balance can confirm that.

Respond with ONLY valid JSON, no other text, no markdown code fences, in this exact format:
{{
  "ai_score": <integer 0-100>,
  "ai_level": "<Low Risk|Medium Risk|High Risk>",
  "confidence": "<Low|Medium|High>",
  "reasons": ["<specific reason 1>", "<specific reason 2>", "<up to 4 reasons>"]
}}"""

    try:
        image = PIL.Image.open(image_path)
        response = model.generate_content(
            [prompt, image],
            generation_config=genai.types.GenerationConfig(temperature=0.2, max_output_tokens=500)
        )
        text = response.text.strip().replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
        result["ai_available"] = True
        return result
    except Exception as e:
        return {
            "ai_score": rule_score,
            "ai_level": None,
            "confidence": "Low",
            "reasons": [f"AI visual verification unavailable: {str(e)}"],
            "ai_available": False
        }


def combine_rule_and_ai(rule_score, rule_reasons, ai_result):
    if not ai_result.get("ai_available"):
        return rule_score, rule_reasons

    final_score = round((rule_score * 0.4) + (ai_result["ai_score"] * 0.6))
    combined_reasons = rule_reasons + [f"AI check: {r}" for r in ai_result.get("reasons", [])]
    return final_score, combined_reasons