"""
DynamoDB client and table access for Blood Bridge.
Uses boto3; credentials from env or default chain.
"""
import os
import boto3
from botocore.exceptions import ClientError

from config import (
    AWS_REGION,
    USERS_TABLE,
    DONATIONS_TABLE,
    BLOOD_REQUESTS_TABLE,
    MESSAGES_TABLE,
    ADMINS_TABLE,
)


def _get_client():
    kwargs = {"region_name": os.environ.get("AWS_REGION") or AWS_REGION}
    if os.environ.get("AWS_ACCESS_KEY_ID"):
        kwargs["aws_access_key_id"] = os.environ.get("AWS_ACCESS_KEY_ID")
        kwargs["aws_secret_access_key"] = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
    return boto3.resource("dynamodb", **kwargs)


def get_dynamodb_tables(app):
    """Return an object with DynamoDB Table resources.

    Exposes:
      - users
      - donations
      - blood_requests
      - messages
      - admins
    """
    client = _get_client()
    return type("DynamoDBTables", (), {
        "client": client,
        "users": client.Table(os.environ.get("USERS_TABLE") or USERS_TABLE),
        "donations": client.Table(os.environ.get("DONATIONS_TABLE") or DONATIONS_TABLE),
        "blood_requests": client.Table(os.environ.get("BLOOD_REQUESTS_TABLE") or BLOOD_REQUESTS_TABLE),
        "messages": client.Table(os.environ.get("MESSAGES_TABLE") or MESSAGES_TABLE),
        "admins": client.Table(os.environ.get("ADMINS_TABLE") or ADMINS_TABLE),
    })()


def dynamodb_health_check(app):
    """Return True if DynamoDB is reachable (describe_table on users table)."""
    try:
        tables = app.extensions["dynamodb"]
        client = tables.client.meta.client
        client.describe_table(TableName=tables.users.name)
        return True
    except (ClientError, KeyError, AttributeError, Exception):
        return False
