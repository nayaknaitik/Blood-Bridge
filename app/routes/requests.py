"""
Blood requests API: create, my requests, pending (for donors view), admin list.
All responses JSON.
"""
from flask import Blueprint, request, jsonify, session, current_app

from app.services.database_service import (
    get_db,
    create_blood_request,
    get_blood_requests_by_requester,
    get_pending_blood_requests,
    get_all_blood_requests_sorted,
)
from app.services.validation import validate_blood_request
from app.services.matching_service import MatchingService
from app.models.request import BloodRequest

requests_bp = Blueprint("requests", __name__)


def json_response(success, message, data=None, status_code=200):
    out = {"success": success, "message": message}
    if data is not None:
        out["data"] = data
    return jsonify(out), status_code


def require_session(f):
    from functools import wraps

    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return json_response(False, "Authentication required.", None, 401)
        return f(*args, **kwargs)

    return wrapped


def require_admin(f):
    from functools import wraps

    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return json_response(False, "Authentication required.", None, 401)
        if session.get("role") != "admin":
            return json_response(False, "Unauthorized.", None, 403)
        return f(*args, **kwargs)

    return wrapped


@requests_bp.route("", methods=["POST"])
@require_session
def create_request():
    data = request.get_json(silent=True) or request.form.to_dict()
    v = validate_blood_request(data)
    if not v["valid"]:
        return json_response(False, v["error"], None, 400)
    db = get_db(current_app)
    request_id = create_blood_request(
        db,
        session["user_id"],
        (data.get("patient_name") or "").strip(),
        (data.get("blood_group") or "").strip(),
        data.get("units"),
        (data.get("hospital") or "").strip(),
        status="pending",
    )
    return json_response(
        True,
        "Blood request has been posted successfully!",
        {"request_id": request_id},
        201,
    )


@requests_bp.route("/my", methods=["GET"])
@require_session
def my_requests():
    matching = MatchingService(current_app)
    requests_with_avail = matching.get_recipient_requests_with_availability(session["user_id"])
    inventory = matching.get_inventory()
    return json_response(
        True,
        "OK",
        {"requests": requests_with_avail, "inventory": inventory},
    )


@requests_bp.route("/pending", methods=["GET"])
@require_session
def pending():
    db = get_db(current_app)
    docs = get_pending_blood_requests(db)
    return json_response(True, "OK", {"requests": BloodRequest.list_serializable(docs)})


@requests_bp.route("/all", methods=["GET"])
@require_admin
def all_requests():
    db = get_db(current_app)
    docs = get_all_blood_requests_sorted(db, sort_timestamp=-1)
    return json_response(True, "OK", {"requests": BloodRequest.list_serializable(docs)})
