from flask import Blueprint, request, jsonify
import os
from werkzeug.utils import secure_filename
from .analyzer import analyze_screenshot

screenshot_bp = Blueprint("screenshot", __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@screenshot_bp.route("/upload", methods=["POST"])
def upload_screenshot():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only png, jpg, jpeg files are allowed"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        result = analyze_screenshot(filepath)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500