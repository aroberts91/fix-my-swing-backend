from functools import lru_cache
import os
import boto3
from botocore.config import Config

@lru_cache
def get_s3_client():
    return boto3.client(
        "s3",
        region_name=os.environ["AWS_REGION"],
        config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
    )

@lru_cache
def get_table():
        return boto3.resource("dynamodb", region_name=os.environ["AWS_REGION"]).Table(
          os.environ["SWINGS_TABLE_NAME"]
    )

def get_bucket_name() -> str:
    return os.environ["UPLOADS_BUCKET_NAME"]