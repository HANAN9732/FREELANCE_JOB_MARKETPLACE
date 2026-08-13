from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    title: str = Field(
        ...,
        min_length=3,
        max_length=255
    )

    description: str = Field(
        ...,
        min_length=10
    )

    budget: Decimal = Field(
        ...,
        gt=0
    )

    deadline: datetime | None = None


class JobUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=3,
        max_length=255
    )

    description: str | None = Field(
        default=None,
        min_length=10
    )

    budget: Decimal | None = Field(
        default=None,
        gt=0
    )

    deadline: datetime | None = None


class JobResponse(BaseModel):
    id: str
    client_id: str
    title: str
    description: str
    budget: Decimal
    status: str
    deadline: datetime | None

    model_config = {
        "from_attributes": True
    }
    