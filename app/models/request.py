"""
Blood request model and serialization for DynamoDB items.
"""
from datetime import datetime


def _format_timestamp(ts):
    if ts is None:
        return "N/A"
    if isinstance(ts, datetime):
        return ts.strftime("%Y-%m-%d")
    s = str(ts)
    return s[:10] if len(s) >= 10 else "N/A"


class BloodRequest:
    """Blood request document shape and serialization."""

    @staticmethod
    def to_serializable(doc, extra=None):
        """Convert blood request item to JSON-serializable dict."""
        if not doc:
            return None
        out = {
            "id": str(doc.get("id") or doc.get("_id", "")),
            "requester_id": doc.get("requester_id"),
            "patient_name": doc.get("patient_name", "N/A"),
            "blood_group": doc.get("blood_group", "N/A"),
            "units": doc.get("units"),
            "hospital": doc.get("hospital", "N/A"),
            "status": doc.get("status", "pending"),
            "timestamp": _format_timestamp(doc.get("timestamp")),
        }
        if extra:
            out.update(extra)
        return out

    @staticmethod
    def list_serializable(docs, extra_fn=None):
        result = []
        for d in docs or []:
            extra = extra_fn(d) if extra_fn else None
            result.append(BloodRequest.to_serializable(d, extra))
        return result
