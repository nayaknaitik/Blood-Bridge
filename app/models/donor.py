"""
Donation (donor) model and serialization for DynamoDB items.
"""


class Donation:
    """Donation document shape and serialization."""

    @staticmethod
    def to_serializable(doc):
        """Convert donation item to JSON-serializable dict."""
        if not doc:
            return None
        return {
            "id": str(doc.get("id") or doc.get("_id", "")),
            "donor_id": doc.get("donor_id"),
            "donor_name": doc.get("donor_name", ""),
            "blood_group": doc.get("blood_group", ""),
            "date": doc.get("date", ""),
            "location": doc.get("location", ""),
            "time_slot": doc.get("time_slot", ""),
            "status": doc.get("status", "Scheduled"),
        }

    @staticmethod
    def list_serializable(docs):
        return [Donation.to_serializable(d) for d in (docs or [])]
