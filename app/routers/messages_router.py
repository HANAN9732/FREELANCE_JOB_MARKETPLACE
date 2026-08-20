from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi import Query
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_db,
    get_current_user,
)
from app.core.logger import logger

from app.models.user import User
from app.models.job import Job
from app.models.message import Message

from app.schemas.message import (
    MessageCreate,
    MessageResponse,
)


router = APIRouter(
    prefix="/jobs",
    tags=["Messages"]
)


def get_messaging_job(
    job_id: str,
    current_user: User,
    db: Session
):

    job = db.query(Job).filter(
        Job.id == job_id,
        Job.is_deleted == False
    ).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    # Only the client or assigned freelancer
    # can access the conversation
    if (
        job.client_id != current_user.id
        and job.assigned_freelancer_id != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You are not part of this job conversation"
        )

    return job


@router.get(
    "/{job_id}/messages",
    response_model=list[MessageResponse]
)
def get_messages(
    job_id: str,

    page: int = Query(
        1,
        ge=1,
        description="Page number"
    ),

    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Number of messages per page"
    ),

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):
    # -----------------------------------
    # 1. Check job + ownership
    #    (client or assigned freelancer)
    # -----------------------------------

    job = get_messaging_job(
        job_id,
        current_user,
        db
    )

    # -----------------------------------
    # 2. Check job is in a messaging-
    #    eligible state
    # -----------------------------------

    if job.status not in [
        "assigned",
        "in_progress",
        "completed"
    ]:
        raise HTTPException(
            status_code=400,
            detail="Messaging is not available for this job"
        )

    # -----------------------------------
    # 3. Calculate offset
    # -----------------------------------

    offset = (page - 1) * limit

    # -----------------------------------
    # 4. Get messages
    # -----------------------------------

    messages = (
        db.query(Message)
        .filter(
            Message.job_id == job_id
        )
        .order_by(
            Message.created_at.asc()
        )
        .offset(offset)
        .limit(limit)
        .all()
    )

    # -----------------------------------
    # 5. Mark incoming unread messages
    #    as read (auto mark-as-read)
    #    - Only messages sent by the
    #      OTHER party
    #    - Only if not already read
    # -----------------------------------

    unread_incoming_ids = [
        message.id
        for message in messages
        if message.sender_id != current_user.id
        and message.read_at is None
    ]

    if unread_incoming_ids:

        db.query(Message).filter(
            Message.id.in_(unread_incoming_ids)
        ).update(
            {
                Message.read_at: datetime.utcnow()
            },
            synchronize_session=False
        )

        db.commit()

        # Refresh in-memory objects so the
        # response reflects the updated
        # read_at values instead of stale None
        for message in messages:
            if message.id in unread_incoming_ids:
                db.refresh(message)

        logger.info(f"Messages marked as read | job_id={job_id} | by user_id={current_user.id} | count={len(unread_incoming_ids)}")

    return messages


@router.post(
    "/{job_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED
)
def send_message(
    job_id: str,
    message_data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    job = get_messaging_job(
        job_id,
        current_user,
        db
    )

    if job.status not in ["assigned", "in_progress"]:
        raise HTTPException(
            status_code=400,
            detail="Messages cannot be sent for this job"
        )

    message = Message(
        job_id=job.id,
        sender_id=current_user.id,
        content=message_data.content.strip()
    )

    db.add(message)

    db.commit()
    db.refresh(message)

    logger.info(f"Message sent | job_id={job.id} | by user_id={current_user.id} | message_id={message.id}")

    return message