# ==========================================
# MODULE: SERVICES LAYER
# PURPOSE: Business logic and service operations
# ==========================================

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
import string
from app.repositories import (
    UserRepository, ButtonRepository, ChannelRepository,
    SupportTicketRepository, BroadcastRepository,
    SchedulerRepository, AdminUserRepository, ActivityLogRepository
)
from app import models, schemas


# ==========================================
# USER SERVICE
# PURPOSE: Handle user-related business logic
# ==========================================

class UserService:
    """Service for user operations"""

    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db
        self.user_repo = UserRepository(db)

    def get_or_create_user(self, telegram_id: int, first_name: str = None,
                          last_name: str = None, username: str = None) -> models.User:
        """
        Get existing user or create new one.
        Used when user starts the bot.
        """
        user = self.user_repo.get_by_telegram_id(telegram_id)
        
        if not user:
            # Generate unique referral code
            referral_code = self._generate_referral_code()
            
            user_data = {
                "telegram_id": telegram_id,
                "first_name": first_name,
                "last_name": last_name,
                "username": username,
                "referral_code": referral_code,
                "points": 0
            }
            user = self.user_repo.create(user_data)
        
        return user

    def add_points(self, user_id: int, points: int, reason: str,
                   description: str = None) -> models.UserPointsHistory:
        """Add points to user"""
        return self.user_repo.add_points(user_id, points, reason, description)

    def remove_points(self, user_id: int, points: int, reason: str,
                      description: str = None) -> bool:
        """Remove points from user"""
        user = self.user_repo.get_by_id(user_id)
        if user and user.points >= points:
            return self.user_repo.add_points(user_id, -points, reason, description) is not None
        return False

    def ban_user(self, user_id: int, reason: str = None) -> Optional[models.User]:
        """Ban a user"""
        return self.user_repo.update(user_id, {
            "is_banned": True,
            "status": models.UserStatus.BANNED,
            "ban_reason": reason
        })

    def unban_user(self, user_id: int) -> Optional[models.User]:
        """Unban a user"""
        return self.user_repo.update(user_id, {
            "is_banned": False,
            "status": models.UserStatus.ACTIVE,
            "ban_reason": None
        })

    def process_referral(self, referrer_code: str, new_user_id: int,
                        referral_points: int = 5) -> bool:
        """
        Process referral when new user joins via referral link.
        Awards points to referrer.
        """
        referrer = self.user_repo.get_by_referral_code(referrer_code)
        new_user = self.user_repo.get_by_id(new_user_id)
        
        if referrer and new_user:
            # Update referrer
            referrer.referral_count += 1
            self.add_points(
                referrer.id,
                referral_points,
                "referral",
                f"New user referred: {new_user.first_name}"
            )
            
            # Update new user
            new_user.referrer_id = referrer.id
            self.db.commit()
            return True
        
        return False

    def update_activity(self, user_id: int) -> Optional[models.User]:
        """Update user's last activity timestamp"""
        return self.user_repo.update(user_id, {"last_activity": datetime.utcnow()})

    def _generate_referral_code(self) -> str:
        """Generate unique referral code"""
        chars = string.ascii_letters + string.digits
        while True:
            code = ''.join(secrets.choice(chars) for _ in range(8))
            if not self.user_repo.get_by_referral_code(code):
                return code


# ==========================================
# BUTTON SERVICE
# PURPOSE: Handle button/menu business logic
# ==========================================

class ButtonService:
    """Service for button operations"""

    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db
        self.button_repo = ButtonRepository(db)

    def get_accessible_buttons(self, user_id: int) -> List[models.Button]:
        """
        Get buttons accessible to user based on points.
        Filters out buttons user doesn't have enough points for.
        """
        user = UserRepository(self.db).get_by_id(user_id)
        if not user:
            return []
        
        main_buttons = self.button_repo.get_main_menu_buttons()
        accessible = []
        
        for button in main_buttons:
            if button.required_points <= user.points:
                accessible.append(button)
        
        return accessible

    def get_menu_tree(self, button_id: int = None) -> Optional[Dict[str, Any]]:
        """
        Get button menu tree structure.
        Returns nested menu hierarchy.
        """
        if button_id:
            button = self.button_repo.get_by_id(button_id)
        else:
            # If no ID provided, return main menu
            buttons = self.button_repo.get_main_menu_buttons()
            return [self._build_button_tree(b) for b in buttons]
        
        if button:
            return self._build_button_tree(button)
        return None

    def _build_button_tree(self, button: models.Button) -> Dict[str, Any]:
        """Build nested button tree"""
        return {
            "id": button.id,
            "name": button.name,
            "slug": button.slug,
            "button_type": button.button_type,
            "content_text": button.content_text,
            "children": [self._build_button_tree(child) for child in button.children]
        }

    def reorder_buttons(self, parent_id: Optional[int], button_orders: List[Dict[int, int]]) -> bool:
        """
        Reorder buttons among siblings.
        
        Args:
            parent_id: Parent button ID (None for main menu)
            button_orders: List of {button_id: new_order}
        """
        for button_id, order in button_orders:
            self.button_repo.reorder_buttons(button_id, order)
        return True


# ==========================================
# CHANNEL SERVICE
# PURPOSE: Handle forced join system
# ==========================================

class ChannelService:
    """Service for channel operations"""

    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db
        self.channel_repo = ChannelRepository(db)

    def get_required_channels(self) -> List[models.Channel]:
        """Get all currently required channels"""
        return self.channel_repo.get_active_channels()

    def check_user_membership(self, user_id: int, channel_id: int) -> bool:
        """Check if user is verified member of channel"""
        membership = self.db.query(models.UserChannelMembership).filter(
            models.UserChannelMembership.user_id == user_id,
            models.UserChannelMembership.channel_id == channel_id
        ).first()
        
        return membership and membership.is_member

    def verify_membership(self, user_id: int, channel_id: int) -> models.UserChannelMembership:
        """Mark user as verified member"""
        membership = self.db.query(models.UserChannelMembership).filter(
            models.UserChannelMembership.user_id == user_id,
            models.UserChannelMembership.channel_id == channel_id
        ).first()
        
        if not membership:
            membership = models.UserChannelMembership(
                user_id=user_id,
                channel_id=channel_id
            )
            self.db.add(membership)
        
        membership.is_member = True
        membership.verified_at = datetime.utcnow()
        self.db.commit()
        return membership

    def can_user_access_bot(self, user_id: int) -> bool:
        """Check if user has verified all required channels"""
        required_channels = self.get_required_channels()
        
        for channel in required_channels:
            if not self.check_user_membership(user_id, channel.id):
                return False
        
        return True


# ==========================================
# SUPPORT SERVICE
# PURPOSE: Handle support tickets
# ==========================================

class SupportService:
    """Service for support operations"""

    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db
        self.ticket_repo = SupportTicketRepository(db)

    def create_ticket(self, user_id: int, subject: str, description: str) -> models.SupportTicket:
        """Create new support ticket"""
        ticket_number = self._generate_ticket_number()
        
        ticket_data = {
            "user_id": user_id,
            "ticket_number": ticket_number,
            "subject": subject,
            "description": description,
            "status": models.TicketStatus.OPEN
        }
        
        return self.ticket_repo.create(ticket_data)

    def respond_to_ticket(self, ticket_id: int, admin_response: str,
                          is_resolved: bool = False) -> Optional[models.SupportTicket]:
        """Add admin response to ticket"""
        update_data = {
            "admin_response": admin_response,
            "response_at": datetime.utcnow(),
            "status": models.TicketStatus.RESOLVED if is_resolved else models.TicketStatus.IN_PROGRESS,
            "is_resolved": is_resolved
        }
        
        return self.ticket_repo.update(ticket_id, update_data)

    def _generate_ticket_number(self) -> str:
        """Generate unique ticket number"""
        import time
        return f"TK-{int(time.time())}"


# ==========================================
# BROADCAST SERVICE
# PURPOSE: Handle broadcast campaigns
# ==========================================

class BroadcastService:
    """Service for broadcast operations"""

    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db
        self.broadcast_repo = BroadcastRepository(db)
        self.user_repo = UserRepository(db)

    def create_campaign(self, name: str, content_type: str, content_text: str,
                       target_type: str = "all",
                       selected_user_ids: List[int] = None) -> models.BroadcastCampaign:
        """Create new broadcast campaign"""
        # Get target users
        if target_type == "all":
            users = self.user_repo.get_all(limit=10000)
        elif target_type == "active":
            users = self.user_repo.get_active_users(limit=10000)
        elif target_type == "selected":
            users = [self.user_repo.get_by_id(uid) for uid in selected_user_ids or []]
        else:
            users = []
        
        # Create campaign
        campaign_data = {
            "name": name,
            "content_type": content_type,
            "content_text": content_text,
            "target_type": target_type,
            "status": models.BroadcastStatus.DRAFT,
            "total_recipients": len(users)
        }
        
        campaign = self.broadcast_repo.create(campaign_data)
        
        # Create receipts
        for user in users:
            receipt = models.BroadcastReceipt(
                campaign_id=campaign.id,
                user_id=user.id
            )
            self.db.add(receipt)
        
        self.db.commit()
        return campaign

    def get_pending_campaigns(self) -> List[models.BroadcastCampaign]:
        """Get campaigns ready to send"""
        return self.broadcast_repo.get_active_campaigns()

    def mark_sent(self, campaign_id: int, user_id: int, success: bool = True) -> Optional[models.BroadcastReceipt]:
        """Mark broadcast as sent to user"""
        receipt = self.db.query(models.BroadcastReceipt).filter(
            models.BroadcastReceipt.campaign_id == campaign_id,
            models.BroadcastReceipt.user_id == user_id
        ).first()
        
        if receipt:
            receipt.is_sent = success
            receipt.is_failed = not success
            receipt.sent_at = datetime.utcnow()
            self.db.commit()
            
            # Update campaign stats
            self._update_campaign_stats(campaign_id)
        
        return receipt

    def _update_campaign_stats(self, campaign_id: int):
        """Update broadcast campaign statistics"""
        receipts = self.broadcast_repo.get_campaign_receipts(campaign_id)
        sent = sum(1 for r in receipts if r.is_sent)
        failed = sum(1 for r in receipts if r.is_failed)
        
        campaign = self.broadcast_repo.get_by_id(campaign_id)
        if campaign and campaign.total_recipients > 0:
            campaign.sent_count = sent
            campaign.failed_count = failed
            campaign.success_rate = (sent / campaign.total_recipients) * 100
            self.db.commit()


# ==========================================
# SCHEDULER SERVICE
# PURPOSE: Handle scheduled tasks
# ==========================================

class SchedulerService:
    """Service for scheduled task operations"""

    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db
        self.scheduler_repo = SchedulerRepository(db)

    def get_pending_tasks(self) -> List[models.ScheduledTask]:
        """Get all pending tasks due for execution"""
        return self.scheduler_repo.get_pending_tasks()

    def mark_executed(self, task_id: int, success: bool = True,
                     result: str = None, error: str = None):
        """Mark task as executed"""
        update_data = {
            "is_executed": success,
            "execution_result": result,
            "last_error": error if not success else None,
            "executed_at": datetime.utcnow() if success else None
        }
        
        return self.scheduler_repo.update(task_id, update_data)

    def retry_failed_task(self, task_id: int) -> Optional[models.ScheduledTask]:
        """Retry a failed task"""
        task = self.scheduler_repo.get_by_id(task_id)
        
        if task and task.retry_count < task.max_retries:
            task.retry_count += 1
            task.is_executed = False
            task.last_error = None
            self.db.commit()
            return task
        
        return None
