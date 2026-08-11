import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    Text,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Message(BaseModel):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "jobs.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    sender_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    read_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    # Relationships
    job: Mapped["Job"] = relationship(
        "Job",
        foreign_keys=[job_id]
    )

    sender: Mapped["User"] = relationship(
        "User",
        foreign_keys=[sender_id]
    )

    # Index
    __table_args__ = (
        Index(
            "idx_messages_job_created",
            "job_id",
            "created_at"
        ),
    )