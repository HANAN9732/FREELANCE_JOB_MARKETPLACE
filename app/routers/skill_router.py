from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_admin
from app.core.logger import logger

from app.models.skill import Skill
from app.models.user import User

from app.schemas.skill import (
    SkillCreate,
    SkillUpdate,
    SkillResponse
)


router = APIRouter(
    prefix="/skills",
    tags=["Skills"]
)


# =========================================
# CREATE SKILL
# =========================================

@router.post(
    "/",
    response_model=SkillResponse,
    status_code=201
)
def create_skill(
    skill_data: SkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):

    logger.info(
        f"Admin {current_user.id} attempting to create "
        f"skill '{skill_data.name}'"
    )

    # Check whether skill already exists
    existing_skill = db.query(Skill).filter(
        Skill.name == skill_data.name
    ).first()

    if existing_skill:

        logger.warning(
            f"Admin {current_user.id} attempted to create "
            f"duplicate skill '{skill_data.name}'"
        )

        raise HTTPException(
            status_code=400,
            detail="Skill already exists"
        )

    new_skill = Skill(
        name=skill_data.name,
        description=skill_data.description
    )

    db.add(new_skill)
    db.commit()
    db.refresh(new_skill)

    logger.info(
        f"Skill '{new_skill.name}' created successfully "
        f"with ID {new_skill.id} by admin {current_user.id}"
    )

    return new_skill


# =========================================
# GET ALL SKILLS
# =========================================

@router.get(
    "/",
    response_model=list[SkillResponse]
)
def get_all_skills(
    db: Session = Depends(get_db)
):

    logger.info(
        "Request received to fetch all skills"
    )

    skills = db.query(Skill).all()

    logger.info(
        f"Returned {len(skills)} skills"
    )

    return skills


# =========================================
# GET ONE SKILL
# Search by UUID OR NAME
# =========================================

@router.get(
    "/{skill_identifier}",
    response_model=SkillResponse
)
def get_skill(
    skill_identifier: str,
    db: Session = Depends(get_db)
):

    logger.info(
        f"Searching for skill using identifier "
        f"'{skill_identifier}'"
    )

    # -----------------------------------------
    # First search by UUID
    # -----------------------------------------

    skill = db.query(Skill).filter(
        Skill.id == skill_identifier
    ).first()

    # -----------------------------------------
    # If UUID not found, search by name
    # -----------------------------------------

    if not skill:

        logger.info(
            f"Skill ID '{skill_identifier}' not found. "
            f"Searching by skill name."
        )

        skill = db.query(Skill).filter(
            Skill.name == skill_identifier
        ).first()

    # -----------------------------------------
    # Skill not found
    # -----------------------------------------

    if not skill:

        logger.warning(
            f"Skill '{skill_identifier}' not found"
        )

        raise HTTPException(
            status_code=404,
            detail="Skill not found"
        )

    logger.info(
        f"Skill '{skill.name}' found successfully "
        f"with ID {skill.id}"
    )

    return skill


# =========================================
# UPDATE SKILL
# =========================================

@router.put(
    "/{skill_id}",
    response_model=SkillResponse
)
def update_skill(
    skill_id: str,
    skill_data: SkillUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):

    logger.info(
        f"Admin {current_user.id} attempting to update "
        f"skill {skill_id}"
    )

    skill = db.query(Skill).filter(
        Skill.id == skill_id
    ).first()

    if not skill:

        logger.warning(
            f"Skill {skill_id} not found for update"
        )

        raise HTTPException(
            status_code=404,
            detail="Skill not found"
        )

    # -----------------------------------------
    # Update name
    # -----------------------------------------

    if skill_data.name is not None:

        existing_skill = db.query(Skill).filter(
            Skill.name == skill_data.name,
            Skill.id != skill_id
        ).first()

        if existing_skill:

            logger.warning(
                f"Admin {current_user.id} attempted to change "
                f"skill {skill_id} to duplicate name "
                f"'{skill_data.name}'"
            )

            raise HTTPException(
                status_code=400,
                detail="Skill name already exists"
            )

        skill.name = skill_data.name

    # -----------------------------------------
    # Update description
    # -----------------------------------------

    if skill_data.description is not None:

        skill.description = skill_data.description

    db.commit()
    db.refresh(skill)

    logger.info(
        f"Skill {skill_id} updated successfully "
        f"by admin {current_user.id}"
    )

    return skill


# =========================================
# DELETE SKILL
# HARD DELETE
# =========================================

@router.delete(
    "/{skill_id}"
)
def delete_skill(
    skill_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):

    logger.info(
        f"Admin {current_user.id} attempting to delete "
        f"skill {skill_id}"
    )

    skill = db.query(Skill).filter(
        Skill.id == skill_id
    ).first()

    if not skill:

        logger.warning(
            f"Skill {skill_id} not found for deletion"
        )

        raise HTTPException(
            status_code=404,
            detail="Skill not found"
        )

    skill_name = skill.name

    # -----------------------------------------
    # HARD DELETE
    # -----------------------------------------

    db.delete(skill)
    db.commit()

    logger.info(
        f"Skill {skill_id} ('{skill_name}') permanently "
        f"deleted by admin {current_user.id}"
    )

    return {
        "message": "Skill deleted successfully"
    }