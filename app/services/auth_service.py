"""
Authentication business logic: login, register, session.
"""
from werkzeug.security import generate_password_hash, check_password_hash

from app.services.database_service import (
    find_user_by_email,
    create_user,
    find_user_by_id,
    update_user_current_role,
    find_admin_by_email,
    create_admin,
    get_db,
)
from app.services.validation import validate_registration, validate_login, validate_choose_role


class AuthService:
    """Auth operations; requires Flask app for DB and session."""

    def __init__(self, app):
        self.app = app
        self.db = get_db(app)

    def register(self, data):
        """Register new user. Returns (success, message, data)."""
        v = validate_registration(data)
        if not v["valid"]:
            return False, v["error"], None
        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = data.get("password")
        blood_group = (data.get("blood_group") or "").strip() or None
         # Admin registration via special code
        admin_code = (data.get("admin_code") or "").strip()
        is_admin = admin_code == "1234"

        if is_admin:
            # Ensure no existing admin with this email
            if find_admin_by_email(self.db, email):
                return False, "An admin account with this email already exists.", None
            hashed = generate_password_hash(password)
            admin_id = create_admin(self.db, name, email, hashed)
            return True, "Admin registration successful. Please login via the admin portal.", {
                "admin_id": admin_id,
                "is_admin": True,
            }
        else:
            # Normal user registration
            if find_user_by_email(self.db, email):
                return False, "An account with this email already exists.", None
            hashed = generate_password_hash(password)
            user_id = create_user(self.db, name, email, hashed, blood_group=blood_group)
            return True, "Registration successful.", {"user_id": user_id, "is_admin": False}

    def login(self, data):
        """Validate credentials and return user info for session. Returns (success, message, user_dict)."""
        v = validate_login(data)
        if not v["valid"]:
            return False, v["error"], None
        email = (data.get("email") or "").strip().lower()
        password = data.get("password")

        user = find_user_by_email(self.db, email)
        if not user or not check_password_hash(user.get("password", ""), password):
            return False, "Invalid email or password.", None

        from app.models.user import User
        out = User.to_serializable(user)
        out["session"] = {
            "user_id": str(user.get("id") or user.get("_id", "")),
            "name": user.get("name", ""),
            "user_email": user.get("email", ""),
            "role": user.get("role"),
            "current_role": user.get("current_role"),
        }
        return True, "Login successful.", out

    def choose_role(self, user_id, data):
        """Set current_role for user. Returns (success, message)."""
        v = validate_choose_role(data)
        if not v["valid"]:
            return False, v["error"]
        role = (data.get("role_choice") or data.get("role") or "").strip().lower()
        user = find_user_by_id(self.db, user_id)
        if not user:
            return False, "User not found."
        if user.get("role") in ["admin", "bloodbank"]:
            return True, "Role unchanged (special account)."
        update_user_current_role(self.db, user_id, role)
        return True, "Role updated.", {"current_role": role}

    def get_current_user(self, session_dict):
        """Return current user doc from session; None if not logged in."""
        user_id = session_dict.get("user_id")
        if not user_id:
            return None
        return find_user_by_id(self.db, user_id)
