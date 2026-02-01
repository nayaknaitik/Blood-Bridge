"""
Health / utility API: health check, contact form.
"""
from flask import Blueprint, jsonify, request, current_app

from app.services.database_service import get_db, create_contact_message
from app.services.validation import validate_contact

health_bp = Blueprint("health", __name__)


def json_response(success, message, data=None, status_code=200):
    out = {"success": success, "message": message}
    if data is not None:
        out["data"] = data
    return jsonify(out), status_code


@health_bp.route("/health", methods=["GET"])
def health():
    from app.services.dynamodb_client import dynamodb_health_check
    db_ok = dynamodb_health_check(current_app)
    return jsonify({
        "success": True,
        "message": "OK",
        "data": {"database": "ok" if db_ok else "error"},
    }), 200 if db_ok else 503


@health_bp.route("/contact", methods=["POST"])
def contact():
    data = request.get_json(silent=True) or request.form.to_dict()
    v = validate_contact(data)
    if not v["valid"]:
        return json_response(False, v["error"], None, 400)
    db = get_db(current_app)
    create_contact_message(
        db,
        (data.get("name") or "").strip(),
        (data.get("email") or "").strip().lower(),
        (data.get("subject") or "").strip(),
        (data.get("message") or "").strip(),
    )
    return json_response(True, "Thank you! Your message has been sent successfully.", None, 201)
