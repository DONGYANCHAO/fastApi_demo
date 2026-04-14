"""
通知服务模块
提供各种场景下的通知创建功能
"""
from sqlalchemy.orm import Session
from typing import Optional, List
from sql_app.cruds.notification import create_notification
from sql_app.schemas.schemas_notification import NotificationType


class NotificationService:
    """通知服务类"""
    
    @staticmethod
    def notify_task_assigned(db: Session, task_id: int, task_title: str, assignee_id: int, assigner_id: int):
        """任务被分配时通知执行者"""
        return create_notification(
            db=db,
            recipient_id=assignee_id,
            sender_id=assigner_id,
            type=NotificationType.TASK,
            title="新任务分配",
            content=f"您被分配了一个新任务：{task_title}",
            related_id=task_id
        )
    
    @staticmethod
    def notify_task_status_changed(
        db: Session, 
        task_id: int, 
        task_title: str, 
        new_status: str, 
        notify_user_ids: List[int],
        changer_id: int
    ):
        """任务状态变更时通知相关人员"""
        notifications = []
        for user_id in notify_user_ids:
            if user_id != changer_id:  # 不通知操作者自己
                notif = create_notification(
                    db=db,
                    recipient_id=user_id,
                    sender_id=changer_id,
                    type=NotificationType.TASK,
                    title="任务状态变更",
                    content=f"任务「{task_title}」状态已变更为：{new_status}",
                    related_id=task_id
                )
                notifications.append(notif)
        return notifications
    
    @staticmethod
    def notify_project_new_member(
        db: Session, 
        project_id: int, 
        project_name: str, 
        new_member_name: str,
        notify_user_ids: List[int],
        operator_id: int
    ):
        """项目有新成员加入时通知所有人"""
        notifications = []
        for user_id in notify_user_ids:
            if user_id != operator_id:  # 不通知操作者自己
                notif = create_notification(
                    db=db,
                    recipient_id=user_id,
                    sender_id=operator_id,
                    type=NotificationType.PROJECT,
                    title="项目新成员",
                    content=f"{new_member_name} 加入了项目「{project_name}」",
                    related_id=project_id
                )
                notifications.append(notif)
        return notifications
    
    @staticmethod
    def notify_comment_reply(
        db: Session, 
        comment_id: int,
        comment_content: str,
        replied_user_id: int,
        replier_id: int,
        related_type: str,  # 'task' 或 'project'
        related_id: int,
        related_title: str
    ):
        """评论回复时通知被回复者"""
        return create_notification(
            db=db,
            recipient_id=replied_user_id,
            sender_id=replier_id,
            type=NotificationType.COMMENT,
            title=f"收到新的回复",
            content=f"您在「{related_title}」中的评论收到了回复：{comment_content[:50]}...",
            related_id=related_id
        )
    
    @staticmethod
    def notify_system_announcement(
        db: Session, 
        title: str, 
        content: str,
        notify_all_users: bool = True,
        specific_user_ids: Optional[List[int]] = None
    ):
        """系统公告
        
        Args:
            db: 数据库会话
            title: 公告标题
            content: 公告内容
            notify_all_users: 是否通知所有用户
            specific_user_ids: 指定用户ID列表（当 notify_all_users=False 时使用）
        """
        from sql_app.cruds.users import get_users
        
        notifications = []
        
        if notify_all_users:
            # 获取所有用户
            users = get_users(db, skip=0, limit=10000)
            user_ids = [user.id for user in users]
        else:
            user_ids = specific_user_ids or []
        
        for user_id in user_ids:
            notif = create_notification(
                db=db,
                recipient_id=user_id,
                sender_id=None,  # 系统通知没有发送者
                type=NotificationType.SYSTEM,
                title=title,
                content=content,
                related_id=None
            )
            notifications.append(notif)
        
        return notifications
    
    @staticmethod
    def notify_new_message(
        db: Session,
        sender_id: int,
        recipient_id: int,
        message_content: str
    ):
        """新消息通知（在发送私信时自动创建）"""
        from sql_app.cruds.users import get_user
        
        sender = get_user(db, user_id=sender_id)
        sender_name = sender.username if sender else "未知用户"
        
        return create_notification(
            db=db,
            recipient_id=recipient_id,
            sender_id=sender_id,
            type=NotificationType.MESSAGE,
            title=f"收到来自 {sender_name} 的新消息",
            content=message_content[:100] + "..." if len(message_content) > 100 else message_content,
            related_id=None
        )
