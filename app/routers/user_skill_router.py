from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_freelancer
from app.models.user import User
from app.models.skill import Skill
from app.models.user_skill import UserSkill
from app.schemas.user_skill import UserSkillResponse


router = APIRouter(
    prefix="/users/me/skills",
    tags=["Freelancer Skills"]
)


# Add a skill to the current freelancer
@router.post(
    "/{skill_id}",
    response_model=UserSkillResponse,
    status_code=status.HTTP_201_CREATED
)
def add_skill(
    skill_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_freelancer)
):

    # Check if skill exists
    skill = db.query(Skill).filter(
        Skill.id == skill_id,
        Skill.deleted_at.is_(None)
    ).first()

    if not skill:
        raise HTTPException(
            status_code=404,
            detail="Skill not found"
        )

    # Check if freelancer already has this skill
    existing_skill = db.query(UserSkill).filter(
        UserSkill.user_id == current_user.id,
        UserSkill.skill_id == skill_id
    ).first()

    if existing_skill:
        raise HTTPException(
            status_code=400,
            detail="You already have this skill"
        )

    # Create relationship
    user_skill = UserSkill(
        user_id=current_user.id,
        skill_id=skill_id
    )

    db.add(user_skill)
    db.commit()
    db.refresh(user_skill)

    return user_skill


# Get current freelancer's skills
@router.get(
    "",
    response_model=list[UserSkillResponse]
)
def get_my_skills(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_freelancer)
):

    user_skills = db.query(UserSkill).filter(
        UserSkill.user_id == current_user.id
    ).all()

    return user_skills


# Remove a skill from current freelancer
@router.delete(
    "/{skill_id}"
)
def remove_skill(
    skill_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_freelancer)
):

    user_skill = db.query(UserSkill).filter(
        UserSkill.user_id == current_user.id,
        UserSkill.skill_id == skill_id
    ).first()

    if not user_skill:
        raise HTTPException(
            status_code=404,
            detail="Skill is not assigned to you"
        )

    db.delete(user_skill)
    db.commit()

    return {
        "message": "Skill removed successfully"
    }