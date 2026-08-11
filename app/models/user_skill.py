from sqlalchemy import String, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserSkill(Base):
    __tablename__ = "user_skills"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "users.id",
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
            "idx_user_skills_skill",
            "skill_id"
        ),
    )