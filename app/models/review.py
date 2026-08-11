import uuid

from sqlalchemy import (
    String,
    Text,
    ForeignKey,
    CheckConstraint,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Review(BaseModel):
    __tablename__ = "reviews"

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

    reviewer_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    target_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    rating: Mapped[int] = mapped_column(
        TINYINT(unsigned=True),
        nullable=False
    )

    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Relationships
    job: Mapped["Job"] = relationship(
        "Job",
        foreign_keys=[job_id]
    )

    reviewer: Mapped["User"] = relationship(
        "User",
        foreign_keys=[reviewer_id]
    )

    target: Mapped["User"] = relationship(
        "User",
        foreign_keys=[target_id]
    )

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "rating BETWEEN 1 AND 5",
            name="chk_reviews_rating"
        ),

        UniqueConstraint(
            "job_id",
            "reviewer_id",
            name="uq_job_reviewer"
        ),

        Index(
            "idx_reviews_target",
            "target_id"
        ),
    )