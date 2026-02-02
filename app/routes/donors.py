"""
Donors API: my-donations, schedule donation.
All responses JSON.
"""
from flask import Blueprint, request, jsonify, session, current_app

from app.services.database_service import (
    get_db,
    create_donation,
    get_donations_by_donor,
)
from app.services.validation import validate_donation_slot
from app.models.donor import Donation

donors_bp = Blueprint("donors", __name__)


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


@donors_bp.route("/my-donations", methods=["GET"])
@require_session
def my_donations():
    db = get_db(current_app)
    docs = get_donations_by_donor(db, session["user_id"])
    return json_response(True, "OK", {"donations": Donation.list_serializable(docs)})


@donors_bp.route("/schedule", methods=["POST"])
@require_session
def schedule():
    data = request.get_json(silent=True) or request.form.to_dict()
    v = validate_donation_slot(data)
    if not v["valid"]:
        return json_response(False, v["error"], None, 400)
    db = get_db(current_app)
    blood_group = (data.get("blood_group") or "").strip()
    donation_date = (data.get("donation_date") or data.get("date") or "").strip()
    location = (data.get("location") or "").strip()
    time_slot = (data.get("time_slot") or "").strip()
    donation_id = create_donation(
        db,
        session["user_id"],
        session.get("name", ""),
        blood_group,
        donation_date,
        location,
        time_slot,
        status="Scheduled",
    )
    return json_response(
        True,
        "Success! Your donation slot has been scheduled.",
        {"donation_id": donation_id},
        201,
    )
