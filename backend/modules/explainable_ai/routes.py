from flask import Blueprint, request, jsonify
from .analyzer import combine_evidence

explain_bp = Blueprint("explain", __name__)


@explain_bp.route("/combine", methods=["POST"])
def combine():
    data = request.get_json()
    evidence_results = data.get("evidence_results", [])

    if not isinstance(evidence_results, list):
        return jsonify({"error": "evidence_results must be a list"}), 400

    try:
        result = combine_evidence(evidence_results)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500