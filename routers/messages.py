from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sql_app.database import get_db
from sql_app.schemas import schemas_notification
from routers.auth import get_current_active_user
from sql_app.schemas.schemas_user import User
from sql_app.cruds import notifications as message_crud
from sql_app.cruds import users as user_crud

router = APIRouter()


@router.get("/api/messages/", response_model=List[schemas_notification.Conversation])
async def get_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return message_crud.get_conversations(db, user_id=current_user.id)


@router.get("/api/messages/conversation/{user_id}", response_model=List[schemas_notification.Message])
async def get_conversation(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    other_user = user_crud.get_user(db, user_id=user_id)
    if not other_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    message_crud.mark_conversation_read(db, user_id=current_user.id, other_user_id=user_id)
    
    messages = message_crud.get_conversation(
        db, 
        user_id=current_user.id, 
        other_user_id=user_id, 
        skip=skip, 
        limit=limit
    )
    return messages


@router.post("/api/messages/", response_model=schemas_notification.Message)
async def send_message(
    message: schemas_notification.MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    recipient = user_crud.get_user(db, user_id=message.recipient_id)
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    
    if message.recipient_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot send message to yourself")
    
    return message_crud.create_message(db, sender_id=current_user.id, message=message)


@router.get("/api/messages/unread-count")
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    count = message_crud.get_unread_message_count(db, recipient_id=current_user.id)
    return {"unread_count": count}


@router.put("/api/messages/{message_id}/read")
async def mark_message_read(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    message = message_crud.mark_message_read(
        db, 
        message_id=message_id, 
        recipient_id=current_user.id
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"msg": "Message marked as read"}
