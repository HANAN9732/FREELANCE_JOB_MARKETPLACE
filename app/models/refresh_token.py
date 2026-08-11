import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class RefreshToken(BaseModel):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    token_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id]
    )

    __table_args__ = (
        UniqueConstraint(
            "token_hash",
            name="uq_refresh_token_hash"
        ),

        Index(
            "idx_refresh_user",
            "user_id"
        ),
    )