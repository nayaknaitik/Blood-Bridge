"""
Auth API: register, login, logout, session, choose-role.
All responses JSON.
"""
from flask import Blueprint, request, jsonify, session, current_app

from app.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)


def json_response(success, message, data=None, status_code=200):
    out = {"success": success, "message": message}
    if data is not None:
        out["data"] = data
    return jsonify(out), status_code


def require_session(f):
    """Decorator: require user_id in session; return 401 JSON if not."""
    from functools import wraps

    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return json_response(False, "Authentication required.", None, 401)
        return f(*args, **kwargs)

    return wrapped


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or request.form.to_dict()
    auth = AuthService(current_app)
    success, message, data_out = auth.register(data)
    if not success:
        return json_response(False, message, None, 400)
    return json_response(True, message, data_out, 201)


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or request.form.to_dict()
    auth = AuthService(current_app)
    success, message, data_out = auth.login(data)
    if not success:
        return json_response(False, message, None, 401)
    # Set session
    sess = data_out.get("session", {})
    session["user_id"] = sess.get("user_id")
    session["name"] = sess.get("name", "")
    session["user_email"] = sess.get("user_email", "")
    session["role"] = sess.get("role")
    session["current_role"] = sess.get("current_role")
    return json_response(True, message, {"user": data_out})


@auth_bp.route("/logout", methods=["POST", "GET"])
def logout():
    session.clear()
    return json_response(True, "Logged out.", None)


@auth_bp.route("/session", methods=["GET"])
def get_session():
    if "user_id" not in session:
        return json_response(False, "Not authenticated.", None, 401)
    data = {
        "user_id": session.get("user_id"),
        "name": session.get("name"),
        "user_email": session.get("user_email"),
        "role": session.get("role"),
        "current_role": session.get("current_role"),
    }
    return json_response(True, "OK", data)


@auth_bp.route("/choose-role", methods=["POST"])
@require_session
def choose_role():
    data = request.get_json(silent=True) or request.form.to_dict()
    auth = AuthService(current_app)
    success, message, *rest = auth.choose_role(session["user_id"], data)
    if not success:
        return json_response(False, message, None, 400)
    data_out = rest[0] if rest else None
    if data_out:
        session["current_role"] = data_out.get("current_role")
    return json_response(True, message, data_out)
