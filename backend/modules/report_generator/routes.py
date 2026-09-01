from flask import Blueprint, request, jsonify, send_file
import datetime
import os
from .generator import generate_case_id, build_pdf_report
from .db import cases_collection

report_bp = Blueprint("report", __name__)


@report_bp.route("/generate", methods=["POST"])
def generate_report():
    data = request.get_json()

    combined_result = data.get("combined_result")
    evidence_details = data.get("evidence_details", [])
    screenshot_image_path = data.get("screenshot_image_path")  # optional, filename saved on server

    if not combined_result:
        return jsonify({"error": "combined_result is required"}), 400

    case_id = generate_case_id()
    created_at = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Resolve full path if a screenshot filename was passed
    full_image_path = None
    if screenshot_image_path:
        upload_folder = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads"
        )
        full_image_path = os.path.join(upload_folder, screenshot_image_path)

    try:
        pdf_path = build_pdf_report(case_id, created_at, combined_result, evidence_details, full_image_path)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Save case record in MongoDB
    cases_collection.insert_one({
        "case_id": case_id,
        "created_at": created_at,
        "combined_result": combined_result,
        "evidence_details": evidence_details,
        "pdf_path": pdf_path
    })

    return jsonify({
        "case_id": case_id,
        "created_at": created_at,
        "download_url": f"/api/report/download/{case_id}"
    }), 200


@report_bp.route("/download/<case_id>", methods=["GET"])
def download_report(case_id):
    case = cases_collection.find_one({"case_id": case_id})
    if not case:
        return jsonify({"error": "Case not found"}), 404

    pdf_path = case.get("pdf_path")
    if not pdf_path or not os.path.exists(pdf_path):
        return jsonify({"error": "Report file not found"}), 404

    return send_file(pdf_path, as_attachment=True, download_name=f"{case_id}.pdf")


@report_bp.route("/history", methods=["GET"])
def get_history():
    cases = list(cases_collection.find({}, {"_id": 0, "evidence_details": 0}).sort("created_at", -1))
    return jsonify(cases), 200