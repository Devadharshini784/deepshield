# This module combines results from Screenshot, Email, and Audio analyzers
# into one unified, human-readable risk verdict.

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


def get_confidence_level(evidence_count, total_reasons):
    """
    Confidence grows with more evidence types analyzed together
    and more concrete reasons found.
    """
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
    """
    evidence_results: list of dicts like:
      {"type": "Screenshot", "score": 80, "reasons": [...]}
    """
    lines = []

    if overall_level == "High Risk":
        lines.append(
            "Multiple strong indicators point to this being a scam. "
            "The evidence shows patterns commonly used by fraudsters to pressure victims into "
            "sharing money or sensitive information."
        )
    elif overall_level == "Medium Risk":
        lines.append(
            "Some suspicious patterns were found. This doesn't confirm a scam, but there are "
            "enough warning signs that you should verify independently before taking any action."
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
            top_reasons = reasons[:3]
            lines.append(f"From the {etype} analysis: " + "; ".join(top_reasons) + ".")

    return " ".join(lines)


def combine_evidence(evidence_results):
    """
    evidence_results: list of dicts, each like:
      {"type": "Screenshot", "score": 80, "reasons": ["...", "..."]}
      {"type": "Email", "score": 60, "reasons": ["...", "..."]}
      {"type": "Audio", "score": 90, "reasons": ["...", "..."]}

    Returns a combined verdict.
    """
    if not evidence_results:
        return {
            "combined_score": 0,
            "overall_level": "Low Risk",
            "confidence": "Low",
            "explanation": "No evidence was provided for analysis.",
            "recommended_actions": RECOMMENDATIONS["Low Risk"]
        }

    scores = [e.get("score", 0) for e in evidence_results]
    combined_score = round(sum(scores) / len(scores))

    # If any single piece of evidence is very high risk, don't let averaging water it down too much
    max_score = max(scores)
    if max_score >= 80:
        combined_score = max(combined_score, 75)

    overall_level = determine_overall_level(combined_score)

    total_reasons = sum(len(e.get("reasons", [])) for e in evidence_results)
    confidence = get_confidence_level(len(evidence_results), total_reasons)

    explanation = generate_plain_explanation(evidence_results, overall_level)
    recommended_actions = RECOMMENDATIONS[overall_level]

    return {
        "combined_score": combined_score,
        "overall_level": overall_level,
        "confidence": confidence,
        "explanation": explanation,
        "recommended_actions": recommended_actions,
        "evidence_breakdown": evidence_results
    }