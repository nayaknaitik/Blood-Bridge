"""
Admin auth API: login, logout, session.
Uses separate Admins table and admin_* session keys.
"""
from flask import Blueprint, request, jsonify, session, current_app

from app.services.admin_auth_service import AdminAuthService

admin_auth_bp = Blueprint("admin_auth", __name__)


def json_response(success, message, data=None, status_code=200):
    out = {"success": success, "message": message}
    if data is not None:
        out["data"] = data
    return jsonify(out), status_code


def require_admin_session(f):
    """Decorator: require admin_id in session."""
    from functools import wraps

    @wraps(f)
    def wrapped(*args, **kwargs):
        if "admin_id" not in session:
            return json_response(False, "Admin authentication required.", None, 401)
        return f(*args, **kwargs)

    return wrapped


@admin_auth_bp.route("/login", methods=["POST"])
def admin_login():
    data = request.get_json(silent=True) or request.form.to_dict()
    auth = AdminAuthService(current_app)
    success, message, admin_sess = auth.login(data)
    if not success:
        return json_response(False, message, None, 401)
    # Set admin-only session keys
    session["admin_id"] = admin_sess.get("admin_id")
    session["admin_name"] = admin_sess.get("admin_name", "")
    session["admin_email"] = admin_sess.get("admin_email", "")
    return json_response(True, message, {"admin": admin_sess})


@admin_auth_bp.route("/logout", methods=["POST"])
def admin_logout():
    # Clear only admin-related keys; leave user session intact
    for key in ["admin_id", "admin_name", "admin_email"]:
        session.pop(key, None)
    return json_response(True, "Admin logged out.", None)


@admin_auth_bp.route("/session", methods=["GET"])
def admin_session():
    if "admin_id" not in session:
        return json_response(False, "Not authenticated as admin.", None, 401)
    data = {
        "admin_id": session.get("admin_id"),
        "admin_name": session.get("admin_name"),
        "admin_email": session.get("admin_email"),
    }
    return json_response(True, "OK", data)

