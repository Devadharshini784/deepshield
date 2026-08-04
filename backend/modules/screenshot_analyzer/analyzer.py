import pytesseract
import cv2
import numpy as np
from pyzbar.pyzbar import decode
from PIL import Image

# IMPORTANT: update this path if your Tesseract install location is different
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Common keywords found in fake payment screenshots / scam texts
SUSPICIOUS_KEYWORDS = [
    "urgent", "verify now", "account suspended", "click here",
    "limited time", "act now", "congratulations", "you won",
    "claim your prize", "otp", "refund pending", "payment failed",
    "kyc update", "blocked", "reactivate", "gift card"
]

# Words that commonly appear specifically in fake payment/UPI screenshots
FAKE_PAYMENT_KEYWORDS = [
    "payment successful", "amount credited", "transaction id",
    "upi reference", "money received", "rs.", "₹"
]


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
    """
    Basic manipulation check using Error Level Analysis (ELA) approximation.
    This is a simplified rule-based check, not a deep learning model.
    """
    image = cv2.imread(image_path)
    if image is None:
        return {"manipulated": False, "reason": "Could not read image"}

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

    # Very low variance can indicate blurring/smoothing often used to hide edits
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


def calculate_risk_score(extracted_text, qr_results, manipulation_result):
    score = 0
    reasons = []

    text_lower = extracted_text.lower()

    for keyword in SUSPICIOUS_KEYWORDS:
        if keyword in text_lower:
            score += 15
            reasons.append(f"Suspicious phrase detected: '{keyword}'")

    for keyword in FAKE_PAYMENT_KEYWORDS:
        if keyword in text_lower:
            score += 10
            reasons.append(f"Payment-related phrase detected: '{keyword}'")

    if qr_results:
        score += 20
        reasons.append(f"{len(qr_results)} QR code(s) found in image - verify destination before scanning")

    if manipulation_result.get("manipulated"):
        score += 25
        reasons.append(manipulation_result.get("reason"))

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
    risk = calculate_risk_score(extracted_text, qr_results, manipulation_result)

    return {
        "extracted_text": extracted_text,
        "qr_codes": qr_results,
        "manipulation_check": manipulation_result,
        "risk_assessment": risk
    }