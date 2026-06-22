from pydantic import BaseModel

class CreateSwingRequest(BaseModel):
    content_type: str