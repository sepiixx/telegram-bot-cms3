# ==========================================
# MODULE: REPOSITORY LAYER
# PURPOSE: Abstract database operations
# ==========================================

from typing import List, Optional, Generic, TypeVar, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from app.models import (
    User, Button, MediaFile, Channel, UserChannelMembership,
    SupportTicket, BroadcastCampaign, BroadcastReceipt, ScheduledTask,
    AdminUser, UserPointsHistory, AdminActivityLog
)

# ========== Generic TypeVar for Generic Repository ==========
T = TypeVar('T')


# ==========================================
# BASE REPOSITORY
# PURPOSE: Generic database operations
# ==========================================

class BaseRepository(Generic[T]):
    """
    Generic repository for common CRUD operations.
    All specific repositories inherit from this.
    """

    def __init__(self, db: Session, model: type):
        """
        Initialize repository with database session and model.
        
        Args:
            db: SQLAlchemy session
            model: SQLAlchemy model class
        """
        self.db = db
        self.model = model

    def create(self, obj_in: Dict[str, Any]) -> T:
        """Create a new record"""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_by_id(self, obj_id: int) -> Optional[T]:
        """Get record by ID"""
        return self.db.query(self.model).filter(self.model.id == obj_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all records with pagination"""
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def update(self, obj_id: int, obj_in: Dict[str, Any]) -> Optional[T]:
        """Update a record"""
        db_obj = self.get_by_id(obj_id)
        if db_obj:
            for key, value in obj_in.items():
                if hasattr(db_obj, key):
                    setattr(db_obj, key, value)
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj

    def delete(self, obj_id: int) -> bool:
        """Delete a record"""
        db_obj = self.get_by_id(obj_id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False

    def count(self) -> int:
        """Count total records"""
        return self.db.query(self.model).count()


# ==========================================
# USER REPOSITORY
# PURPOSE: User-specific database operations
# ==========================================

class UserRepository(BaseRepository[User]):
    """Repository for User model operations"""

    def __init__(self, db: Session):
        """Initialize with User model"""
        super().__init__(db, User)

    def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID"""
        return self.db.query(User).filter(User.telegram_id == telegram_id).first()

    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()

    def get_by_referral_code(self, referral_code: str) -> Optional[User]:
        """Get user by referral code"""
        return self.db.query(User).filter(User.referral_code == referral_code).first()

    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all active users"""
        return self.db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()

    def get_banned_users(self) -> List[User]:
        """Get all banned users"""
        return self.db.query(User).filter(User.is_banned == True).all()

    def search_users(self, query: str, limit: int = 50) -> List[User]:
        """Search users by name, username, or phone"""
        return self.db.query(User).filter(
            or_(
                User.first_name.ilike(f"%{query}%"),
                User.last_name.ilike(f"%{query}%"),
                User.username.ilike(f"%{query}%"),
                User.phone.ilike(f"%{query}%")
            )
        ).limit(limit).all()

    def count_active_users(self) -> int:
        """Count active users"""
        return self.db.query(User).filter(User.is_active == True).count()

    def add_points(self, user_id: int, points: int, reason: str, description: str = None) -> UserPointsHistory:
        """Add points to user and create history record"""
        user = self.get_by_id(user_id)
        if user:
            user.points += points
            user.total_points_earned += points if points > 0 else 0
            
            history = UserPointsHistory(
                user_id=user_id,
                points=points,
                reason=reason,
                description=description
            )
            self.db.add(history)
            self.db.commit()
            return history
        return None

    def get_points_history(self, user_id: int, limit: int = 50) -> List[UserPointsHistory]:
        """Get points history for user"""
        return self.db.query(UserPointsHistory).filter(
            UserPointsHistory.user_id == user_id
        ).order_by(desc(UserPointsHistory.created_at)).limit(limit).all()


# ==========================================
# BUTTON REPOSITORY
# PURPOSE: Button-specific database operations
# ==========================================

class ButtonRepository(BaseRepository[Button]):
    """Repository for Button model operations"""

    def __init__(self, db: Session):
        """Initialize with Button model"""
        super().__init__(db, Button)

    def get_by_slug(self, slug: str) -> Optional[Button]:
        """Get button by slug"""
        return self.db.query(Button).filter(Button.slug == slug).first()

    def get_main_menu_buttons(self) -> List[Button]:
        """Get all main menu buttons (level 0)"""
        return self.db.query(Button).filter(
            and_(Button.level == 0, Button.is_active == True)
        ).order_by(Button.order).all()

    def get_submenu_buttons(self, parent_id: int) -> List[Button]:
        """Get all submenu buttons for a parent"""
        return self.db.query(Button).filter(
            and_(Button.parent_id == parent_id, Button.is_active == True)
        ).order_by(Button.order).all()

    def get_nested_buttons(self, button_id: int) -> List[Button]:
        """Get all nested buttons recursively"""
        button = self.get_by_id(button_id)
        if button:
            return button.children
        return []

    def reorder_buttons(self, button_id: int, new_order: int) -> Optional[Button]:
        """Reorder button among siblings"""
        button = self.get_by_id(button_id)
        if button:
            button.order = new_order
            self.db.commit()
            self.db.refresh(button)
        return button


# ==========================================
# CHANNEL REPOSITORY
# PURPOSE: Channel-specific database operations
# ==========================================

class ChannelRepository(BaseRepository[Channel]):
    """Repository for Channel model operations"""

    def __init__(self, db: Session):
        """Initialize with Channel model"""
        super().__init__(db, Channel)

    def get_by_username(self, channel_username: str) -> Optional[Channel]:
        """Get channel by username"""
        return self.db.query(Channel).filter(Channel.channel_username == channel_username).first()

    def get_active_channels(self) -> List[Channel]:
        """Get all active channels"""
        return self.db.query(Channel).filter(Channel.is_active == True).all()

    def get_scheduled_channels(self) -> List[Channel]:
        """Get all channels with scheduled changes"""
        return self.db.query(Channel).filter(
            or_(Channel.is_scheduled_add == True, Channel.is_scheduled_remove == True)
        ).all()


# ==========================================
# SUPPORT TICKET REPOSITORY
# PURPOSE: Support ticket-specific operations
# ==========================================

class SupportTicketRepository(BaseRepository[SupportTicket]):
    """Repository for SupportTicket model operations"""

    def __init__(self, db: Session):
        """Initialize with SupportTicket model"""
        super().__init__(db, SupportTicket)

    def get_by_ticket_number(self, ticket_number: str) -> Optional[SupportTicket]:
        """Get ticket by ticket number"""
        return self.db.query(SupportTicket).filter(
            SupportTicket.ticket_number == ticket_number
        ).first()

    def get_user_tickets(self, user_id: int, limit: int = 50) -> List[SupportTicket]:
        """Get all tickets from a user"""
        return self.db.query(SupportTicket).filter(
            SupportTicket.user_id == user_id
        ).order_by(desc(SupportTicket.created_at)).limit(limit).all()

    def get_open_tickets(self, limit: int = 100) -> List[SupportTicket]:
        """Get all open tickets"""
        return self.db.query(SupportTicket).filter(
            SupportTicket.status == "open"
        ).order_by(SupportTicket.created_at).limit(limit).all()

    def search_tickets(self, query: str, limit: int = 50) -> List[SupportTicket]:
        """Search tickets by subject or ticket number"""
        return self.db.query(SupportTicket).filter(
            or_(
                SupportTicket.ticket_number.ilike(f"%{query}%"),
                SupportTicket.subject.ilike(f"%{query}%")
            )
        ).limit(limit).all()


# ==========================================
# BROADCAST REPOSITORY
# PURPOSE: Broadcast campaign-specific operations
# ==========================================

class BroadcastRepository(BaseRepository[BroadcastCampaign]):
    """Repository for BroadcastCampaign model operations"""

    def __init__(self, db: Session):
        """Initialize with BroadcastCampaign model"""
        super().__init__(db, BroadcastCampaign)

    def get_active_campaigns(self) -> List[BroadcastCampaign]:
        """Get all active/sending campaigns"""
        return self.db.query(BroadcastCampaign).filter(
            BroadcastCampaign.status.in_(["scheduled", "sending"])
        ).all()

    def get_campaign_receipts(self, campaign_id: int) -> List[BroadcastReceipt]:
        """Get all receipts for a campaign"""
        return self.db.query(BroadcastReceipt).filter(
            BroadcastReceipt.campaign_id == campaign_id
        ).all()

    def get_failed_receipts(self, campaign_id: int) -> List[BroadcastReceipt]:
        """Get failed receipts for a campaign"""
        return self.db.query(BroadcastReceipt).filter(
            and_(
                BroadcastReceipt.campaign_id == campaign_id,
                BroadcastReceipt.is_failed == True
            )
        ).all()


# ==========================================
# SCHEDULER REPOSITORY
# PURPOSE: Scheduled task-specific operations
# ==========================================

class SchedulerRepository(BaseRepository[ScheduledTask]):
    """Repository for ScheduledTask model operations"""

    def __init__(self, db: Session):
        """Initialize with ScheduledTask model"""
        super().__init__(db, ScheduledTask)

    def get_pending_tasks(self) -> List[ScheduledTask]:
        """Get all pending tasks due for execution"""
        from datetime import datetime
        return self.db.query(ScheduledTask).filter(
            and_(
                ScheduledTask.is_executed == False,
                ScheduledTask.is_active == True,
                ScheduledTask.scheduled_for <= datetime.utcnow()
            )
        ).all()

    def get_tasks_by_type(self, task_type: str) -> List[ScheduledTask]:
        """Get all tasks of a specific type"""
        return self.db.query(ScheduledTask).filter(
            ScheduledTask.task_type == task_type
        ).all()


# ==========================================
# ADMIN USER REPOSITORY
# PURPOSE: Admin user-specific operations
# ==========================================

class AdminUserRepository(BaseRepository[AdminUser]):
    """Repository for AdminUser model operations"""

    def __init__(self, db: Session):
        """Initialize with AdminUser model"""
        super().__init__(db, AdminUser)

    def get_by_username(self, username: str) -> Optional[AdminUser]:
        """Get admin by username"""
        return self.db.query(AdminUser).filter(AdminUser.username == username).first()

    def get_by_email(self, email: str) -> Optional[AdminUser]:
        """Get admin by email"""
        return self.db.query(AdminUser).filter(AdminUser.email == email).first()

    def get_active_admins(self) -> List[AdminUser]:
        """Get all active admin users"""
        return self.db.query(AdminUser).filter(AdminUser.is_active == True).all()


# ==========================================
# ACTIVITY LOG REPOSITORY
# PURPOSE: Admin activity logging operations
# ==========================================

class ActivityLogRepository(BaseRepository[AdminActivityLog]):
    """Repository for AdminActivityLog model operations"""

    def __init__(self, db: Session):
        """Initialize with AdminActivityLog model"""
        super().__init__(db, AdminActivityLog)

    def get_admin_logs(self, admin_id: int, limit: int = 100) -> List[AdminActivityLog]:
        """Get all logs for a specific admin"""
        return self.db.query(AdminActivityLog).filter(
            AdminActivityLog.admin_id == admin_id
        ).order_by(desc(AdminActivityLog.created_at)).limit(limit).all()

    def get_entity_logs(self, entity_type: str, entity_id: int) -> List[AdminActivityLog]:
        """Get all logs for a specific entity"""
        return self.db.query(AdminActivityLog).filter(
            and_(
                AdminActivityLog.entity_type == entity_type,
                AdminActivityLog.entity_id == entity_id
            )
        ).order_by(desc(AdminActivityLog.created_at)).all()

    def log_action(self, admin_id: int, admin_username: str, action: str,
                   entity_type: str, entity_id: int = None, details: str = None,
                   ip_address: str = None) -> AdminActivityLog:
        """Log an admin action"""
        log = AdminActivityLog(
            admin_id=admin_id,
            admin_username=admin_username,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address
        )
        self.db.add(log)
        self.db.commit()
        return log
