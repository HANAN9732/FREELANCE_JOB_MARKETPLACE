from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    type: str
    reference_id: str | None
    payload: dict[str, Any] | None
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]
    total: int
    unread_count: int


class NotificationReadResponse(BaseModel):
    message: str
    notification: NotificationResponse