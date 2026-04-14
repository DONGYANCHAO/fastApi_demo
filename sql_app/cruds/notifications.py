from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, desc
from typing import List, Optional
from datetime import datetime
from .. import models
from ..schemas import schemas_notification
from sql_app.models import NotificationType


def create_notification(db: Session, notification: schemas_notification.NotificationCreate) -> models.Notification:
    db_notification = models.Notification(**notification.dict())
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification


def get_notifications(
    db: Session, 
    recipient_id: int, 
    skip: int = 0, 
    limit: int = 20,
    is_read: Optional[bool] = None,
    notification_type: Optional[NotificationType] = None
) -> List[models.Notification]:
    query = db.query(models.Notification).filter(models.Notification.recipient_id == recipient_id)
    if is_read is not None:
        query = query.filter(models.Notification.is_read == is_read)
    if notification_type:
        query = query.filter(models.Notification.type == notification_type)
    return query.order_by(desc(models.Notification.created_at)).offset(skip).limit(limit).all()


def get_unread_notification_count(db: Session, recipient_id: int) -> int:
    return db.query(models.Notification).filter(
        models.Notification.recipient_id == recipient_id,
        models.Notification.is_read == False
    ).count()


def mark_notification_read(db: Session, notification_id: int, recipient_id: int) -> Optional[models.Notification]:
    notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.recipient_id == recipient_id
    ).first()
    if notification:
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        db.commit()
        db.refresh(notification)
    return notification


def mark_all_notifications_read(db: Session, recipient_id: int) -> int:
    result = db.query(models.Notification).filter(
        models.Notification.recipient_id == recipient_id,
        models.Notification.is_read == False
    ).update({"is_read": True, "read_at": datetime.utcnow()})
    db.commit()
    return result


def delete_notification(db: Session, notification_id: int, recipient_id: int) -> int:
    result = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.recipient_id == recipient_id
    ).delete()
    db.commit()
    return result


def create_message(db: Session, sender_id: int, message: schemas_notification.MessageCreate) -> models.Message:
    db_message = models.Message(
        sender_id=sender_id,
        recipient_id=message.recipient_id,
        content=message.content
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def get_conversation(
    db: Session, 
    user_id: int, 
    other_user_id: int, 
    skip: int = 0, 
    limit: int = 50
) -> List[models.Message]:
    return db.query(models.Message).filter(
        or_(
            and_(models.Message.sender_id == user_id, models.Message.recipient_id == other_user_id),
            and_(models.Message.sender_id == other_user_id, models.Message.recipient_id == user_id)
        )
    ).order_by(desc(models.Message.created_at)).offset(skip).limit(limit).all()


def get_conversations(db: Session, user_id: int) -> List[dict]:
    messages = db.query(models.Message).filter(
        or_(models.Message.sender_id == user_id, models.Message.recipient_id == user_id)
    ).order_by(desc(models.Message.created_at)).all()
    
    conversation_map = {}
    for msg in messages:
        other_user_id = msg.recipient_id if msg.sender_id == user_id else msg.sender_id
        if other_user_id not in conversation_map:
            conversation_map[other_user_id] = msg
    
    results = []
    for other_user_id, last_message in conversation_map.items():
        unread_count = db.query(models.Message).filter(
            models.Message.sender_id == other_user_id,
            models.Message.recipient_id == user_id,
            models.Message.is_read == False
        ).count()
        
        other_user = db.query(models.User).filter(models.User.id == other_user_id).first()
        
        results.append({
            "user_id": other_user_id,
            "username": other_user.username if other_user else "Unknown",
            "avatar": other_user.avatar if other_user else None,
            "last_message": last_message.content,
            "last_message_time": last_message.created_at,
            "unread_count": unread_count
        })
    
    results.sort(key=lambda x: x["last_message_time"], reverse=True)
    return results


def get_unread_message_count(db: Session, recipient_id: int) -> int:
    return db.query(models.Message).filter(
        models.Message.recipient_id == recipient_id,
        models.Message.is_read == False
    ).count()


def mark_message_read(db: Session, message_id: int, recipient_id: int) -> Optional[models.Message]:
    message = db.query(models.Message).filter(
        models.Message.id == message_id,
        models.Message.recipient_id == recipient_id
    ).first()
    if message:
        message.is_read = True
        db.commit()
        db.refresh(message)
    return message


def mark_conversation_read(db: Session, user_id: int, other_user_id: int) -> int:
    result = db.query(models.Message).filter(
        models.Message.sender_id == other_user_id,
        models.Message.recipient_id == user_id,
        models.Message.is_read == False
    ).update({"is_read": True})
    db.commit()
    return result
