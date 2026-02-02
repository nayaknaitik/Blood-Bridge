"""
All validation logic for Blood Bridge.
Used by routes and services; no validation in routes.
"""
import re
from config import BLOOD_GROUPS, USER_CHOOSABLE_ROLES


def _error(message):
    return {"valid": False, "error": message}


def _ok():
    return {"valid": True, "error": None}


def validate_email(email):
    if not email or not isinstance(email, str):
        return False
    email = email.strip().lower()
    if len(email) > 254:
        return False
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_registration(data):
    """Validate signup payload: name, email, password, blood_group (optional)."""
    if not data:
        return _error("Missing registration data")
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password")
    blood_group = (data.get("blood_group") or "").strip() or None

    if not name or len(name) < 2:
        return _error("Name must be at least 2 characters")
    if not email:
        return _error("Email is required")
    if not validate_email(email):
        return _error("Invalid email format")
    if not password or len(str(password)) < 6:
        return _error("Password must be at least 6 characters")
    if blood_group and blood_group not in BLOOD_GROUPS:
        return _error("Invalid blood group")

    return _ok()


def validate_login(data):
    """Validate login payload: email, password."""
    if not data:
        return _error("Missing login data")
    email = (data.get("email") or "").strip().lower()
    password = data.get("password")

    if not email:
        return _error("Email is required")
    if not validate_email(email):
        return _error("Invalid email format")
    if not password:
        return _error("Password is required")

    return _ok()


def validate_choose_role(data):
    """Validate role choice: role_choice in donor, recipient."""
    role = (data.get("role_choice") or data.get("role") or "").strip().lower()
    if role not in USER_CHOOSABLE_ROLES:
        return _error("Please choose donor or recipient")
    return _ok()


def validate_blood_request(data):
    """Validate blood request: patient_name, blood_group, units, hospital."""
    if not data:
        return _error("Missing request data")
    patient_name = (data.get("patient_name") or "").strip()
    blood_group = (data.get("blood_group") or "").strip()
    units = data.get("units")
    hospital = (data.get("hospital") or "").strip()

    if not patient_name or len(patient_name) < 2:
        return _error("Patient name must be at least 2 characters")
    if blood_group not in BLOOD_GROUPS:
        return _error("Invalid blood group")
    try:
        u = int(units)
        if u < 1 or u > 100:
            return _error("Units must be between 1 and 100")
    except (TypeError, ValueError):
        return _error("Units must be a number (1-100)")
    if not hospital or len(hospital) < 5:
        return _error("Hospital name/address must be at least 5 characters")

    return _ok()


def validate_donation_slot(data):
    """Validate donation slot: blood_group, donation_date, location, time_slot optional."""
    if not data:
        return _error("Missing donation data")
    blood_group = (data.get("blood_group") or "").strip()
    donation_date = (data.get("donation_date") or data.get("date") or "").strip()
    location = (data.get("location") or "").strip()
    time_slot = (data.get("time_slot") or "").strip()

    if not blood_group or blood_group not in BLOOD_GROUPS:
        return _error("Please select a valid blood group")
    if not donation_date:
        return _error("Donation date is required")
    if not location or len(location) < 2:
        return _error("Location is required")

    return _ok()


def validate_contact(data):
    """Validate contact form: name, email, subject, message."""
    if not data:
        return _error("Missing contact data")
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    subject = (data.get("subject") or "").strip()
    message = (data.get("message") or "").strip()

    if not name or len(name) < 2:
        return _error("Name must be at least 2 characters")
    if not email:
        return _error("Email is required")
    if not validate_email(email):
        return _error("Invalid email format")
    if not subject:
        return _error("Subject is required")
    if not message or len(message) < 10:
        return _error("Message must be at least 10 characters")

    return _ok()
