"""
Admin-only APIs: dashboard, users, requests, donations, inventory, user delete.
Protected by admin session (admin_id in session).
"""
from flask import Blueprint, jsonify, session, current_app

from app.routes.admin_auth import require_admin_session
from app.services.admin_service import AdminService

admin_bp = Blueprint("admin", __name__)


def json_response(success, message, data=None, status_code=200):
    out = {"success": success, "message": message}
    if data is not None:
        out["data"] = data
    return jsonify(out), status_code


def admin_required(f):
    """Alias for require_admin_session for readability in this module."""
    return require_admin_session(f)


@admin_bp.route("/dashboard", methods=["GET"])
@admin_required
def dashboard():
    svc = AdminService(current_app)
    payload = svc.get_dashboard_stats()
    return json_response(True, "OK", payload)


@admin_bp.route("/users", methods=["GET"])
@admin_required
def users():
    svc = AdminService(current_app)
    data = {"users": svc.list_users()}
    return json_response(True, "OK", data)


@admin_bp.route("/users/<user_id>/delete", methods=["POST", "DELETE"])
@admin_required
def delete_user(user_id):
    svc = AdminService(current_app)
    success, message = svc.delete_user(user_id)
    status = 200 if success else 404
    return json_response(success, message, None, status)


@admin_bp.route("/requests", methods=["GET"])
@admin_required
def requests():
    svc = AdminService(current_app)
    data = {"requests": svc.list_requests()}
    return json_response(True, "OK", data)


@admin_bp.route("/donations", methods=["GET"])
@admin_required
def donations():
    svc = AdminService(current_app)
    data = {"donations": svc.list_donations()}
    return json_response(True, "OK", data)


@admin_bp.route("/inventory", methods=["GET"])
@admin_required
def inventory():
    svc = AdminService(current_app)
    data = {"inventory": svc.get_inventory()}
    return json_response(True, "OK", data)

