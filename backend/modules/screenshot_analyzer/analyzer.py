import pytesseract
import cv2
import numpy as np
import re
from pyzbar.pyzbar import decode
from PIL import Image

# IMPORTANT: update this path if your Tesseract install location is different
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

# Real UPI/bank transaction references are long numeric/alphanumeric strings
TRANSACTION_REF_PATTERN = re.compile(r'\b[A-Za-z0-9]{10,20}\b')
TIME_PATTERN = re.compile(r'\b\d{1,2}[:.]\d{2}\s?(AM|PM|am|pm)?\b')


def extract_text_from_image(image_path):
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    return text.strip()


def detect_qr_codes(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return []
    decoded_objects = decode(image)
    qr_results = []
    for obj in decoded_objects:
        qr_results.append({
            "type": obj.type,
            "data": obj.data.decode("utf-8", errors="ignore")
        })
    return qr_results


def detect_image_manipulation(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return {"manipulated": False, "reason": "Could not read image"}

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

    if laplacian_var < 50:
        return {
            "manipulated": True,
            "reason": "Unusually smooth/blurred regions detected, possible editing",
            "score": round(laplacian_var, 2)
        }
    return {
        "manipulated": False,
        "reason": "No strong signs of manipulation detected",
        "score": round(laplacian_var, 2)
    }


def detect_fake_payment_patterns(text):
    """
    Genuine payment confirmations almost always show a long transaction/UTR/reference number.
    AI-generated or manually edited fake screenshots often claim success without one.
    """
    text_lower = text.lower()
    findings = []
    has_success_claim = any(p in text_lower for p in PAYMENT_SUCCESS_PHRASES)
    has_reference_number = bool(TRANSACTION_REF_PATTERN.search(text))

    if has_success_claim and not has_reference_number:
        findings.append(
            "Claims a successful payment but no valid transaction/reference number was found — "
            "this is a common sign of a fake or AI-generated payment screenshot"
        )

    return findings, has_success_claim


def check_authenticity_signals(image_path, extracted_text):
    """
    Checks structural signs that a screenshot may not be a genuine phone capture.
    """
    findings = []
    image = cv2.imread(image_path)
    if image is None:
        return findings

    height, width = image.shape[:2]
    if width == 0:
        return findings
    aspect_ratio = height / width

    # Genuine phone screenshots are tall/portrait, roughly between these ratios
    if not (1.5 <= aspect_ratio <= 2.6):
        findings.append(
            f"Image proportions ({width}x{height}) don't match typical phone screenshot dimensions, "
            "which can indicate an edited or AI-generated image"
        )

    if not TIME_PATTERN.search(extracted_text):
        findings.append(
            "No status bar clock/time reading was detected near the top of the image — "
            "genuine phone screenshots almost always show one"
        )

    return findings


def calculate_risk_score(extracted_text, qr_results, manipulation_result,
                          fake_payment_findings, authenticity_findings, has_payment_claim):
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

    # Any payment-success claim deserves at least a caution-level score,
    # since screenshots are trivial to fake regardless of other signals
    if has_payment_claim and score < 30:
        score = 30
        reasons.append(
            "This image claims a payment was completed — always verify directly in your bank/UPI app, "
            "never trust a screenshot alone as proof of payment"
        )

    score = min(score, 100)

    if score >= 70:
        level = "High Risk"
    elif score >= 40:
        level = "Medium Risk"
    else:
        level = "Low Risk"

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

    risk = calculate_risk_score(
        extracted_text, qr_results, manipulation_result,
        fake_payment_findings, authenticity_findings, has_payment_claim
    )

    return {
        "extracted_text": extracted_text,
        "qr_codes": qr_results,
        "manipulation_check": manipulation_result,
        "risk_assessment": risk
    }