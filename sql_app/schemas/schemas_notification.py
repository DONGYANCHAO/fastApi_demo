from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# 通知类型枚举
class NotificationType:
    SYSTEM = "system"
    TASK = "task"
    PROJECT = "project"
    COMMENT = "comment"
    MESSAGE = "message"


# 基础通知模型
class NotificationBase(BaseModel):
    type: str
    title: str
    content: Optional[str] = None
    related_id: Optional[int] = None


# 创建通知
class NotificationCreate(NotificationBase):
    recipient_id: int
    sender_id: Optional[int] = None


# 通知响应模型
class Notification(NotificationBase):
    id: int
    recipient_id: int
    sender_id: Optional[int] = None
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 通知列表项（包含发送者信息）
class NotificationWithSender(Notification):
    sender_username: Optional[str] = None
    sender_avatar: Optional[str] = None


# 基础消息模型
class MessageBase(BaseModel):
    content: str


# 创建消息
class MessageCreate(MessageBase):
    recipient_id: int


# 消息响应模型
class Message(MessageBase):
    id: int
    sender_id: int
    recipient_id: int
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 消息列表项（包含发送者/接收者信息）
class MessageWithUser(Message):
    sender_username: str
    sender_avatar: Optional[str] = None
    recipient_username: str
    recipient_avatar: Optional[str] = None


# 会话列表项
class ConversationItem(BaseModel):
    user_id: int
    username: str
    avatar: Optional[str] = None
    last_message: str
    last_message_time: datetime
    unread_count: int


# 未读数量响应
class UnreadCount(BaseModel):
    count: int
