from datetime import datetime

from pydantic import BaseModel, Field



class MessageCreate(BaseModel):
    content: str = Field(
        ...,
        min_length=1,
        max_length=5000
    )


class MessageResponse(BaseModel):
    id: str
    job_id: str
    sender_id: str
    content: str
    created_at: datetime
    read_at: datetime | None

    model_config = {
        "from_attributes": True
    }