from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sql_app.database import get_db
from sql_app.schemas import schemas_notification
from routers.auth import get_current_active_user
from sql_app.schemas.schemas_user import User
from sql_app.cruds import notifications as notification_crud
from sql_app.models import NotificationType

router = APIRouter()


@router.get("/api/notifications/", response_model=List[schemas_notification.Notification])
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    is_read: Optional[bool] = None,
    notification_type: Optional[NotificationType] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return notification_crud.get_notifications(
        db, 
        recipient_id=current_user.id, 
        skip=skip, 
        limit=limit,
        is_read=is_read,
        notification_type=notification_type
    )


@router.get("/api/notifications/unread-count")
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    count = notification_crud.get_unread_notification_count(db, recipient_id=current_user.id)
    return {"unread_count": count}


@router.put("/api/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    notification = notification_crud.mark_notification_read(
        db, 
        notification_id=notification_id, 
        recipient_id=current_user.id
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"msg": "Notification marked as read"}


@router.put("/api/notifications/read-all")
async def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    count = notification_crud.mark_all_notifications_read(db, recipient_id=current_user.id)
    return {"msg": f"Marked {count} notifications as read"}


@router.delete("/api/notifications/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = notification_crud.delete_notification(
        db, 
        notification_id=notification_id, 
        recipient_id=current_user.id
    )
    if result <= 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"msg": "Notification deleted successfully"}
