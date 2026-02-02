"""
Admin-facing business logic: dashboard stats, users, requests, donations, inventory.
"""
from datetime import datetime

from config import BLOOD_GROUPS
from app.services.database_service import (
    get_db,
    list_all_users,
    enrich_users_with_blood_group,
    get_all_blood_requests_sorted,
    get_all_donations_sorted,
    count_donors_distinct,
    count_recipients_distinct,
    count_users_by_role,
    count_blood_requests_by_status,
    count_donations_by_blood_group_and_status,
    count_donations_by_date,
    delete_user_by_id,
    find_user_by_id,
)
from app.models.user import User
from app.models.donor import Donation
from app.models.request import BloodRequest


class AdminService:
    """Service providing admin-only views and aggregations."""

    def __init__(self, app):
        self.app = app
        self.db = get_db(app)

    # ----- Dashboard -----
    def get_dashboard_stats(self):
        """Aggregated system stats for admin dashboard."""
        db = self.db
        users = list_all_users(db)
        users = enrich_users_with_blood_group(db, users)
        blood_requests = get_all_blood_requests_sorted(db, sort_timestamp=-1)
        all_donations = get_all_donations_sorted(db, sort_timestamp=-1)

        inv_counts = count_donations_by_blood_group_and_status(
            db, blood_groups=BLOOD_GROUPS, statuses=["Scheduled", "Completed"]
        )
        inventory_list = [{"group": bg, "units": inv_counts.get(bg, 0)} for bg in BLOOD_GROUPS]
        today_str = datetime.now().strftime("%Y-%m-%d")

        stats = {
            "total_users": len(users),
            "donors_count": count_donors_distinct(db),
            "recipients_count": count_recipients_distinct(db),
            "banks_count": count_users_by_role(db, "bloodbank"),
            "total_requests": len(blood_requests),
            "pending_requests": count_blood_requests_by_status(db, "pending"),
            "completed_requests": count_blood_requests_by_status(db, "fulfilled"),
            "total_donations": len(all_donations),
            "today_donations": count_donations_by_date(db, today_str),
            "total_inventory": sum(inv_counts.values()),
        }

        return {
            "stats": stats,
            "inventory": inventory_list,
        }

    # ----- Users -----
    def list_users(self):
        users = list_all_users(self.db)
        users = enrich_users_with_blood_group(self.db, users)
        return [User.to_serializable(u) for u in users]

    def delete_user(self, user_id):
        if not find_user_by_id(self.db, user_id):
            return False, "User not found."
        delete_user_by_id(self.db, user_id)
        return True, "User removed successfully."

    # ----- Requests -----
    def list_requests(self):
        reqs = get_all_blood_requests_sorted(self.db, sort_timestamp=-1)
        return BloodRequest.list_serializable(reqs)

    # ----- Donations -----
    def list_donations(self, limit=None):
        donations = get_all_donations_sorted(self.db, sort_timestamp=-1, limit=limit)
        return Donation.list_serializable(donations)

    # ----- Inventory -----
    def get_inventory(self):
        db = self.db
        inv_counts = count_donations_by_blood_group_and_status(
            db, blood_groups=BLOOD_GROUPS, statuses=["Scheduled", "Completed"]
        )
        return [{"group": bg, "units": inv_counts.get(bg, 0)} for bg in BLOOD_GROUPS]

