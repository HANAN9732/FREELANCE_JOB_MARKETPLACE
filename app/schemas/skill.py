from pydantic import BaseModel, Field


class SkillCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    description: str | None = None


class SkillUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    description: str | None = None


class SkillResponse(BaseModel):
    id: str
    name: str
    description: str | None

    model_config = {
        "from_attributes": True
    }