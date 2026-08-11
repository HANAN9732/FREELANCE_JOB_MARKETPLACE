import uuid
from datetime import date

from sqlalchemy import (
    String,
    Text,
    ForeignKey,
    Date,
    Enum,
    Numeric,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Job(BaseModel):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    client_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    budget: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    deadline: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        Enum(
            "open",
            "assigned",
            "in_progress",
            "completed",
            "closed",
            name="job_status"
        ),
        nullable=False,
        default="open"
    )

    assigned_freelancer_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    # Relationships
    client: Mapped["User"] = relationship(
        "User",
        foreign_keys=[client_id]
    )

    assigned_freelancer: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[assigned_freelancer_id]
    )

    # Indexes
    __table_args__ = (
        Index("idx_jobs_status", "status"),
        Index("idx_jobs_client", "client_id"),
        Index("idx_jobs_deadline_status", "deadline", "status"),
    )