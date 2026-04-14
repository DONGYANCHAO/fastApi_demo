from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base


class NotificationType(str, enum.Enum):
    system = "system"
    task = "task"
    project = "project"
    comment = "comment"
    message = "message"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String)
    avatar = Column(String, default=None)
    hashed_password = Column(String)
    role = Column(String, default="general")
    is_active = Column(Boolean, default=True)
    frequency_max = Column(Integer, default=600)

    todos = relationship("ToDo", back_populates="owner_todo")
    notifications_received = relationship("Notification", back_populates="recipient", foreign_keys="Notification.recipient_id")
    notifications_sent = relationship("Notification", back_populates="sender", foreign_keys="Notification.sender_id")
    messages_sent = relationship("Message", back_populates="sender", foreign_keys="Message.sender_id")
    messages_received = relationship("Message", back_populates="recipient", foreign_keys="Message.recipient_id")


class ToDo(Base):
    __tablename__ = "todo_info"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    done = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner_todo = relationship("User", back_populates="todos")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    type = Column(SQLEnum(NotificationType), nullable=False, default=NotificationType.system)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    related_id = Column(Integer, nullable=True)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    read_at = Column(DateTime, nullable=True)

    recipient = relationship("User", back_populates="notifications_received", foreign_keys=[recipient_id])
    sender = relationship("User", back_populates="notifications_sent", foreign_keys=[sender_id])


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(String, nullable=False)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    sender = relationship("User", back_populates="messages_sent", foreign_keys=[sender_id])
    recipient = relationship("User", back_populates="messages_received", foreign_keys=[recipient_id])
