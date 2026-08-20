import uuid

from sqlalchemy import String ,Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Skill(BaseModel):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )