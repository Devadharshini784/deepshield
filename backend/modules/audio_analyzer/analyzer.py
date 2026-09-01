import whisper

# Load the model once when the server starts (not on every request - too slow otherwise)
# "base" is a good balance of speed vs accuracy for a prototype
print("Loading Whisper model, this happens once at startup...")
model = whisper.load_model("base")
print("Whisper model loaded.")

SCAM_KEYWORDS = [
    "otp", "one time password", "share your otp", "cvv", "pin number",
    "bank account", "verify your account", "gift card", "urgent",
    "kyc", "block your account", "suspended", "refund", "wire transfer",
    "western union", "arrest warrant", "police case", "legal action",
    "income tax", "customs department", "courier held", "parcel seized"
]

MONEY_REQUEST_KEYWORDS = [
    "send money", "transfer money", "pay now", "pay immediately",
    "google pay", "phonepe", "paytm", "upi", "bank transfer",
    "gift card code", "bitcoin", "cryptocurrency"
]

OTP_KEYWORDS = [
    "otp", "one time password", "verification code", "share the code",
    "tell me the code", "read out the number"
]

EMOTIONAL_MANIPULATION_PHRASES = [
    "don't tell anyone", "keep this confidential", "act immediately",
    "you will be arrested", "legal action will be taken", "your account will be blocked",
    "this is your final warning", "don't hang up", "stay on the line",
    "trust me", "i am from the government", "i am a police officer"
]


def transcribe_audio(audio_path):
    result = model.transcribe(audio_path)
    return result["text"].strip()


def detect_scam_keywords(text):
    text_lower = text.lower()
    found = [kw for kw in SCAM_KEYWORDS if kw in text_lower]
    return found


def detect_money_requests(text):
    text_lower = text.lower()
    found = [kw for kw in MONEY_REQUEST_KEYWORDS if kw in text_lower]
    return found


def detect_otp_requests(text):
    text_lower = text.lower()
    found = [kw for kw in OTP_KEYWORDS if kw in text_lower]
    return found


def detect_emotional_manipulation(text):
    text_lower = text.lower()
    found = [kw for kw in EMOTIONAL_MANIPULATION_PHRASES if kw in text_lower]
    return found


def calculate_audio_risk(scam_kw, money_kw, otp_kw, manipulation_kw):
    score = 0
    reasons = []

    if scam_kw:
        score += 15 * len(scam_kw)
        reasons.append(f"Scam-related keywords detected: {', '.join(scam_kw)}")

    if money_kw:
        score += 20 * len(money_kw)
        reasons.append(f"Money transfer request detected: {', '.join(money_kw)}")

    if otp_kw:
        score += 30
        reasons.append(f"Caller is asking for OTP/verification code, this is a major red flag: {', '.join(otp_kw)}")

    if manipulation_kw:
        score += 20 * len(manipulation_kw)
        reasons.append(f"Emotional pressure/manipulation tactics detected: {', '.join(manipulation_kw)}")

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
        "reasons": reasons if reasons else ["No strong scam indicators found in the audio"]
    }


def analyze_audio(audio_path):
    transcript = transcribe_audio(audio_path)

    scam_kw = detect_scam_keywords(transcript)
    money_kw = detect_money_requests(transcript)
    otp_kw = detect_otp_requests(transcript)
    manipulation_kw = detect_emotional_manipulation(transcript)

    risk = calculate_audio_risk(scam_kw, money_kw, otp_kw, manipulation_kw)

    return {
        "transcript": transcript,
        "scam_keywords_found": scam_kw,
        "money_request_keywords": money_kw,
        "otp_keywords": otp_kw,
        "manipulation_keywords": manipulation_kw,
        "risk_assessment": risk
    }