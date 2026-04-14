from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, or_, and_
from typing import List, Optional
from datetime import datetime

from sql_app import models


# ==================== 通知相关操作 ====================

def create_notification(
    db: Session,
    recipient_id: int,
    type: str,
    title: str,
    content: Optional[str] = None,
    sender_id: Optional[int] = None,
    related_id: Optional[int] = None
) -> models.Notification:
    """创建通知"""
    db_notification = models.Notification(
        recipient_id=recipient_id,
        sender_id=sender_id,
        type=type,
        title=title,
        content=content,
        related_id=related_id,
        is_read=False,
        created_at=datetime.utcnow()
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification


def get_notifications(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False
) -> List[models.Notification]:
    """获取用户的通知列表"""
    query = db.query(models.Notification).filter(
        models.Notification.recipient_id == user_id
    )
    
    if unread_only:
        query = query.filter(models.Notification.is_read == False)
    
    return query.order_by(desc(models.Notification.created_at)).offset(skip).limit(limit).all()


def get_notification_by_id(db: Session, notification_id: int) -> Optional[models.Notification]:
    """根据ID获取通知"""
    return db.query(models.Notification).filter(models.Notification.id == notification_id).first()


def get_unread_notification_count(db: Session, user_id: int) -> int:
    """获取未读通知数量"""
    return db.query(func.count(models.Notification.id)).filter(
        models.Notification.recipient_id == user_id,
        models.Notification.is_read == False
    ).scalar()


def mark_notification_as_read(db: Session, notification_id: int, user_id: int) -> bool:
    """标记通知为已读"""
    notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.recipient_id == user_id
    ).first()
    
    if notification and not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        db.commit()
        return True
    return False


def mark_all_notifications_as_read(db: Session, user_id: int) -> int:
    """标记所有通知为已读，返回更新的数量"""
    result = db.query(models.Notification).filter(
        models.Notification.recipient_id == user_id,
        models.Notification.is_read == False
    ).update({
        "is_read": True,
        "read_at": datetime.utcnow()
    })
    db.commit()
    return result


def delete_notification(db: Session, notification_id: int, user_id: int) -> bool:
    """删除通知"""
    notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.recipient_id == user_id
    ).first()
    
    if notification:
        db.delete(notification)
        db.commit()
        return True
    return False


# ==================== 消息相关操作 ====================

def create_message(
    db: Session,
    sender_id: int,
    recipient_id: int,
    content: str
) -> models.Message:
    """创建私信"""
    db_message = models.Message(
        sender_id=sender_id,
        recipient_id=recipient_id,
        content=content,
        is_read=False,
        created_at=datetime.utcnow()
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def get_conversations(db: Session, user_id: int) -> List[dict]:
    """获取用户的会话列表（与谁聊过天）"""
    # 子查询：获取每个会话的最新消息
    from sqlalchemy import union, literal_column
    
    # 获取用户作为发送者或接收者的所有消息
    messages = db.query(models.Message).filter(
        or_(
            models.Message.sender_id == user_id,
            models.Message.recipient_id == user_id
        )
    ).order_by(desc(models.Message.created_at)).all()
    
    # 按用户分组，获取每个用户的最新消息
    conversations = {}
    for msg in messages:
        other_user_id = msg.recipient_id if msg.sender_id == user_id else msg.sender_id
        if other_user_id not in conversations:
            conversations[other_user_id] = msg
    
    # 获取用户信息
    result = []
    for other_user_id, last_msg in conversations.items():
        user = db.query(models.User).filter(models.User.id == other_user_id).first()
        if user:
            unread_count = db.query(func.count(models.Message.id)).filter(
                models.Message.sender_id == other_user_id,
                models.Message.recipient_id == user_id,
                models.Message.is_read == False
            ).scalar()
            
            result.append({
                "user_id": user.id,
                "username": user.username,
                "avatar": user.avatar,
                "last_message": last_msg.content,
                "last_message_time": last_msg.created_at,
                "unread_count": unread_count
            })
    
    # 按最后消息时间排序
    result.sort(key=lambda x: x["last_message_time"], reverse=True)
    return result


def get_conversation_messages(
    db: Session,
    user_id: int,
    other_user_id: int,
    skip: int = 0,
    limit: int = 50
) -> List[models.Message]:
    """获取与某用户的聊天记录"""
    return db.query(models.Message).filter(
        or_(
            and_(
                models.Message.sender_id == user_id,
                models.Message.recipient_id == other_user_id
            ),
            and_(
                models.Message.sender_id == other_user_id,
                models.Message.recipient_id == user_id
            )
        )
    ).order_by(desc(models.Message.created_at)).offset(skip).limit(limit).all()


def get_unread_message_count(db: Session, user_id: int) -> int:
    """获取未读消息数量"""
    return db.query(func.count(models.Message.id)).filter(
        models.Message.recipient_id == user_id,
        models.Message.is_read == False
    ).scalar()


def mark_message_as_read(db: Session, message_id: int, user_id: int) -> bool:
    """标记消息为已读"""
    message = db.query(models.Message).filter(
        models.Message.id == message_id,
        models.Message.recipient_id == user_id
    ).first()
    
    if message and not message.is_read:
        message.is_read = True
        message.read_at = datetime.utcnow()
        db.commit()
        return True
    return False


def mark_conversation_as_read(db: Session, user_id: int, sender_id: int) -> int:
    """标记与某用户的所有消息为已读"""
    result = db.query(models.Message).filter(
        models.Message.sender_id == sender_id,
        models.Message.recipient_id == user_id,
        models.Message.is_read == False
    ).update({
        "is_read": True,
        "read_at": datetime.utcnow()
    })
    db.commit()
    return result
