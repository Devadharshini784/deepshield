import re
import tldextract
import validators
from bs4 import BeautifulSoup
from modules.shared.ai_verifier import is_borderline, get_ai_verdict, combine_rule_and_ai

# Trusted domains that scammers commonly impersonate
COMMONLY_IMPERSONATED = [
    "paypal", "amazon", "google", "microsoft", "apple", "netflix",
    "bank", "facebook", "instagram", "whatsapp", "government"
]

URGENT_PHRASES = [
    "urgent action required", "verify your account", "account suspended",
    "click here immediately", "limited time offer", "your account will be closed",
    "confirm your identity", "unusual activity detected", "update your payment",
    "you have won", "claim your reward", "act now", "final notice"
]

GRAMMAR_RED_FLAGS = [
    "dear valued customer", "dear user", "dear sir/madam", "kindly revert",
    "do the needful", "please to inform you"
]


def extract_urls(email_body):
    url_pattern = re.compile(r'(https?://[^\s<>"\']+)')
    urls = url_pattern.findall(email_body)
    return list(set(urls))


def inspect_urls(urls):
    findings = []
    for url in urls:
        if not validators.url(url):
            continue
        extracted = tldextract.extract(url)
        domain = f"{extracted.domain}.{extracted.suffix}"

        entry = {"url": url, "domain": domain, "suspicious": False, "reason": ""}

        # Check for IP address used instead of domain
        if re.match(r'^https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url):
            entry["suspicious"] = True
            entry["reason"] = "URL uses raw IP address instead of a domain name"

        # Check for impersonation of trusted brands in subdomain/domain tricks
        for brand in COMMONLY_IMPERSONATED:
            if brand in extracted.subdomain.lower() and brand not in extracted.domain.lower():
                entry["suspicious"] = True
                entry["reason"] = f"Domain tries to impersonate '{brand}' using a subdomain trick"

        # Check for excessive hyphens/misspelled lookalike domains
        if extracted.domain.count("-") >= 2:
            entry["suspicious"] = True
            entry["reason"] = "Domain contains multiple hyphens, common in fake lookalike domains"

        # Check for suspicious/uncommon TLDs often used in scams
        risky_tlds = ["xyz", "top", "click", "info", "loan", "win", "tk"]
        if extracted.suffix in risky_tlds:
            entry["suspicious"] = True
            entry["reason"] = f"Uses uncommon top-level domain '.{extracted.suffix}' often seen in scam links"

        findings.append(entry)
    return findings


def analyze_sender(sender_email, display_name=""):
    findings = []

    if not sender_email or "@" not in sender_email:
        findings.append("Sender email format is invalid or missing")
        return findings

    domain_part = sender_email.split("@")[1].lower()
    extracted = tldextract.extract(domain_part)

    for brand in COMMONLY_IMPERSONATED:
        if brand in display_name.lower() and brand not in extracted.domain.lower():
            findings.append(f"Display name mentions '{brand}' but sending domain doesn't match")

    free_domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"]
    if any(brand in display_name.lower() for brand in COMMONLY_IMPERSONATED) and domain_part in free_domains:
        findings.append("Claims to be a company/bank but sent from a free public email domain")

    return findings


def analyze_content(email_body):
    findings = []
    text_lower = email_body.lower()

    for phrase in URGENT_PHRASES:
        if phrase in text_lower:
            findings.append(f"Urgency/pressure phrase detected: '{phrase}'")

    for phrase in GRAMMAR_RED_FLAGS:
        if phrase in text_lower:
            findings.append(f"Generic/awkward greeting pattern detected: '{phrase}'")

    if text_lower.count("!") > 5:
        findings.append("Excessive use of exclamation marks, common in scam emails")

    return findings


def calculate_email_risk(sender_findings, content_findings, url_findings):
    score = 0
    reasons = []

    for f in sender_findings:
        score += 20
        reasons.append(f)

    for f in content_findings:
        score += 10
        reasons.append(f)

    suspicious_url_count = 0
    for u in url_findings:
        if u["suspicious"]:
            score += 20
            reasons.append(f"Suspicious URL ({u['url']}): {u['reason']}")
            suspicious_url_count += 1

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
        "reasons": reasons if reasons else ["No strong phishing indicators found"]
    }


def analyze_email(sender_email, display_name, subject, body):
    soup = BeautifulSoup(body, "html.parser")
    clean_text = soup.get_text()

    urls = extract_urls(body)
    url_findings = inspect_urls(urls)
    sender_findings = analyze_sender(sender_email, display_name)
    content_findings = analyze_content(clean_text + " " + subject)

    risk = calculate_email_risk(sender_findings, content_findings, url_findings)

    ai_verified = False
    if is_borderline(risk["score"]):
        full_context = f"From: {display_name} <{sender_email}>\nSubject: {subject}\n\n{clean_text}"
        ai_result = get_ai_verdict("Email", full_context, risk["score"], risk["reasons"])
        final_score, final_reasons = combine_rule_and_ai(risk["score"], risk["reasons"], ai_result)
        if ai_result.get("ai_available"):
            ai_verified = True
            risk["score"] = final_score
            risk["reasons"] = final_reasons
            if final_score >= 70:
                risk["level"] = "High Risk"
            elif final_score >= 40:
                risk["level"] = "Medium Risk"
            else:
                risk["level"] = "Low Risk"

    risk["ai_verified"] = ai_verified

    return {
        "sender_email": sender_email,
        "subject": subject,
        "urls_found": url_findings,
        "sender_findings": sender_findings,
        "content_findings": content_findings,
        "risk_assessment": risk
    }