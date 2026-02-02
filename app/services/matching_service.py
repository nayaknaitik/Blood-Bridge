"""
Inventory and availability logic: inventory from donations, request availability.
"""
from datetime import datetime

from app.services.database_service import (
    get_db,
    count_donations_by_blood_group_and_status,
    get_blood_requests_by_requester,
    BLOOD_GROUPS,
)
from config import BLOOD_GROUPS as CONFIG_BLOOD_GROUPS
from app.models.request import BloodRequest


# Use config canonical list
BLOOD_GROUPS_LIST = CONFIG_BLOOD_GROUPS or [
    "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"
]


class MatchingService:
    """Inventory and request-availability; requires Flask app for DB."""

    def __init__(self, app):
        self.app = app
        self.db = get_db(app)

    def get_inventory(self):
        """Return dict blood_group -> units (from donations with status Scheduled/Completed)."""
        return count_donations_by_blood_group_and_status(
            self.db,
            blood_groups=BLOOD_GROUPS_LIST,
            statuses=["Scheduled", "Completed"],
        )

    def get_recipient_requests_with_availability(self, requester_id):
        """Return list of request dicts with available_units and is_available."""
        inventory = self.get_inventory()
        requests = get_blood_requests_by_requester(self.db, requester_id, sort_timestamp=-1)

        def extra(req):
            bg = req.get("blood_group") or ""
            units_val = req.get("units", 0)
            try:
                requested_units = int(units_val) if units_val else 0
            except (TypeError, ValueError):
                requested_units = 0
            available_units = inventory.get(bg, 0)
            return {
                "available_units": available_units,
                "is_available": available_units >= requested_units if requested_units > 0 else False,
            }

        return BloodRequest.list_serializable(requests, extra_fn=extra)
