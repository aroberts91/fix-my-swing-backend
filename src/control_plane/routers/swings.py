import os
import boto3
import datetime
import logging
import uuid

from fastapi import APIRouter, HTTPException
from botocore.exceptions import ClientError
from botocore.config import Config
from schemas import CreateSwingRequest

s3_client = boto3.client(
      "s3",
      region_name=os.environ["AWS_REGION"],
      config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
)

dynamodb = boto3.resource("dynamodb")

table = dynamodb.Table(os.environ["SWINGS_TABLE_NAME"])

router = APIRouter(prefix="/swings", tags=["swings"])

@router.post("")
def create_swing(payload: CreateSwingRequest):
    swing_id = uuid.uuid4().hex
    user_id = None

    s3_key = f"swings/{swing_id}/source.mp4"

    now = datetime.datetime.now(datetime.timezone.utc)

    item = {
        "swing_id": swing_id,
        "status": "uploading",
        "created_at": now.isoformat(),
        "s3_key": s3_key,
        "content_type": payload.content_type,
    }

    if user_id:
        item["user_id"] = user_id
    else:
        item["expires_at"] = int((now + datetime.timedelta(days=7)).timestamp())

    try:
        table.put_item(Item=item)
    except ClientError as e:
        logging.error(
            "Couldn't add swing %s to table %s. Here's why: %s: %s",
            swing_id,
            os.environ["SWINGS_TABLE_NAME"],
            e.response["Error"]["Code"],
            e.response["Error"]["Message"]
        )
        raise HTTPException(status_code=500, detail="Could not create swing")

    try:
        upload_url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": os.environ["UPLOADS_BUCKET_NAME"],
                "Key": s3_key,
                "ContentType": payload.content_type
            },
            ExpiresIn=300
        )
    except ClientError as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail="Could not create upload URL")

    return {"swing_id": swing_id, "upload_url": upload_url, "s3_key": s3_key}

@router.get("/{swing_id}")
def get_swing(swing_id: str):
    response = table.get_item(Key={"swing_id": swing_id})

    if "Item" not in response:
        raise HTTPException(status_code=404, detail="Swing not found")

    return response["Item"]