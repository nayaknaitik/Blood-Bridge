"""
All database access for Blood Bridge.
Uses DynamoDB via boto3. No raw DB access in routes.
"""
import uuid
from datetime import datetime
from decimal import Decimal

from app.models.user import User
from app.models.donor import Donation
from app.models.request import BloodRequest
from boto3.dynamodb.conditions import Attr

from config import BLOOD_GROUPS


def get_db(app):
    """Return DynamoDB tables wrapper from app (has .users, .donations, .blood_requests, .messages)."""
    return app.extensions["dynamodb"]


def _serialize_item(item):
    """Convert DynamoDB item (with Decimal) to plain Python dict."""
    if not item:
        return None
    out = {}
    for k, v in item.items():
        if isinstance(v, Decimal):
            out[k] = int(v) if v % 1 == 0 else float(v)
        elif isinstance(v, dict):
            out[k] = _serialize_item(v)
        elif isinstance(v, list):
            out[k] = [_serialize_item(x) if isinstance(x, dict) else x for x in v]
        else:
            out[k] = v
    return out


# ---------- Users ----------
def find_user_by_id(db, user_id):
    item = User.from_id(db, user_id)
    return _serialize_item(item) if item else None


def find_user_by_email(db, email):
    email = (email or "").strip().lower()
    if not email:
        return None
    try:
        r = db.users.query(
            IndexName="email-index",
            KeyConditionExpression="email = :e",
            ExpressionAttributeValues={":e": email},
            Limit=1,
        )
        items = list(r.get("Items", []))
        return _serialize_item(items[0]) if items else None
    except Exception:
        return None


def create_user(db, name, email, password_hash, blood_group=None, role=None):
    user_id = str(uuid.uuid4())
    item = {
        "id": user_id,
        "name": (name or "").strip(),
        "email": (email or "").strip().lower(),
        "password": password_hash,
    }
    if blood_group is not None:
        item["blood_group"] = blood_group
    if role is not None:
        item["role"] = role
    db.users.put_item(Item=item)
    return user_id


def update_user_current_role(db, user_id, current_role):
    db.users.update_item(
        Key={"id": user_id},
        UpdateExpression="SET current_role = :r",
        ExpressionAttributeValues={":r": current_role},
    )


def delete_user_by_id(db, user_id):
    db.users.delete_item(Key={"id": user_id})


def list_all_users(db):
    r = db.users.scan()
    items = r.get("Items", [])
    while r.get("LastEvaluatedKey"):
        r = db.users.scan(ExclusiveStartKey=r["LastEvaluatedKey"])
        items.extend(r.get("Items", []))
    return [_serialize_item(i) for i in items]


def enrich_users_with_blood_group(db, users):
    for user in users:
        try:
            if user.get("blood_group"):
                continue
            uid = user.get("id")
            if not uid:
                continue
            donations = get_donations_by_donor(db, uid, limit=1)
            if donations and donations[0].get("blood_group"):
                bg = donations[0]["blood_group"]
                user["blood_group"] = bg
                db.users.update_item(
                    Key={"id": uid},
                    UpdateExpression="SET blood_group = :bg",
                    ExpressionAttributeValues={":bg": str(bg)},
                )
        except Exception:
            continue
    return users


# ---------- Donations ----------
def create_donation(db, donor_id, donor_name, blood_group, date, location, time_slot, status="Scheduled"):
    donation_id = str(uuid.uuid4())
    item = {
        "id": donation_id,
        "donor_id": donor_id,
        "donor_name": donor_name,
        "blood_group": blood_group,
        "date": str(date),
        "location": location or "",
        "time_slot": time_slot or "",
        "status": status,
    }
    db.donations.put_item(Item=item)
    return donation_id


def get_donations_by_donor(db, donor_id, limit=None):
    try:
        r = db.donations.query(
            IndexName="donor_id-date-index",
            KeyConditionExpression="donor_id = :d",
            ExpressionAttributeValues={":d": donor_id},
            ScanIndexForward=False,
        )
        items = r.get("Items", [])
        while r.get("LastEvaluatedKey") and (limit is None or len(items) < limit):
            r = db.donations.query(
                IndexName="donor_id-date-index",
                KeyConditionExpression="donor_id = :d",
                ExpressionAttributeValues={":d": donor_id},
                ScanIndexForward=False,
                ExclusiveStartKey=r["LastEvaluatedKey"],
            )
            items.extend(r.get("Items", []))
        items = [_serialize_item(i) for i in items]
        return items[:limit] if limit else items
    except Exception:
        return []


def get_recent_donations_for_bloodbank(db, limit=5):
    r = db.donations.scan(ProjectionExpression="donor_name, blood_group, #dt, location", ExpressionAttributeNames={"#dt": "date"})
    items = r.get("Items", [])
    while r.get("LastEvaluatedKey"):
        r = db.donations.scan(
            ProjectionExpression="donor_name, blood_group, #dt, location",
            ExpressionAttributeNames={"#dt": "date"},
            ExclusiveStartKey=r["LastEvaluatedKey"],
        )
        items.extend(r.get("Items", []))
    items = [_serialize_item(i) for i in items]
    items.sort(key=lambda x: (x.get("date") or ""), reverse=True)
    return items[:limit]


def get_all_donations_sorted(db, sort_timestamp=-1, limit=None):
    r = db.donations.scan()
    items = r.get("Items", [])
    while r.get("LastEvaluatedKey"):
        r = db.donations.scan(ExclusiveStartKey=r["LastEvaluatedKey"])
        items.extend(r.get("Items", []))
    items = [_serialize_item(i) for i in items]
    items.sort(key=lambda x: (x.get("date") or ""), reverse=True)
    return items[:limit] if limit else items


def count_donors_distinct(db):
    r = db.donations.scan(ProjectionExpression="donor_id")
    items = r.get("Items", [])
    while r.get("LastEvaluatedKey"):
        r = db.donations.scan(ProjectionExpression="donor_id", ExclusiveStartKey=r["LastEvaluatedKey"])
        items.extend(r.get("Items", []))
    return len(set(i.get("donor_id") for i in items if i.get("donor_id")))


def count_donations_by_date(db, date_str):
    r = db.donations.scan(
        FilterExpression="#dt = :d",
        ExpressionAttributeNames={"#dt": "date"},
        ExpressionAttributeValues={":d": str(date_str)},
    )
    count = len(r.get("Items", []))
    while r.get("LastEvaluatedKey"):
        r = db.donations.scan(
            FilterExpression="#dt = :d",
            ExpressionAttributeNames={"#dt": "date"},
            ExpressionAttributeValues={":d": str(date_str)},
            ExclusiveStartKey=r["LastEvaluatedKey"],
        )
        count += len(r.get("Items", []))
    return count


def count_donations_by_blood_group_and_status(db, blood_groups=None, statuses=None):
    blood_groups = blood_groups or BLOOD_GROUPS
    statuses = statuses or ["Scheduled", "Completed"]

    # Initialize result
    result = {bg: 0 for bg in blood_groups}

    # Correct DynamoDB filter expression
    filter_expr = (
        Attr("blood_group").is_in(blood_groups) &
        Attr("status").is_in(statuses)
    )

    r = db.donations.scan(FilterExpression=filter_expr)

    for item in r.get("Items", []):
        bg = item.get("blood_group")
        if bg in result:
            result[bg] += 1

    # Handle pagination
    while "LastEvaluatedKey" in r:
        r = db.donations.scan(
            FilterExpression=filter_expr,
            ExclusiveStartKey=r["LastEvaluatedKey"],
        )
        for item in r.get("Items", []):
            bg = item.get("blood_group")
            if bg in result:
                result[bg] += 1

    return result


# ---------- Blood requests ----------
def create_blood_request(db, requester_id, patient_name, blood_group, units, hospital, status="pending"):
    try:
        units = int(units) if units is not None else 0
    except (TypeError, ValueError):
        units = 0
    request_id = str(uuid.uuid4())
    ts = datetime.utcnow().isoformat() + "Z"
    item = {
        "id": request_id,
        "requester_id": requester_id,
        "patient_name": patient_name,
        "blood_group": blood_group,
        "units": units,
        "hospital": hospital,
        "status": status,
        "timestamp": ts,
    }
    db.blood_requests.put_item(Item=item)
    return request_id


def get_blood_requests_by_requester(db, requester_id, sort_timestamp=-1):
    try:
        r = db.blood_requests.query(
            IndexName="requester_id-timestamp-index",
            KeyConditionExpression="requester_id = :r",
            ExpressionAttributeValues={":r": requester_id},
            ScanIndexForward=(sort_timestamp == 1),
        )
        items = r.get("Items", [])
        while r.get("LastEvaluatedKey"):
            r = db.blood_requests.query(
                IndexName="requester_id-timestamp-index",
                KeyConditionExpression="requester_id = :r",
                ExpressionAttributeValues={":r": requester_id},
                ScanIndexForward=(sort_timestamp == 1),
                ExclusiveStartKey=r["LastEvaluatedKey"],
            )
            items.extend(r.get("Items", []))
        return [_serialize_item(i) for i in items]
    except Exception:
        return []


def get_pending_blood_requests(db, limit=None):
    try:
        r = db.blood_requests.query(
            IndexName="status-timestamp-index",
            KeyConditionExpression="#st = :pending",
            ExpressionAttributeNames={"#st": "status"},
            ExpressionAttributeValues={":pending": "pending"},
            ScanIndexForward=False,
        )
        items = r.get("Items", [])
        while r.get("LastEvaluatedKey") and (limit is None or len(items) < limit):
            r = db.blood_requests.query(
                IndexName="status-timestamp-index",
                KeyConditionExpression="#st = :pending",
                ExpressionAttributeNames={"#st": "status"},
                ExpressionAttributeValues={":pending": "pending"},
                ScanIndexForward=False,
                ExclusiveStartKey=r["LastEvaluatedKey"],
            )
            items.extend(r.get("Items", []))
        items = [_serialize_item(i) for i in items]
        return items[:limit] if limit else items
    except Exception:
        return []


def get_all_blood_requests_sorted(db, sort_timestamp=-1, limit=None):
    r = db.blood_requests.scan()
    items = r.get("Items", [])
    while r.get("LastEvaluatedKey"):
        r = db.blood_requests.scan(ExclusiveStartKey=r["LastEvaluatedKey"])
        items.extend(r.get("Items", []))
    items = [_serialize_item(i) for i in items]
    items.sort(key=lambda x: x.get("timestamp") or "", reverse=(sort_timestamp == -1))
    return items[:limit] if limit else items


def count_blood_requests_by_status(db, status):
    try:
        r = db.blood_requests.query(
            IndexName="status-timestamp-index",
            KeyConditionExpression="#st = :s",
            ExpressionAttributeNames={"#st": "status"},
            ExpressionAttributeValues={":s": status},
            Select="COUNT",
        )
        count = r.get("Count", 0)
        while r.get("LastEvaluatedKey"):
            r = db.blood_requests.query(
                IndexName="status-timestamp-index",
                KeyConditionExpression="#st = :s",
                ExpressionAttributeNames={"#st": "status"},
                ExpressionAttributeValues={":s": status},
                Select="COUNT",
                ExclusiveStartKey=r["LastEvaluatedKey"],
            )
            count += r.get("Count", 0)
        return count
    except Exception:
        return 0


def count_recipients_distinct(db):
    r = db.blood_requests.scan(ProjectionExpression="requester_id")
    items = r.get("Items", [])
    while r.get("LastEvaluatedKey"):
        r = db.blood_requests.scan(ProjectionExpression="requester_id", ExclusiveStartKey=r["LastEvaluatedKey"])
        items.extend(r.get("Items", []))
    return len(set(i.get("requester_id") for i in items if i.get("requester_id")))


# ---------- Contact messages ----------
def create_contact_message(db, name, email, subject, message):
    msg_id = str(uuid.uuid4())
    ts = datetime.utcnow().isoformat() + "Z"
    item = {
        "id": msg_id,
        "name": name,
        "email": email,
        "subject": subject,
        "message": message,
        "timestamp": ts,
    }
    db.messages.put_item(Item=item)
    return msg_id


# ---------- Admin ----------
def count_users_by_role(db, role):
    r = db.users.scan(
        FilterExpression="#r = :role",
        ExpressionAttributeNames={"#r": "role"},
        ExpressionAttributeValues={":role": role},
        Select="COUNT",
    )
    count = r.get("Count", 0)
    while r.get("LastEvaluatedKey"):
        r = db.users.scan(
            FilterExpression="#r = :role",
            ExpressionAttributeNames={"#r": "role"},
            ExpressionAttributeValues={":role": role},
            Select="COUNT",
            ExclusiveStartKey=r["LastEvaluatedKey"],
        )
        count += r.get("Count", 0)
    return count


# ---------- Admin users (separate table) ----------
def find_admin_by_email(db, email):
    """Find admin by email from Admins table."""
    email = (email or "").strip().lower()
    if not email:
        return None
    try:
        r = db.admins.query(
            IndexName="admin-email-index",
            KeyConditionExpression="email = :e",
            ExpressionAttributeValues={":e": email},
            Limit=1,
        )
        items = list(r.get("Items", []))
        return _serialize_item(items[0]) if items else None
    except Exception:
        return None


def find_admin_by_id(db, admin_id):
    """Find admin by id (primary key) from Admins table."""
    try:
        r = db.admins.get_item(Key={"id": str(admin_id)})
        return _serialize_item(r.get("Item")) if r.get("Item") else None
    except Exception:
        return None


def create_admin(db, name, email, password_hash):
    """Create a new admin user in Admins table."""
    admin_id = str(uuid.uuid4())
    item = {
        "id": admin_id,
        "name": (name or "").strip(),
        "email": (email or "").strip().lower(),
        "password": password_hash,
    }
    db.admins.put_item(Item=item)
    return admin_id
