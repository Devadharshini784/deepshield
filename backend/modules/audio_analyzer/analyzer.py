import os
import re
from difflib import SequenceMatcher
import whisper
from pyannote.audio import Pipeline
from dotenv import load_dotenv
from modules.shared.ai_verifier import is_borderline, get_ai_verdict, combine_rule_and_ai

load_dotenv()

print("Loading Whisper model, this happens once at startup...")
whisper_model = whisper.load_model("base")
print("Whisper model loaded.")

HF_TOKEN = os.getenv("HF_TOKEN")
diarization_pipeline = None
print("Loading speaker diarization model, this happens once at startup...")
if HF_TOKEN:
    try:
        diarization_pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1", use_auth_token=HF_TOKEN
        )
        print("Speaker diarization model loaded.")
    except Exception as e:
        print(f"Could not load diarization model, continuing without it: {e}")
else:
    print("HF_TOKEN not set in .env, speaker diarization will be skipped.")

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

ROBOCALL_KEYWORDS = [
    "this will be the only notice", "limited time offer", "act now",
    "eligible for", "interest rate reduction", "final notice",
    "please call", "call back", "business days", "underwriting department",
    "card member services", "do not call list", "auto warranty",
    "student loan forgiveness", "social security number has been suspended",
    "your card has been", "press 1", "extended warranty", "congratulations",
    "pre-approved", "reduce your interest rate", "lower your payments",
    "irs", "warrant for your arrest", "compromised", "unusual activity"
]

PHONE_NUMBER_PATTERN = re.compile(r'\b(?:\+?\d{1,2}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b')


def transcribe_with_timestamps(audio_path):
    result = whisper_model.transcribe(audio_path)
    return result["text"].strip(), result.get("segments", [])


def diarize_speakers(audio_path):
    if diarization_pipeline is None:
        return None
    try:
        diarization = diarization_pipeline(audio_path)
        turns = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            turns.append({"start": turn.start, "end": turn.end, "speaker": speaker})
        return turns
    except Exception as e:
        print(f"Diarization failed, continuing without speaker labels: {e}")
        return None


def label_segments_with_speakers(whisper_segments, diarization_turns):
    """
    Assigns a speaker label to each Whisper segment by finding the diarization
    turn it overlaps with the most. Renames raw labels (SPEAKER_00 etc.) to
    friendly "Speaker 1", "Speaker 2" in order of first appearance.
    """
    speaker_name_map = {}
    next_number = 1
    labeled = []

    for seg in whisper_segments:
        seg_start, seg_end, seg_text = seg["start"], seg["end"], seg["text"].strip()
        best_speaker, best_overlap = None, 0

        for turn in diarization_turns:
            overlap = min(seg_end, turn["end"]) - max(seg_start, turn["start"])
            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = turn["speaker"]

        if best_speaker is None:
            friendly_name = "Unknown Speaker"
        else:
            if best_speaker not in speaker_name_map:
                speaker_name_map[best_speaker] = f"Speaker {next_number}"
                next_number += 1
            friendly_name = speaker_name_map[best_speaker]

        labeled.append({
            "speaker": friendly_name,
            "start": round(seg_start, 1),
            "end": round(seg_end, 1),
            "text": seg_text
        })

    return labeled


def merge_consecutive_same_speaker(labeled_segments):
    if not labeled_segments:
        return []
    merged = [dict(labeled_segments[0])]
    for seg in labeled_segments[1:]:
        if seg["speaker"] == merged[-1]["speaker"]:
            merged[-1]["text"] += " " + seg["text"]
            merged[-1]["end"] = seg["end"]
        else:
            merged.append(dict(seg))
    return merged


def build_labeled_transcript_text(merged_segments):
    return "\n".join(f"{seg['speaker']}: {seg['text']}" for seg in merged_segments)


def detect_scam_keywords(text):
    text_lower = text.lower()
    return [kw for kw in SCAM_KEYWORDS if kw in text_lower]


def detect_money_requests(text):
    text_lower = text.lower()
    return [kw for kw in MONEY_REQUEST_KEYWORDS if kw in text_lower]


def detect_otp_requests(text):
    text_lower = text.lower()
    return [kw for kw in OTP_KEYWORDS if kw in text_lower]


def detect_emotional_manipulation(text):
    text_lower = text.lower()
    return [kw for kw in EMOTIONAL_MANIPULATION_PHRASES if kw in text_lower]


def detect_robocall_patterns(text):
    text_lower = text.lower()
    return [kw for kw in ROBOCALL_KEYWORDS if kw in text_lower]


def extract_phone_numbers(text):
    return list(set(PHONE_NUMBER_PATTERN.findall(text)))


def detect_repeated_script(text):
    sentences = [s.strip() for s in re.split(r'[.!?]', text) if len(s.strip()) > 25]
    for i in range(len(sentences)):
        for j in range(i + 1, len(sentences)):
            if SequenceMatcher(None, sentences[i].lower(), sentences[j].lower()).ratio() > 0.55:
                return True
    return False


def calculate_audio_risk(scam_kw, money_kw, otp_kw, manipulation_kw, robocall_kw, phone_numbers, is_repeated_script):
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
    if robocall_kw:
        score += 12 * len(robocall_kw)
        reasons.append(f"Common robocall/scam-script phrases detected: {', '.join(robocall_kw)}")
    if is_repeated_script:
        score += 25
        reasons.append("The message repeats itself almost word-for-word, a strong sign of a pre-recorded scam robocall")
    if phone_numbers:
        reasons.append(
            f"Callback number(s) mentioned: {', '.join(phone_numbers)} — never call these directly, "
            "verify through the official number on your card/bank statement instead"
        )
        score += 10

    score = min(score, 100)
    level = "High Risk" if score >= 70 else "Medium Risk" if score >= 40 else "Low Risk"

    return {
        "score": score,
        "level": level,
        "reasons": reasons if reasons else ["No strong scam indicators found in the audio"]
    }


def analyze_audio(audio_path):
    transcript, whisper_segments = transcribe_with_timestamps(audio_path)

    diarization_turns = diarize_speakers(audio_path)
    speaker_segments = []
    labeled_transcript = None
    speaker_count = 0

    if diarization_turns:
        labeled = label_segments_with_speakers(whisper_segments, diarization_turns)
        speaker_segments = merge_consecutive_same_speaker(labeled)
        labeled_transcript = build_labeled_transcript_text(speaker_segments)
        speaker_count = len(set(s["speaker"] for s in speaker_segments))

    scam_kw = detect_scam_keywords(transcript)
    money_kw = detect_money_requests(transcript)
    otp_kw = detect_otp_requests(transcript)
    manipulation_kw = detect_emotional_manipulation(transcript)
    robocall_kw = detect_robocall_patterns(transcript)
    phone_numbers = extract_phone_numbers(transcript)
    is_repeated_script = detect_repeated_script(transcript)

    risk = calculate_audio_risk(
        scam_kw, money_kw, otp_kw, manipulation_kw, robocall_kw, phone_numbers, is_repeated_script
    )

    ai_verified = False
    if is_borderline(risk["score"]) and transcript.strip():
        content_for_ai = labeled_transcript or transcript
        ai_result = get_ai_verdict("Audio call transcript", content_for_ai, risk["score"], risk["reasons"])
        final_score, final_reasons = combine_rule_and_ai(risk["score"], risk["reasons"], ai_result)
        if ai_result.get("ai_available"):
            ai_verified = True
            risk["score"] = final_score
            risk["reasons"] = final_reasons
            risk["level"] = "High Risk" if final_score >= 70 else "Medium Risk" if final_score >= 40 else "Low Risk"

    risk["ai_verified"] = ai_verified

    return {
        "transcript": transcript,
        "labeled_transcript": labeled_transcript,
        "speaker_segments": speaker_segments,
        "speaker_count": speaker_count,
        "scam_keywords_found": scam_kw,
        "money_request_keywords": money_kw,
        "otp_keywords": otp_kw,
        "manipulation_keywords": manipulation_kw,
        "robocall_keywords_found": robocall_kw,
        "phone_numbers_found": phone_numbers,
        "is_repeated_script": is_repeated_script,
        "risk_assessment": risk
    }