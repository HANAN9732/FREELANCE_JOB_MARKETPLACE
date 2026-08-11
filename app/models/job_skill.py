from sqlalchemy import String, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class JobSkill(Base):
    __tablename__ = "job_skills"

    job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "jobs.id",
            ondelete="CASCADE"
        ),
        primary_key=True
    )

    skill_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "skills.id",
            ondelete="CASCADE"
        ),
        primary_key=True
    )

    __table_args__ = (
        Index(
            "idx_job_skills_skill",
            "skill_id"
        ),
    )