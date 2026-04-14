from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from sql_app.models import NotificationType


class NotificationBase(BaseModel):
    recipient_id: int
    sender_id: Optional[int] = None
    type: NotificationType = NotificationType.system
    title: str
    content: str
    related_id: Optional[int] = None


class NotificationCreate(NotificationBase):
    pass


class Notification(NotificationBase):
    id: int
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class MessageBase(BaseModel):
    recipient_id: int
    content: str


class MessageCreate(MessageBase):
    pass


class Message(MessageBase):
    id: int
    sender_id: int
    is_read: bool
    created_at: datetime

    class Config:
        orm_mode = True


class Conversation(BaseModel):
    user_id: int
    username: str
    avatar: Optional[str] = None
    last_message: Optional[str] = None
    last_message_time: Optional[datetime] = None
    unread_count: int = 0

    class Config:
        orm_mode = True
