"""
Page routes: serve HTML shells only. No business logic; data loaded via fetch in frontend.
"""
from flask import Blueprint, render_template, redirect, session, url_for

pages_bp = Blueprint("pages", __name__)


def _logged_in():
    return "user_id" in session


def _require_login(f):
    from functools import wraps

    @wraps(f)
    def wrapped(*args, **kwargs):
        if not _logged_in():
            return redirect(url_for("pages.login"))
        return f(*args, **kwargs)

    return wrapped


@pages_bp.route("/")
def index():
    return render_template("index.html")


@pages_bp.route("/login")
def login():
    return render_template("login.html")


@pages_bp.route("/register")
def register():
    return render_template("register.html")


@pages_bp.route("/signup")
def signup():
    """Alias for register."""
    return redirect(url_for("pages.register"))


@pages_bp.route("/choose_role")
@_require_login
def choose_role():
    return render_template("choose_role.html")


@pages_bp.route("/dashboard")
@_require_login
def dashboard():
    return render_template("dashboard.html")


@pages_bp.route("/request_blood")
@_require_login
def request_blood():
    return render_template("request_blood.html")


@pages_bp.route("/schedule_donation")
@_require_login
def schedule_donation():
    return render_template("schedule_donation.html")


@pages_bp.route("/view_requests")
@_require_login
def view_requests():
    return render_template("view_requests_for_donors.html")


@pages_bp.route("/admin/login")
def admin_login():
    """Admin login page (separate from user login)."""
    return render_template("admin/admin_login.html")


@pages_bp.route("/admin/dashboard")
def admin_dashboard():
    """Admin dashboard shell; data loaded via admin JS."""
    if "admin_id" not in session:
        return redirect(url_for("pages.admin_login"))
    return render_template("admin/admin_dashboard.html")


@pages_bp.route("/contact")
def contact():
    return render_template("contact.html")


@pages_bp.route("/about")
def about():
    return render_template("about.html")


@pages_bp.route("/logout")
def logout():
    """Clear session and redirect to home. Nav links here."""
    session.clear()
    return redirect(url_for("pages.index"))
