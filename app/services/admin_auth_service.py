"""
Admin authentication business logic: login, logout, session.
Uses separate Admins table and session keys.
"""
from werkzeug.security import check_password_hash

from app.services.database_service import (
    get_db,
    find_admin_by_email,
    find_admin_by_id,
)
from app.services.validation import validate_login


class AdminAuthService:
    """Admin auth operations; isolated from normal user auth."""

    def __init__(self, app):
        self.app = app
        self.db = get_db(app)

    def login(self, data):
        """Validate admin credentials. Returns (success, message, admin_dict)."""
        v = validate_login(data)
        if not v["valid"]:
            return False, v["error"], None
        email = (data.get("email") or "").strip().lower()
        password = data.get("password")

        admin = find_admin_by_email(self.db, email)
        if not admin or not check_password_hash(admin.get("password", ""), password):
            return False, "Invalid email or password.", None

        admin_sess = {
            "admin_id": admin.get("id"),
            "admin_name": admin.get("name", ""),
            "admin_email": admin.get("email", ""),
        }
        return True, "Admin login successful.", admin_sess

    def get_current_admin(self, session_dict):
        """Return current admin from session; None if not logged in."""
        admin_id = session_dict.get("admin_id")
        if not admin_id:
            return None
        return find_admin_by_id(self.db, admin_id)

