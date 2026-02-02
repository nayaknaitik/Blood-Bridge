"""
Blood Bridge data models / schemas.
MongoDB is schema-less; these define expected shapes and serialization.
"""
from app.models.user import User
from app.models.donor import Donation
from app.models.request import BloodRequest

__all__ = ["User", "Donation", "BloodRequest"]
