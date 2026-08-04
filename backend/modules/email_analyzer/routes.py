from flask import Blueprint, request, jsonify
from .analyzer import analyze_email

email_bp = Blueprint("email", __name__)


@email_bp.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()

    sender_email = data.get("sender_email", "")
    display_name = data.get("display_name", "")
    subject = data.get("subject", "")
    body = data.get("body", "")

    if not body:
        return jsonify({"error": "Email body is required"}), 400

    try:
        result = analyze_email(sender_email, display_name, subject, body)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500