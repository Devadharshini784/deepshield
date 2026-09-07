import pytesseract
import cv2
import numpy as np
import re
from pyzbar.pyzbar import decode
from PIL import Image
from modules.shared.ai_verifier import get_image_ai_verdict, combine_rule_and_ai

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

SUSPICIOUS_KEYWORDS = [
    "urgent", "verify now", "account suspended", "click here",
    "limited time", "act now", "congratulations", "you won",
    "claim your prize", "otp", "refund pending", "payment failed",
    "kyc update", "blocked", "reactivate", "gift card"
]

FAKE_PAYMENT_KEYWORDS = [
    "payment successful", "amount credited", "transaction id",
    "upi reference", "money received", "rs.", "₹"
]

PAYMENT_SUCCESS_PHRASES = [
    "payment successful", "payment received", "money added", "amount credited",
    "transaction successful", "payment done", "you have received",
    "credited to your account", "sent successfully", "transfer successful",
    "paid successfully"
]

# The classic "overpayment / sent by mistake, please refund" scam pattern.
# This is high-risk almost by definition: legitimate senders don't ask strangers
# to manually refund money using only a screenshot as "proof."
REFUND_SCAM_PHRASES = [
    "sent by mistake", "sent it by mistake", "wrong account", "wrong upi",
    "wrong number", "please return", "please refund", "kindly refund",
    "return the money", "return it back", "transferred by mistake",
    "sent to the wrong", "accidentally sent", "accidentally transferred",
    "can you return", "please send it back"
]

TRANSACTION_REF_PATTERN = re.compile(r'\b[A-Za-z0-9]{10,20}\b')
TIME_PATTERN = re.compile(r'\b\d{1,2}[:.]\d{2}\s?(AM|PM|am|pm)?\b')


def extract_text_from_image(image_path):
    image = Image.open(image_path)
    return pytesseract.image_to_string(image).strip()


def detect_qr_codes(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return []
    return [{"type": obj.type, "data": obj.data.decode("utf-8", errors="ignore")} for obj in decode(image)]


def detect_image_manipulation(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return {"manipulated": False, "reason": "Could not read image"}
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    if laplacian_var < 50:
        return {"manipulated": True, "reason": "Unusually smooth/blurred regions detected, possible editing", "score": round(laplacian_var, 2)}
    return {"manipulated": False, "reason": "No strong signs of manipulation detected", "score": round(laplacian_var, 2)}


def detect_fake_payment_patterns(text):
    text_lower = text.lower()
    findings = []
    has_success_claim = any(p in text_lower for p in PAYMENT_SUCCESS_PHRASES)
    has_reference_number = bool(TRANSACTION_REF_PATTERN.search(text))

    if has_success_claim and not has_reference_number:
        findings.append(
            "Claims a successful payment but no valid transaction/reference number was found — "
            "a common sign of a fake or AI-generated payment screenshot"
        )
    return findings, has_success_claim


def detect_refund_scam_pattern(text):
    text_lower = text.lower()
    found = [p for p in REFUND_SCAM_PHRASES if p in text_lower]
    return found


def check_authenticity_signals(image_path, extracted_text):
    findings = []
    image = cv2.imread(image_path)
    if image is None:
        return findings
    height, width = image.shape[:2]
    if width == 0:
        return findings
    aspect_ratio = height / width
    if not (1.5 <= aspect_ratio <= 2.6):
        findings.append(
            f"Image proportions ({width}x{height}) don't match typical phone screenshot dimensions"
        )
    if not TIME_PATTERN.search(extracted_text):
        findings.append("No status bar clock/time reading detected near the top of the image")
    return findings


def calculate_risk_score(extracted_text, qr_results, manipulation_result,
                          fake_payment_findings, authenticity_findings,
                          has_payment_claim, refund_scam_findings):
    score = 0
    reasons = []
    text_lower = extracted_text.lower()

    for keyword in SUSPICIOUS_KEYWORDS:
        if keyword in text_lower:
            score += 15
            reasons.append(f"Suspicious phrase detected: '{keyword}'")

    for keyword in FAKE_PAYMENT_KEYWORDS:
        if keyword in text_lower:
            score += 8
            reasons.append(f"Payment-related phrase detected: '{keyword}'")

    if fake_payment_findings:
        score += 35
        reasons.extend(fake_payment_findings)

    if authenticity_findings:
        score += 15 * len(authenticity_findings)
        reasons.extend(authenticity_findings)

    if qr_results:
        score += 20
        reasons.append(f"{len(qr_results)} QR code(s) found in image - verify destination before scanning")

    if manipulation_result.get("manipulated"):
        score += 25
        reasons.append(manipulation_result.get("reason"))

    # Refund-scam pattern is a hard escalation, regardless of how clean the image looks
    if refund_scam_findings and has_payment_claim:
        score = max(score, 75)
        reasons.append(
            f"This message asks you to refund/return money based on phrases like "
            f"'{refund_scam_findings[0]}' — this is a well-known scam pattern. A screenshot alone "
            "never proves money was actually sent. Check your own bank/UPI app balance directly "
            "before returning anything."
        )

    if has_payment_claim and score < 30:
        score = 30
        reasons.append(
            "This image claims a payment was completed — always verify directly in your bank/UPI "
            "app, never trust a screenshot alone as proof of payment"
        )

    score = min(score, 100)
    level = "High Risk" if score >= 70 else "Medium Risk" if score >= 40 else "Low Risk"

    return {
        "score": score,
        "level": level,
        "reasons": reasons if reasons else ["No strong scam indicators found"]
    }


def analyze_screenshot(image_path):
    extracted_text = extract_text_from_image(image_path)
    qr_results = detect_qr_codes(image_path)
    manipulation_result = detect_image_manipulation(image_path)
    fake_payment_findings, has_payment_claim = detect_fake_payment_patterns(extracted_text)
    authenticity_findings = check_authenticity_signals(image_path, extracted_text)
    refund_scam_findings = detect_refund_scam_pattern(extracted_text)

    risk = calculate_risk_score(
        extracted_text, qr_results, manipulation_result,
        fake_payment_findings, authenticity_findings, has_payment_claim, refund_scam_findings
    )

    # Always run visual AI verification when there's a payment claim - this is the actual
    # accuracy fix, since rule-based checks alone cannot judge a convincing fake image.
    ai_verified = False
    if has_payment_claim:
        ai_result = get_image_ai_verdict(image_path, extracted_text, risk["score"], risk["reasons"])
        final_score, final_reasons = combine_rule_and_ai(risk["score"], risk["reasons"], ai_result)
        if ai_result.get("ai_available"):
            ai_verified = True
            # Never let AI blending pull the score below the refund-scam floor
            if refund_scam_findings:
                final_score = max(final_score, 70)
            risk["score"] = final_score
            risk["reasons"] = final_reasons
            risk["level"] = "High Risk" if final_score >= 70 else "Medium Risk" if final_score >= 40 else "Low Risk"

    risk["ai_verified"] = ai_verified

    return {
        "extracted_text": extracted_text,
        "qr_codes": qr_results,
        "manipulation_check": manipulation_result,
        "risk_assessment": risk
    }