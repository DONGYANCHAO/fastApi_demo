from sqlalchemy.orm import Session
from sql_app.cruds import notifications as notification_crud
from sql_app.schemas import schemas_notification
from sql_app.models import NotificationType


def notify_task_assigned(db: Session, recipient_id: int, sender_id: int, task_id: int, task_title: str):
    notification = schemas_notification.NotificationCreate(
        recipient_id=recipient_id,
        sender_id=sender_id,
        type=NotificationType.task,
        title="新任务分配",
        content=f"您被分配了一个新任务: {task_title}",
        related_id=task_id
    )
    return notification_crud.create_notification(db, notification)


def notify_task_status_changed(db: Session, recipient_id: int, sender_id: int, task_id: int, task_title: str, new_status: str):
    notification = schemas_notification.NotificationCreate(
        recipient_id=recipient_id,
        sender_id=sender_id,
        type=NotificationType.task,
        title="任务状态变更",
        content=f"任务 '{task_title}' 状态已变更为: {new_status}",
        related_id=task_id
    )
    return notification_crud.create_notification(db, notification)


def notify_project_member_joined(db: Session, recipient_id: int, sender_id: int, project_id: int, project_name: str, new_member_name: str):
    notification = schemas_notification.NotificationCreate(
        recipient_id=recipient_id,
        sender_id=sender_id,
        type=NotificationType.project,
        title="项目成员变更",
        content=f"项目 '{project_name}' 新增成员: {new_member_name}",
        related_id=project_id
    )
    return notification_crud.create_notification(db, notification)


def notify_comment_reply(db: Session, recipient_id: int, sender_id: int, comment_id: int, comment_content: str):
    notification = schemas_notification.NotificationCreate(
        recipient_id=recipient_id,
        sender_id=sender_id,
        type=NotificationType.comment,
        title="评论回复",
        content=f"有人回复了您的评论: {comment_content[:50]}...",
        related_id=comment_id
    )
    return notification_crud.create_notification(db, notification)


def notify_system_announcement(db: Session, recipient_id: int, title: str, content: str):
    notification = schemas_notification.NotificationCreate(
        recipient_id=recipient_id,
        sender_id=None,
        type=NotificationType.system,
        title=title,
        content=content,
        related_id=None
    )
    return notification_crud.create_notification(db, notification)


def notify_system_announcement_all(db: Session, recipient_ids: list, title: str, content: str):
    notifications = []
    for recipient_id in recipient_ids:
        notification = notify_system_announcement(db, recipient_id, title, content)
        notifications.append(notification)
    return notifications
