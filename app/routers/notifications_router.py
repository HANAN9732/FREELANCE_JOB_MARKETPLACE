from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_db,
    get_current_user,
)
from app.core.logger import logger

from app.models.user import User
from app.models.notification import Notification

from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationReadResponse,
)

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)


@router.get(
    "/",
    response_model=NotificationListResponse
)
def get_notifications(
    unread_only: bool = False,

    page: int = Query(
        1,
        ge=1,
        description="Page number"
    ),

    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Number of notifications per page"
    ),

    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    query = db.query(Notification).filter(
        Notification.user_id == current_user.id
    )

    if unread_only:
        query = query.filter(Notification.is_read == False)

    total = query.count()

    unread_count = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        )
        .count()
    )

    offset = (page - 1) * limit

    notifications = (
        query
        .order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "notifications": notifications,
        "total": total,
        "unread_count": unread_count
    }


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationReadResponse
)
def mark_notification_as_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )

    if not notification.is_read:
        notification.is_read = True

        db.commit()
        db.refresh(notification)

        logger.info(f"Notification marked as read | notification_id={notification.id} | by user_id={current_user.id}")

    return {
        "message": "Notification marked as read",
        "notification": notification
    }


@router.patch(
    "/read-all"
)
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    updated_count = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        )
        .update(
            {
                Notification.is_read: True
            },
            synchronize_session=False
        )
    )

    db.commit()

    logger.info(f"All notifications marked as read | by user_id={current_user.id} | updated_count={updated_count}")

    return {
        "message": "All notifications marked as read",
        "updated_count": updated_count
    }