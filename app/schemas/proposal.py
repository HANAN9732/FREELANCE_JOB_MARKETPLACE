from decimal import Decimal

from pydantic import BaseModel, Field


class ProposalResponse(BaseModel):

    id: str
    job_id: str
    freelancer_id: str

    bid_amount: Decimal

    cover_letter_path: str = Field(
        ...,
        max_length=500
    )

    delivery_time_days: int

    status: str

    model_config = {
        "from_attributes": True
    }