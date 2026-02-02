"""
Blood Bridge application configuration.
Load from environment; defaults for development.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _get_env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip() or default


# Flask
SECRET_KEY = _get_env("SECRET_KEY", "blood-bridge-dev-secret-change-in-production")
SESSION_COOKIE_SECURE = _get_env("FLASK_ENV") == "production"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# DynamoDB (AWS)
AWS_REGION = _get_env("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = _get_env("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = _get_env("AWS_SECRET_ACCESS_KEY", "")

# Table names (create these in DynamoDB)
USERS_TABLE = _get_env("USERS_TABLE", "bloodbridge-users")
DONATIONS_TABLE = _get_env("DONATIONS_TABLE", "bloodbridge-donations")
BLOOD_REQUESTS_TABLE = _get_env("BLOOD_REQUESTS_TABLE", "bloodbridge-blood-requests")
MESSAGES_TABLE = _get_env("MESSAGES_TABLE", "bloodbridge-messages")
ADMINS_TABLE = _get_env("ADMINS_TABLE", "bloodbridge-admins")

# App
DEBUG = _get_env("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Blood groups (canonical list)
BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

# Donation statuses
DONATION_STATUSES = ["Scheduled", "Completed", "Cancelled"]
REQUEST_STATUSES = ["pending", "fulfilled", "cancelled"]

# Roles
ROLES = ["donor", "recipient", "bloodbank", "admin"]
USER_CHOOSABLE_ROLES = ["donor", "recipient"]
