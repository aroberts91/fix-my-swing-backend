import os
import datetime
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from botocore.exceptions import ClientError

from dependencies import get_s3_client, get_table, get_bucket_name
from schemas import CreateSwingRequest, CreateSwingResponse, SwingResponse, Swing

router = APIRouter(prefix="/swings", tags=["swings"])

@router.post("")
def create_swing(
        payload: CreateSwingRequest,
        table=Depends(get_table),
        s3_client=Depends(get_s3_client),
        bucket=Depends(get_bucket_name)
) -> CreateSwingResponse:
    swing_id = uuid.uuid4().hex
    user_id = None

    s3_key = f"swings/{swing_id}/source.mp4"

    now = datetime.datetime.now(datetime.timezone.utc)

    swing = Swing(
        swing_id=swing_id,
        status="uploading",
        created_at=now.isoformat(),
        content_type=payload.content_type,
        s3_key=s3_key,
        user_id=user_id,
        expires_at=None if user_id else int((now + datetime.timedelta(days=7)).timestamp()),
    )

    try:
        table.put_item(Item=swing.model_dump(exclude_none=True))
    except ClientError as e:
        logging.error(
            "Couldn't add swing %s to table %s. Here's why: %s: %s",
            swing_id,
            table.name,
            e.response["Error"]["Code"],
            e.response["Error"]["Message"]
        )
        raise HTTPException(status_code=500, detail="Could not create swing")

    try:
        upload_url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": bucket,
                "Key": s3_key,
                "ContentType": payload.content_type
            },
            ExpiresIn=300
        )
    except ClientError as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail="Could not create upload URL")

    return CreateSwingResponse(
        swing_id=swing_id,
        upload_url=upload_url,
        s3_key=s3_key
    )

@router.get("/{swing_id}")
def get_swing(swing_id: str, table=Depends(get_table)) -> SwingResponse:
    response = table.get_item(Key={"swing_id": swing_id})

    if "Item" not in response:
        raise HTTPException(status_code=404, detail="Swing not found")

    return SwingResponse(**response["Item"])