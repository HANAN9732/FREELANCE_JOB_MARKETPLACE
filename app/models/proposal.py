import uuid

from sqlalchemy import (
    String,
    ForeignKey,
    Numeric,
    Enum,
    Index,
    UniqueConstraint,
    
)
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Proposal(BaseModel):
    __tablename__ = "proposals"

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

    freelancer_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    bid_amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    cover_letter_path: Mapped[str] = mapped_column(
    String(500),
    nullable=False
)

    delivery_time_days: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "accepted",
            "rejected",
            "withdrawn",
            name="proposal_status"
        ),
        nullable=False,
        default="pending"
    )

    # Relationships
    job: Mapped["Job"] = relationship(
        "Job",
        foreign_keys=[job_id]
    )

    freelancer: Mapped["User"] = relationship(
        "User",
        foreign_keys=[freelancer_id]
    )

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "freelancer_id",
            name="uq_job_freelancer"
        ),

        Index(
            "idx_proposals_job",
            "job_id"
        ),

        Index(
            "idx_proposals_freelancer",
            "freelancer_id"
        ),

        Index(
            "idx_proposals_status",
            "status"
        ),
    )