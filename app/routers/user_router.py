from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.core.dependencies import (
    get_db,
    get_current_user,
    require_admin,
)
from app.core.logger import logger


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


# =========================================================
# SELF-SERVICE
# Any logged-in user
# =========================================================

@router.get(
    "/me",
    response_model=UserResponse
)
def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    logger.info(
        f"User profile viewed | user_id={current_user.id}"
    )

    return current_user


@router.put(
    "/me",
    response_model=UserResponse
)
def update_my_profile(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logger.info(
        f"Profile update requested | user_id={current_user.id}"
    )

    update_data = user_data.model_dump(
        exclude_unset=True
    )

    # -----------------------------------------------------
    # Check email uniqueness
    # -----------------------------------------------------

    if "email" in update_data:

        existing_user = db.query(User).filter(
            User.email == update_data["email"],
            User.id != current_user.id
        ).first()

        if existing_user:

            logger.warning(
                f"Profile update failed - email already in use "
                f"| user_id={current_user.id} "
                f"| email={update_data['email']}"
            )

            raise HTTPException(
                status_code=400,
                detail="Email already in use"
            )

    # -----------------------------------------------------
    # Update fields
    # -----------------------------------------------------

    for field, value in update_data.items():
        setattr(current_user, field, value)

    try:

        db.commit()
        db.refresh(current_user)

        logger.info(
            f"Profile updated successfully "
            f"| user_id={current_user.id}"
        )

    except Exception:

        db.rollback()

        logger.exception(
            f"Profile update failed "
            f"| user_id={current_user.id}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to update profile"
        )

    return current_user


# =========================================================
# ADMIN ONLY
# =========================================================

@router.get(
    "",
    response_model=list[UserResponse]
)
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):

    logger.info(
        f"Admin requested all users "
        f"| admin_id={current_user.id}"
    )

    users = db.query(User).filter(
        User.deleted_at.is_(None)
    ).all()

    logger.info(
        f"Users retrieved successfully "
        f"| admin_id={current_user.id} "
        f"| count={len(users)}"
    )

    return users


@router.get(
    "/{user_id}",
    response_model=UserResponse
)
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):

    logger.info(
        f"Admin requested user "
        f"| admin_id={current_user.id} "
        f"| user_id={user_id}"
    )

    user = db.query(User).filter(
        User.id == user_id,
        User.deleted_at.is_(None)
    ).first()

    if not user:

        logger.warning(
            f"User not found "
            f"| admin_id={current_user.id} "
            f"| user_id={user_id}"
        )

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    logger.info(
        f"User retrieved successfully "
        f"| admin_id={current_user.id} "
        f"| user_id={user_id}"
    )

    return user


@router.put(
    "/{user_id}",
    response_model=UserResponse
)
def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):

    logger.info(
        f"Admin requested user update "
        f"| admin_id={current_user.id} "
        f"| user_id={user_id}"
    )

    user = db.query(User).filter(
        User.id == user_id,
        User.deleted_at.is_(None)
    ).first()

    if not user:

        logger.warning(
            f"User update failed - user not found "
            f"| admin_id={current_user.id} "
            f"| user_id={user_id}"
        )

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    update_data = user_data.model_dump(
        exclude_unset=True
    )

    # -----------------------------------------------------
    # Check email uniqueness
    # -----------------------------------------------------

    if "email" in update_data:

        existing_user = db.query(User).filter(
            User.email == update_data["email"],
            User.id != user_id
        ).first()

        if existing_user:

            logger.warning(
                f"User update failed - email already in use "
                f"| admin_id={current_user.id} "
                f"| user_id={user_id}"
            )

            raise HTTPException(
                status_code=400,
                detail="Email already in use"
            )

    # -----------------------------------------------------
    # Update fields
    # -----------------------------------------------------

    for field, value in update_data.items():
        setattr(user, field, value)

    try:

        db.commit()
        db.refresh(user)

        logger.info(
            f"User updated successfully "
            f"| admin_id={current_user.id} "
            f"| user_id={user_id}"
        )

    except Exception:

        db.rollback()

        logger.exception(
            f"User update failed "
            f"| admin_id={current_user.id} "
            f"| user_id={user_id}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to update user"
        )

    return user


@router.delete(
    "/{user_id}"
)
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):

    logger.info(
        f"Admin requested user deletion "
        f"| admin_id={current_user.id} "
        f"| user_id={user_id}"
    )

    # -----------------------------------------------------
    # Find user
    # -----------------------------------------------------

    user = db.query(User).filter(
        User.id == user_id,
        User.deleted_at.is_(None)
    ).first()

    if not user:

        logger.warning(
            f"User deletion failed - user not found "
            f"| admin_id={current_user.id} "
            f"| user_id={user_id}"
        )

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # -----------------------------------------------------
    # Prevent admin from deleting himself
    # -----------------------------------------------------

    if user.id == current_user.id:

        logger.warning(
            f"Admin attempted to delete own account "
            f"| admin_id={current_user.id}"
        )

        raise HTTPException(
            status_code=400,
            detail="Admins cannot delete their own account"
        )

    # -----------------------------------------------------
    # Soft delete
    # -----------------------------------------------------

    user.deleted_at = datetime.utcnow()

    try:

        db.commit()

        logger.info(
            f"User deleted successfully "
            f"| admin_id={current_user.id} "
            f"| user_id={user_id} "
            f"| deleted_at={user.deleted_at}"
        )

    except Exception:

        db.rollback()

        logger.exception(
            f"User deletion failed "
            f"| admin_id={current_user.id} "
            f"| user_id={user_id}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to delete user"
        )

    return {
        "message": "User deleted successfully",
        "deleted_at": user.deleted_at
    }