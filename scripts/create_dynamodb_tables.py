#!/usr/bin/env python3
"""
Create DynamoDB tables for Blood Bridge.
Run from project root: python scripts/create_dynamodb_tables.py
Requires: AWS credentials (env or ~/.aws/credentials), boto3.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import boto3
from config import (
    AWS_REGION,
    USERS_TABLE,
    DONATIONS_TABLE,
    BLOOD_REQUESTS_TABLE,
    MESSAGES_TABLE,
    ADMINS_TABLE,
)


def get_client():
    kwargs = {"region_name": os.environ.get("AWS_REGION") or AWS_REGION}
    if os.environ.get("AWS_ACCESS_KEY_ID"):
        kwargs["aws_access_key_id"] = os.environ.get("AWS_ACCESS_KEY_ID")
        kwargs["aws_secret_access_key"] = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
    return boto3.client("dynamodb", **kwargs)


def create_tables(client):
    # Users: PK id (S), GSI email-index (email as PK for login lookup)
    try:
        client.create_table(
            TableName=USERS_TABLE,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "email", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "email-index",
                    "KeySchema": [{"AttributeName": "email", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        print(f"Created table: {USERS_TABLE}")
    except client.exceptions.ResourceInUseException:
        print(f"Table {USERS_TABLE} already exists.")

    # Donations: PK id (S), GSI donor_id-date-index
    try:
        client.create_table(
            TableName=DONATIONS_TABLE,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "donor_id", "AttributeType": "S"},
                {"AttributeName": "date", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "donor_id-date-index",
                    "KeySchema": [
                        {"AttributeName": "donor_id", "KeyType": "HASH"},
                        {"AttributeName": "date", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        print(f"Created table: {DONATIONS_TABLE}")
    except client.exceptions.ResourceInUseException:
        print(f"Table {DONATIONS_TABLE} already exists.")

    # Blood requests: PK id (S), GSIs requester_id-timestamp-index, status-timestamp-index
    try:
        client.create_table(
            TableName=BLOOD_REQUESTS_TABLE,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "requester_id", "AttributeType": "S"},
                {"AttributeName": "status", "AttributeType": "S"},
                {"AttributeName": "timestamp", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "requester_id-timestamp-index",
                    "KeySchema": [
                        {"AttributeName": "requester_id", "KeyType": "HASH"},
                        {"AttributeName": "timestamp", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
                {
                    "IndexName": "status-timestamp-index",
                    "KeySchema": [
                        {"AttributeName": "status", "KeyType": "HASH"},
                        {"AttributeName": "timestamp", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        print(f"Created table: {BLOOD_REQUESTS_TABLE}")
    except client.exceptions.ResourceInUseException:
        print(f"Table {BLOOD_REQUESTS_TABLE} already exists.")

    # Messages: PK id (S)
    try:
        client.create_table(
            TableName=MESSAGES_TABLE,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        print(f"Created table: {MESSAGES_TABLE}")
    except client.exceptions.ResourceInUseException:
        print(f"Table {MESSAGES_TABLE} already exists.")

    # Admins: PK id (S), GSI admin-email-index (email as PK for admin login)
    try:
        client.create_table(
            TableName=ADMINS_TABLE,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "email", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "admin-email-index",
                    "KeySchema": [{"AttributeName": "email", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        print(f"Created table: {ADMINS_TABLE}")
    except client.exceptions.ResourceInUseException:
        print(f"Table {ADMINS_TABLE} already exists.")


if __name__ == "__main__":
    client = get_client()
    create_tables(client)
    print("Done.")
