from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sql_app import cruds
from sql_app.database import get_db
from sql_app.schemas import schemas_notification, schemas_user
from routers.auth import get_current_active_user

router = APIRouter()


# ==================== 通知相关接口 ====================

@router.get("/api/notifications/", response_model=List[schemas_notification.NotificationWithSender])
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: schemas_user.User = Depends(get_current_active_user)
):
    """获取我的通知列表"""
    notifications = cruds.get_notifications(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        unread_only=unread_only
    )
    
    # 添加发送者信息
    result = []
    for notification in notifications:
        notif_dict = {
            "id": notification.id,
            "recipient_id": notification.recipient_id,
            "sender_id": notification.sender_id,
            "type": notification.type,
            "title": notification.title,
            "content": notification.content,
            "related_id": notification.related_id,
            "is_read": notification.is_read,
            "created_at": notification.created_at,
            "read_at": notification.read_at,
            "sender_username": None,
            "sender_avatar": None
        }
        
        if notification.sender_id:
            sender = cruds.get_user(db, user_id=notification.sender_id)
            if sender:
                notif_dict["sender_username"] = sender.username
                notif_dict["sender_avatar"] = sender.avatar
        
        result.append(schemas_notification.NotificationWithSender(**notif_dict))
    
    return result


@router.get("/api/notifications/unread-count", response_model=schemas_notification.UnreadCount)
async def get_unread_notification_count(
    db: Session = Depends(get_db),
    current_user: schemas_user.User = Depends(get_current_active_user)
):
    """获取未读通知数量"""
    count = cruds.get_unread_notification_count(db, user_id=current_user.id)
    return {"count": count}


@router.put("/api/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: schemas_user.User = Depends(get_current_active_user)
):
    """标记单条通知为已读"""
    success = cruds.mark_notification_as_read(
        db, notification_id=notification_id, user_id=current_user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found or already read")
    return {"msg": "Notification marked as read"}


@router.put("/api/notifications/read-all")
async def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: schemas_user.User = Depends(get_current_active_user)
):
    """标记所有通知为已读"""
    count = cruds.mark_all_notifications_as_read(db, user_id=current_user.id)
    return {"msg": f"Marked {count} notifications as read"}


@router.delete("/api/notifications/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: schemas_user.User = Depends(get_current_active_user)
):
    """删除通知"""
    success = cruds.delete_notification(
        db, notification_id=notification_id, user_id=current_user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"msg": "Notification deleted successfully"}


# ==================== 消息相关接口 ====================

@router.get("/api/messages/", response_model=List[schemas_notification.ConversationItem])
async def get_conversations(
    db: Session = Depends(get_db),
    current_user: schemas_user.User = Depends(get_current_active_user)
):
    """获取消息列表（会话模式）"""
    conversations = cruds.get_conversations(db, user_id=current_user.id)
    return conversations


@router.get("/api/messages/conversation/{user_id}", response_model=List[schemas_notification.MessageWithUser])
async def get_conversation_messages(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: schemas_user.User = Depends(get_current_active_user)
):
    """获取与某用户的聊天记录"""
    # 检查用户是否存在
    other_user = cruds.get_user(db, user_id=user_id)
    if not other_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    messages = cruds.get_conversation_messages(
        db=db,
        user_id=current_user.id,
        other_user_id=user_id,
        skip=skip,
        limit=limit
    )
    
    # 添加用户信息
    result = []
    for message in messages:
        sender = cruds.get_user(db, user_id=message.sender_id)
        recipient = cruds.get_user(db, user_id=message.recipient_id)
        
        msg_dict = {
            "id": message.id,
            "sender_id": message.sender_id,
            "recipient_id": message.recipient_id,
            "content": message.content,
            "is_read": message.is_read,
            "created_at": message.created_at,
            "read_at": message.read_at,
            "sender_username": sender.username if sender else "Unknown",
            "sender_avatar": sender.avatar if sender else None,
            "recipient_username": recipient.username if recipient else "Unknown",
            "recipient_avatar": recipient.avatar if recipient else None
        }
        result.append(schemas_notification.MessageWithUser(**msg_dict))
    
    # 标记该会话的消息为已读
    cruds.mark_conversation_as_read(db, user_id=current_user.id, sender_id=user_id)
    
    return result


@router.post("/api/messages/", response_model=schemas_notification.MessageWithUser)
async def send_message(
    message: schemas_notification.MessageCreate,
    db: Session = Depends(get_db),
    current_user: schemas_user.User = Depends(get_current_active_user)
):
    """发送私信"""
    # 不能给自己发送消息
    if message.recipient_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot send message to yourself")
    
    # 检查接收者是否存在
    recipient = cruds.get_user(db, user_id=message.recipient_id)
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    
    # 创建消息
    db_message = cruds.create_message(
        db=db,
        sender_id=current_user.id,
        recipient_id=message.recipient_id,
        content=message.content
    )
    
    # 构建响应
    sender = cruds.get_user(db, user_id=current_user.id)
    msg_dict = {
        "id": db_message.id,
        "sender_id": db_message.sender_id,
        "recipient_id": db_message.recipient_id,
        "content": db_message.content,
        "is_read": db_message.is_read,
        "created_at": db_message.created_at,
        "read_at": db_message.read_at,
        "sender_username": sender.username if sender else "Unknown",
        "sender_avatar": sender.avatar if sender else None,
        "recipient_username": recipient.username,
        "recipient_avatar": recipient.avatar
    }
    
    # 创建通知给接收者
    cruds.create_notification(
        db=db,
        recipient_id=message.recipient_id,
        type=schemas_notification.NotificationType.MESSAGE,
        title=f"收到来自 {sender.username} 的新消息",
        content=message.content[:100] + "..." if len(message.content) > 100 else message.content,
        sender_id=current_user.id
    )
    
    return schemas_notification.MessageWithUser(**msg_dict)


@router.get("/api/messages/unread-count", response_model=schemas_notification.UnreadCount)
async def get_unread_message_count(
    db: Session = Depends(get_db),
    current_user: schemas_user.User = Depends(get_current_active_user)
):
    """获取未读消息数量"""
    count = cruds.get_unread_message_count(db, user_id=current_user.id)
    return {"count": count}


@router.put("/api/messages/{message_id}/read")
async def mark_message_as_read(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: schemas_user.User = Depends(get_current_active_user)
):
    """标记消息为已读"""
    success = cruds.mark_message_as_read(
        db, message_id=message_id, user_id=current_user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Message not found or already read")
    return {"msg": "Message marked as read"}
