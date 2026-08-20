from typing import Any

from sqlalchemy.orm import Session

from app.models.notification import Notification


def create_notification(
    db: Session,
    user_id: str,
    type: str,
    reference_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> Notification:
    """
    Builds a Notification object and stages it in the session
    (db.add). Does NOT commit — the caller must commit as part
    of its own transaction, so the notification and the event
    that triggered it (e.g. proposal creation) succeed or fail
    together, atomically.
    """

    notification = Notification(
        user_id=user_id,
        type=type,
        reference_id=reference_id,
        payload=payload,
    )

    db.add(notification)

    return notification