"""
Matching / dashboard API: inventory, dashboard payload by role (donor, recipient, bloodbank).
All responses JSON.
"""
from datetime import datetime
from flask import Blueprint, jsonify, session, current_app

from app.services.database_service import (
    get_db,
    find_user_by_id,
    get_donations_by_donor,
    get_recent_donations_for_bloodbank,
    get_all_donations_sorted,
    get_blood_requests_by_requester,
    get_pending_blood_requests,
    get_all_blood_requests_sorted,
    list_all_users,
    enrich_users_with_blood_group,
    count_donations_by_blood_group_and_status,
    count_donors_distinct,
    count_blood_requests_by_status,
    count_recipients_distinct,
    count_donations_by_date,
    count_users_by_role,
)
from app.services.matching_service import MatchingService
from app.models.donor import Donation
from app.models.request import BloodRequest
from app.models.user import User
from config import BLOOD_GROUPS

matching_bp = Blueprint("matching", __name__)


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


@matching_bp.route("/inventory", methods=["GET"])
def inventory():
    matching = MatchingService(current_app)
    inv = matching.get_inventory()
    return json_response(True, "OK", {"inventory": inv})


@matching_bp.route("/dashboard", methods=["GET"])
@require_session
def dashboard():
    """Return dashboard payload for current user by role."""
    db = get_db(current_app)
    user = find_user_by_id(db, session["user_id"])
    if not user:
        session.clear()
        return json_response(False, "User not found.", None, 401)

    role = user.get("role")
    current_role = user.get("current_role") or session.get("current_role")

    # Normal users: donor or recipient
    if role not in ["bloodbank"]:
        if current_role == "donor":
            docs = get_donations_by_donor(db, session["user_id"])
            return json_response(
                True,
                "OK",
                {"view": "donor", "donations": Donation.list_serializable(docs)},
            )
        if current_role == "recipient":
            matching = MatchingService(current_app)
            requests_with_avail = matching.get_recipient_requests_with_availability(session["user_id"])
            inventory_dict = matching.get_inventory()
            return json_response(
                True,
                "OK",
                {
                    "view": "recipient",
                    "requests": requests_with_avail,
                    "inventory": inventory_dict,
                },
            )
        return json_response(True, "Choose role", {"view": "choose_role"}, 200)

    # Blood bank
    if role == "bloodbank":
        today_str = datetime.now().strftime("%Y-%m-%d")
        inv_counts = count_donations_by_blood_group_and_status(
            db, blood_groups=BLOOD_GROUPS, statuses=["Scheduled", "Completed"]
        )
        inventory_list = [{"group": bg, "units": inv_counts.get(bg, 0)} for bg in BLOOD_GROUPS]
        total_units = sum(inv_counts.values())
        recent_donors_raw = get_recent_donations_for_bloodbank(db, 5)
        donors = [
            {"name": d.get("donor_name", "Unknown"), "blood_group": d.get("blood_group", "N/A"), "last_donation": d.get("date", "N/A")}
            for d in recent_donors_raw
        ]
        recent_requests = get_pending_blood_requests(db, limit=10)
        stats = {
            "total_donors": count_donors_distinct(db),
            "pending_requests": count_blood_requests_by_status(db, "pending"),
            "total_units": total_units,
            "today_donations": count_donations_by_date(db, today_str),
        }
        return json_response(
            True,
            "OK",
            {
                "view": "bloodbank",
                "stats": stats,
                "donors": donors,
                "inventory": inventory_list,
                "requests": BloodRequest.list_serializable(recent_requests),
                "today": datetime.now().strftime("%d %b %Y"),
            },
        )

    # Admin dashboard is now fully separate under /api/admin, so matching.dashboard
    # should never be used for admin accounts.
    return json_response(False, "Invalid role for user dashboard.", None, 400)
