from pymongo import MongoClient
from bson.objectid import ObjectId

class DataStore:
    def __init__(self, uri="mongodb://localhost:27017/", db_name="bloodbridge"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.users = self.db.users
        self.requests = self.db.blood_requests
        self.inventory = self.db.inventory
        self.donations = self.db.donations

    # --- User Operations ---
    def add_user(self, user_data):
        """Inserts a new user into the database."""
        return self.users.insert_one(user_data)

    def find_user_by_email(self, email):
        """Finds a single user by their email address."""
        return self.users.find_one({"email": email})

    def get_all_users(self):
        """Returns a list of all users."""
        return list(self.users.find())

    def delete_user(self, user_id):
        """Deletes a user by their MongoDB ObjectId."""
        return self.users.delete_one({"_id": ObjectId(user_id)})

    # --- Blood Request Operations ---
    def create_request(self, request_data):
        """Stores a new blood request."""
        return self.requests.insert_one(request_data)

    def get_all_requests(self):
        """Fetches all blood requests, sorted by newest first."""
        return list(self.requests.find().sort("_id", -1))

    def get_requests_by_type(self, blood_group):
        """Filters requests by blood group."""
        return list(self.requests.find({"blood_group": blood_group}))

    def update_request_status(self, request_id, new_status):
        """Updates the status (e.g., pending to fulfilled)."""
        return self.requests.update_one(
            {"_id": ObjectId(request_id)},
            {"$set": {"status": new_status}}
        )

    # --- Inventory Operations ---
    def get_inventory_by_blood_group(self, blood_group):
        """Gets inventory count for a specific blood group."""
        item = self.inventory.find_one({"blood_group": blood_group})
        return item.get("units", 0) if item else 0

    def update_inventory(self, blood_group, units_change, operation="add"):
        """Updates inventory for a blood group. operation can be 'add' or 'subtract'."""
        if operation == "add":
            self.inventory.update_one(
                {"blood_group": blood_group},
                {"$inc": {"units": units_change}},
                upsert=True
            )
        elif operation == "subtract":
            self.inventory.update_one(
                {"blood_group": blood_group},
                {"$inc": {"units": -units_change}},
                upsert=True
            )

    def get_all_inventory(self):
        """Returns all inventory items."""
        blood_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        inventory_list = []
        for bg in blood_groups:
            item = self.inventory.find_one({"blood_group": bg})
            inventory_list.append({
                "group": bg,
                "units": item.get("units", 0) if item else 0
            })
        return inventory_list

    def calculate_inventory_from_donations(self):
        """Calculates inventory by counting completed donations grouped by blood group."""
        pipeline = [
            {"$match": {"status": {"$in": ["Scheduled", "Completed"]}}},
            {"$group": {
                "_id": "$blood_group",
                "count": {"$sum": 1}
            }}
        ]
        results = list(self.donations.aggregate(pipeline))
        
        # Update inventory collection
        for result in results:
            blood_group = result["_id"]
            count = result["count"]
            self.inventory.update_one(
                {"blood_group": blood_group},
                {"$set": {"units": count}},
                upsert=True
            )
        
        return results