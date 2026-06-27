from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class ConvertedModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

class CreateSwingRequest(ConvertedModel):
    content_type: str

class CreateSwingResponse(ConvertedModel):
    swing_id: str
    upload_url: str
    s3_key: str

class SwingResponse(ConvertedModel):
    swing_id: str
    status: str
    created_at: str
    content_type: str

class Swing(SwingResponse):
    s3_key: str
    expires_at: int | None = None
    user_id: str | None = None