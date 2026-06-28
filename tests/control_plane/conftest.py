import os
import boto3
import pytest
from moto import mock_aws
from fastapi.testclient import TestClient

from dependencies import get_s3_client, get_table, get_bucket_name
from main import app

TABLE_NAME = "test-swings"
BUCKET_NAME = "test-uploads"


@pytest.fixture
def client():
    os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
    os.environ.setdefault("AWS_DEFAULT_REGION", "eu-west-2")

    with mock_aws():
        ddb = boto3.resource("dynamodb", region_name="eu-west-2")
        ddb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[{"AttributeName": "swing_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "swing_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        s3 = boto3.client("s3", region_name="eu-west-2")
        s3.create_bucket(
            Bucket=BUCKET_NAME,
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )

        app.dependency_overrides[get_table] = lambda: ddb.Table(TABLE_NAME)
        app.dependency_overrides[get_s3_client] = lambda: s3
        app.dependency_overrides[get_bucket_name] = lambda: BUCKET_NAME

        yield TestClient(app)

        app.dependency_overrides.clear()