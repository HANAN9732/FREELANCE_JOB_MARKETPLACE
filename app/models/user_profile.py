from datetime import datetime

from sqlalchemy import (
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
)
from sqlalchemy.dialects.mysql import INTEGER, TINYINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class UserProfile(BaseModel):
    __tablename__ = "user_profiles"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        primary_key=True
    )

    bio: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    avatar_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    rating: Mapped[float] = mapped_column(
        Numeric(3, 2),
        nullable=False,
        default=0.00
    )

    reviews_received_count: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
        default=0
    )

    profile_completeness: Mapped[int] = mapped_column(
        TINYINT(unsigned=True),
        nullable=False,
        default=0
    )

    is_suspended: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    suspended_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="profile"
    )