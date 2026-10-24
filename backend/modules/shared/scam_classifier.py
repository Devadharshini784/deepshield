import os
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "models", "scam_classifier"
)

_tokenizer = None
_model = None
_model_available = False

print("Loading trained scam classifier...")
try:
    if os.path.exists(MODEL_DIR):
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
        _model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
        _model.eval()
        _model_available = True
        print("Scam classifier loaded.")
    else:
        print(f"No trained model found at {MODEL_DIR}, classifier will be skipped.")
except Exception as e:
    print(f"Could not load scam classifier: {e}")


def is_model_available():
    return _model_available


def classify_text(text):
    """
    Returns {"score": 0-100, "confidence": 0-1, "available": bool}
    Score is the model's probability that the text is a scam, scaled to 0-100.
    """
    if not _model_available or not text or not text.strip():
        return {"score": 0, "confidence": 0.0, "available": False}

    try:
        inputs = _tokenizer(text, truncation=True, padding=True, max_length=256, return_tensors="pt")
        with torch.no_grad():
            logits = _model(**inputs).logits
        probs = torch.softmax(logits, dim=1)[0]
        scam_prob = float(probs[1])
        return {
            "score": round(scam_prob * 100),
            "confidence": round(float(torch.max(probs)), 3),
            "available": True
        }
    except Exception as e:
        print(f"Classification failed: {e}")
        return {"score": 0, "confidence": 0.0, "available": False}


def blend_with_rules(rule_score, rule_reasons, model_result):
    """
    Blends the rule-based score with the trained model's prediction.
    The model gets slightly more weight since it generalizes to wording
    the keyword lists were never written for.
    """
    if not model_result.get("available"):
        return rule_score, rule_reasons, False

    model_score = model_result["score"]
    final_score = round((rule_score * 0.45) + (model_score * 0.55))

    reasons = list(rule_reasons)
    reasons.append(
        f"Trained scam-language model rated this {model_score}/100 "
        f"(confidence {model_result['confidence']})"
    )
    return final_score, reasons, True