from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class ConvertedModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

class CreateSwingRequest(ConvertedModel):
    content_type: str

class CreateSwingResponse(ConvertedModel):
    swing_id: str
    upload_url: str
    s3_key: str

class Swing(ConvertedModel):
    swing_id: str
    content_type: str
    created_at: str
    status: str