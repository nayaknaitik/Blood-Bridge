"""
User model and serialization for DynamoDB items.
"""


class User:
    """User document shape and serialization."""

    @staticmethod
    def to_serializable(doc):
        """Convert user item to JSON-serializable dict."""
        if not doc:
            return None
        return {
            "id": str(doc.get("id") or doc.get("_id", "")),
            "name": doc.get("name", ""),
            "email": doc.get("email", ""),
            "role": doc.get("role"),
            "current_role": doc.get("current_role"),
            "blood_group": doc.get("blood_group"),
        }

    @staticmethod
    def from_id(db, user_id):
        """Fetch user by string id. Returns None if not found. Caller should _serialize_item if needed."""
        try:
            r = db.users.get_item(Key={"id": str(user_id)})
            return r.get("Item")
        except Exception:
            return None
