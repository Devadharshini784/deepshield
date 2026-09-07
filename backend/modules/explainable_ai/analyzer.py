import re
from datetime import datetime

RECOMMENDATIONS = {
    "High Risk": [
        "Do not click any links, scan any QR codes, or share OTP/PIN from this evidence",
        "Do not send money or share banking details related to this",
        "Block the sender/caller number or email address immediately",
        "Report this to the National Cyber Crime Reporting Portal (cybercrime.gov.in) or your local cybercrime cell",
        "Save this evidence and generate a report for your complaint"
    ],
    "Medium Risk": [
        "Verify the sender/caller through an official channel before taking any action",
        "Avoid clicking links or sharing personal/financial information until verified",
        "Cross-check with the official company/bank website or customer care number",
        "Keep this evidence saved in case it turns out to be a scam"
    ],
    "Low Risk": [
        "No immediate red flags found, but stay cautious with unexpected requests",
        "Still avoid sharing OTP, passwords, or banking details unless you're fully sure",
        "If anything about this still feels off, trust your instinct and verify independently"
    ]
}

AMOUNT_PATTERN = re.compile(
    r'(?:₹|rs\.?|inr)\s?([\d,]+(?:\.\d{1,2})?)|(\$|usd)\s?([\d,]+(?:\.\d{1,2})?)',
    re.IGNORECASE
)


def extract_amount(text):
    if not text:
        return None
    match = AMOUNT_PATTERN.search(text)
    if not match:
        return None
    raw = match.group(1) or match.group(3)
    if not raw:
        return None
    try:
        return float(raw.replace(",", ""))
    except ValueError:
        return None


def parse_timestamp(ts_string):
    if not ts_string:
        return None
    try:
        return datetime.fromisoformat(ts_string)
    except (ValueError, TypeError):
        return None


def check_time_window_consistency(evidence_results, window_hours=48):
    """
    Compares amounts mentioned across different evidence pieces that happened
    close together in time. A scammer often quotes different amounts across
    a screenshot, email, and call, since they're improvising - this catches that.
    """
    findings = []
    enriched = []

    for e in evidence_results:
        ts = parse_timestamp(e.get("timestamp"))
        amount = extract_amount(e.get("content", ""))
        if ts and amount is not None:
            enriched.append({"type": e.get("type", "Evidence"), "timestamp": ts, "amount": amount})

    for i in range(len(enriched)):
        for j in range(i + 1, len(enriched)):
            a, b = enriched[i], enriched[j]
            diff_hours = abs((a["timestamp"] - b["timestamp"]).total_seconds()) / 3600
            if diff_hours <= window_hours and abs(a["amount"] - b["amount"]) > 0.01:
                findings.append(
                    f"Amount mismatch within {round(diff_hours, 1)}h: {a['type']} references "
                    f"{a['amount']:,.2f} while {b['type']} references {b['amount']:,.2f} — "
                    f"scammers often change the claimed amount across different messages or calls"
                )

    return findings


def get_confidence_level(evidence_count, total_reasons):
    if evidence_count >= 2 and total_reasons >= 4:
        return "High"
    elif evidence_count >= 1 and total_reasons >= 2:
        return "Medium"
    else:
        return "Low"


def determine_overall_level(combined_score):
    if combined_score >= 70:
        return "High Risk"
    elif combined_score >= 40:
        return "Medium Risk"
    else:
        return "Low Risk"


def generate_plain_explanation(evidence_results, overall_level):
    lines = []

    if overall_level == "High Risk":
        lines.append(
            "Multiple strong indicators point to this being a scam. The evidence shows patterns "
            "commonly used by fraudsters to pressure victims into sharing money or sensitive information."
        )
    elif overall_level == "Medium Risk":
        lines.append(
            "Some suspicious patterns were found. This doesn't confirm a scam, but there are enough "
            "warning signs that you should verify independently before taking any action."
        )
    else:
        lines.append(
            "No strong scam indicators were detected in the evidence provided. However, absence of "
            "red flags does not guarantee full safety, always stay cautious."
        )

    for evidence in evidence_results:
        etype = evidence.get("type", "Evidence")
        reasons = evidence.get("reasons", [])
        if reasons:
            lines.append(f"From the {etype} analysis: " + "; ".join(reasons[:3]) + ".")

    return " ".join(lines)


def combine_evidence(evidence_results):
    if not evidence_results:
        return {
            "combined_score": 0,
            "overall_level": "Low Risk",
            "confidence": "Low",
            "explanation": "No evidence was provided for analysis.",
            "recommended_actions": RECOMMENDATIONS["Low Risk"],
            "time_window_findings": []
        }

    scores = [e.get("score", 0) for e in evidence_results]
    combined_score = round(sum(scores) / len(scores))

    max_score = max(scores)
    if max_score >= 80:
        combined_score = max(combined_score, 75)

    time_window_findings = check_time_window_consistency(evidence_results)
    if time_window_findings:
        combined_score = min(combined_score + 30 * len(time_window_findings), 100)

    overall_level = determine_overall_level(combined_score)

    total_reasons = sum(len(e.get("reasons", [])) for e in evidence_results) + len(time_window_findings)
    confidence = get_confidence_level(len(evidence_results), total_reasons)

    explanation = generate_plain_explanation(evidence_results, overall_level)
    if time_window_findings:
        explanation += " " + " ".join(time_window_findings)

    return {
        "combined_score": combined_score,
        "overall_level": overall_level,
        "confidence": confidence,
        "explanation": explanation,
        "recommended_actions": RECOMMENDATIONS[overall_level],
        "evidence_breakdown": evidence_results,
        "time_window_findings": time_window_findings
    }