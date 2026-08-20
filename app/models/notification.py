import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    String,
    Enum,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

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

    type: Mapped[str] = mapped_column(
        Enum(
            "new_proposal",
            "proposal_accepted",
            "proposal_rejected",
            "new_message",
            "job_status_change",
            name="notification_type"
        ),
        nullable=False
    )

    reference_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True
    )

    payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id]
    )

    __table_args__ = (
        Index(
            "idx_notifications_user_read",
            "user_id",
            "is_read"
        ),
        Index(
            "idx_notifications_user_created",
            "user_id",
            "created_at"
        ),
    )