# ==========================================
# MODULE: DATABASE MODELS
# PURPOSE: SQLAlchemy ORM models for all entities
# ==========================================

from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    Float, ForeignKey, Enum, LargeBinary, UniqueConstraint,
    Index
)
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from app.database import Base


# ==========================================
# ENUMS: Entity Type Definitions
# ==========================================

class ButtonType(str, PyEnum):
    """Button type enumeration"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    FILE = "file"
    LINK = "link"
    NESTED = "nested"


class UserStatus(str, PyEnum):
    """User status enumeration"""
    ACTIVE = "active"
    BANNED = "banned"
    INACTIVE = "inactive"


class TicketStatus(str, PyEnum):
    """Support ticket status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class BroadcastStatus(str, PyEnum):
    """Broadcast campaign status"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    COMPLETED = "completed"
    FAILED = "failed"


# ==========================================
# MODULE: USER MANAGEMENT
# PURPOSE: Store and manage bot users
# ==========================================

class User(Base):
    """
    Represents a Telegram user interacting with the bot.
    Tracks user data, points, referrals, and activity.
    """
    __tablename__ = "users"

    # ========== Primary Key ==========
    id = Column(Integer, primary_key=True, index=True)

    # ========== Telegram Data ==========
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    username = Column(String(255), nullable=True, index=True)
    phone = Column(String(20), nullable=True)

    # ========== User Status ==========
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, index=True)
    is_active = Column(Boolean, default=True, index=True)
    is_banned = Column(Boolean, default=False, index=True)
    ban_reason = Column(Text, nullable=True)

    # ========== Points System ==========
    points = Column(Integer, default=0, index=True)
    total_points_earned = Column(Integer, default=0)
    total_points_spent = Column(Integer, default=0)

    # ========== Referral System ==========
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    referral_code = Column(String(50), unique=True, nullable=True, index=True)
    referral_count = Column(Integer, default=0)

    # ========== Tracking Data ==========
    joined_date = Column(DateTime, default=datetime.utcnow, index=True)
    last_activity = Column(DateTime, default=datetime.utcnow, index=True)
    message_count = Column(Integer, default=0)

    # ========== Relationships ==========
    referrals = relationship("User", backref="referrer", remote_side=[id])
    user_points_history = relationship("UserPointsHistory", back_populates="user", cascade="all, delete-orphan")
    user_channels = relationship("UserChannelMembership", back_populates="user", cascade="all, delete-orphan")
    support_tickets = relationship("SupportTicket", back_populates="user", cascade="all, delete-orphan")
    broadcast_receipts = relationship("BroadcastReceipt", back_populates="user", cascade="all, delete-orphan")

    # ========== Timestamps ==========
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ========== Indexes ==========
    __table_args__ = (
        Index("ix_telegram_id", "telegram_id"),
        Index("ix_referral_code", "referral_code"),
        Index("ix_joined_date", "joined_date"),
    )


class UserPointsHistory(Base):
    """
    Tracks all points transactions for a user.
    Complete audit trail of points gains/losses.
    """
    __tablename__ = "user_points_history"

    # ========== Primary Key ==========
    id = Column(Integer, primary_key=True, index=True)

    # ========== Foreign Keys ==========
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # ========== Transaction Data ==========
    points = Column(Integer, nullable=False)  # Positive or negative
    reason = Column(String(255), nullable=False)  # "button_unlock", "referral", "admin_add", etc.
    description = Column(Text, nullable=True)
    reference_id = Column(Integer, nullable=True)  # Link to button, referral, etc.

    # ========== Relationships ==========
    user = relationship("User", back_populates="user_points_history")

    # ========== Timestamps ==========
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


# ==========================================
# MODULE: BUTTON MANAGEMENT
# PURPOSE: Manage dynamic bot buttons and menus
# ==========================================

class Button(Base):
    """
    Represents a Telegram bot button/menu item.
    Supports unlimited nesting levels and various content types.
    """
    __tablename__ = "buttons"

    # ========== Primary Key ==========
    id = Column(Integer, primary_key=True, index=True)

    # ========== Button Identity ==========
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # ========== Button Hierarchy ==========
    parent_id = Column(Integer, ForeignKey("buttons.id"), nullable=True, index=True)
    level = Column(Integer, default=0)  # 0 = main menu, 1 = submenu, etc.
    order = Column(Integer, default=0)  # Display order among siblings

    # ========== Button Configuration ==========
    button_type = Column(Enum(ButtonType), default=ButtonType.TEXT, index=True)
    required_points = Column(Integer, default=0)  # Points needed to access

    # ========== Content Fields ==========
    content_text = Column(Text, nullable=True)
    content_url = Column(String(500), nullable=True)  # For links, images, videos
    content_file_id = Column(Integer, ForeignKey("media_files.id"), nullable=True)

    # ========== Status ==========
    is_active = Column(Boolean, default=True, index=True)
    is_visible = Column(Boolean, default=True, index=True)
    show_back_button = Column(Boolean, default=True)
    show_home_button = Column(Boolean, default=True)

    # ========== Relationships ==========
    children = relationship("Button", backref="parent", remote_side=[id], cascade="all, delete-orphan")
    content_file = relationship("MediaFile")

    # ========== Timestamps ==========
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ========== Indexes ==========
    __table_args__ = (
        Index("ix_parent_id_order", "parent_id", "order"),
        Index("ix_slug", "slug"),
    )


# ==========================================
# MODULE: MEDIA LIBRARY
# PURPOSE: Store and manage bot media assets
# ==========================================

class MediaFile(Base):
    """
    Represents uploaded media files (images, videos, documents).
    Supports reusable media across multiple buttons.
    """
    __tablename__ = "media_files"

    # ========== Primary Key ==========
    id = Column(Integer, primary_key=True, index=True)

    # ========== File Information ==========
    original_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False, unique=True)
    file_size = Column(Integer)  # In bytes
    file_type = Column(String(50), index=True)  # jpg, pdf, etc.
    mime_type = Column(String(100))

    # ========== Storage Information ==========
    storage_type = Column(String(50), default="local")  # local, s3, etc.
    remote_url = Column(String(500), nullable=True)
    telegram_file_id = Column(String(500), nullable=True)

    # ========== Status ==========
    is_active = Column(Boolean, default=True, index=True)

    # ========== Timestamps ==========
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ==========================================
# MODULE: FORCED JOIN SYSTEM
# PURPOSE: Manage channel/group membership requirements
# ==========================================

class Channel(Base):
    """
    Represents a Telegram channel or group that users must join.
    Bot verifies membership before allowing access.
    """
    __tablename__ = "channels"

    # ========== Primary Key ==========
    id = Column(Integer, primary_key=True, index=True)

    # ========== Channel Information ==========
    name = Column(String(255), nullable=False, index=True)
    channel_username = Column(String(255), nullable=False, unique=True, index=True)
    channel_id = Column(String(50), unique=True, nullable=True)
    description = Column(Text, nullable=True)
    channel_type = Column(String(50), default="channel")  # channel or group

    # ========== Status ==========
    is_active = Column(Boolean, default=True, index=True)

    # ========== Scheduling ==========
    add_at_date = Column(DateTime, nullable=True, index=True)
    remove_at_date = Column(DateTime, nullable=True, index=True)
    is_scheduled_add = Column(Boolean, default=False)
    is_scheduled_remove = Column(Boolean, default=False)

    # ========== Relationships ==========
    user_memberships = relationship("UserChannelMembership", back_populates="channel", cascade="all, delete-orphan")

    # ========== Timestamps ==========
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserChannelMembership(Base):
    """
    Tracks whether a user has verified membership in a channel.
    """
    __tablename__ = "user_channel_membership"

    # ========== Primary Key ==========
    id = Column(Integer, primary_key=True, index=True)

    # ========== Foreign Keys ==========
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False, index=True)

    # ========== Status ==========
    is_member = Column(Boolean, default=False, index=True)
    verified_at = Column(DateTime, nullable=True)

    # ========== Relationships ==========
    user = relationship("User", back_populates="user_channels")
    channel = relationship("Channel", back_populates="user_memberships")

    # ========== Timestamps ==========
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ========== Constraints ==========
    __table_args__ = (
        UniqueConstraint("user_id", "channel_id", name="uq_user_channel"),
    )


# ==========================================
# MODULE: SUPPORT SYSTEM
# PURPOSE: Handle user support tickets and messages
# ==========================================

class SupportTicket(Base):
    """
    Represents a support ticket from a user.
    Stores conversation thread and resolution status.
    """
    __tablename__ = "support_tickets"

    # ========== Primary Key ==========
    id = Column(Integer, primary_key=True, index=True)

    # ========== Foreign Keys ==========
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # ========== Ticket Data ==========
    ticket_number = Column(String(50), unique=True, nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    # ========== Status ==========
    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN, index=True)
    is_resolved = Column(Boolean, default=False, index=True)
    is_archived = Column(Boolean, default=False, index=True)

    # ========== Response ==========
    admin_response = Column(Text, nullable=True)
    response_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # ========== Relationships ==========
    user = relationship("User", back_populates="support_tickets")

    # ========== Timestamps ==========
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ==========================================
# MODULE: BROADCAST SYSTEM
# PURPOSE: Send bulk messages to users
# ==========================================

class BroadcastCampaign(Base):
    """
    Represents a broadcast campaign to send messages to users.
    Tracks delivery statistics and status.
    """
    __tablename__ = "broadcast_campaigns"

    # ========== Primary Key ==========
    id = Column(Integer, primary_key=True, index=True)

    # ========== Campaign Information ==========
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # ========== Content ==========
    content_type = Column(String(50))  # text, image, video, document
    content_text = Column(Text, nullable=True)
    content_media_id = Column(Integer, ForeignKey("media_files.id"), nullable=True)

    # ========== Target Audience ==========
    target_type = Column(String(50), default="all")  # all, active, selected
    selected_user_ids = Column(Text, nullable=True)  # JSON string of user IDs

    # ========== Status ==========
    status = Column(Enum(BroadcastStatus), default=BroadcastStatus.DRAFT, index=True)
    scheduled_at = Column(DateTime, nullable=True, index=True)

    # ========== Statistics ==========
    total_recipients = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)

    # ========== Relationships ==========
    content_media = relationship("MediaFile")
    receipts = relationship("BroadcastReceipt", back_populates="campaign", cascade="all, delete-orphan")

    # ========== Timestamps ==========
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class BroadcastReceipt(Base):
    """
    Tracks delivery status of each broadcast message to individual users.
    """
    __tablename__ = "broadcast_receipts"

    # ========== Primary Key ==========
    id = Column(Integer, primary_key=True, index=True)

    # ========== Foreign Keys ==========
    campaign_id = Column(Integer, ForeignKey("broadcast_campaigns.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # ========== Delivery Status ==========
    is_sent = Column(Boolean, default=False, index=True)
    is_failed = Column(Boolean, default=False, index=True)
    error_message = Column(Text, nullable=True)

    # ========== Relationships ==========
    campaign = relationship("BroadcastCampaign", back_populates="receipts")
    user = relationship("User", back_populates="broadcast_receipts")

    # ========== Timestamps ==========
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    sent_at = Column(DateTime, nullable=True)


# ==========================================
# MODULE: SCHEDULER SYSTEM
# PURPOSE: Background task scheduling
# ==========================================

class ScheduledTask(Base):
    """
    Represents a scheduled background task.
    Supports various task types like adding channels, publishing content, etc.
    """
    __tablename__ = "scheduled_tasks"

    # ========== Primary Key ==========
    id = Column(Integer, primary_key=True, index=True)

    # ========== Task Information ==========
    task_name = Column(String(255), nullable=False, index=True)
    task_type = Column(String(50), nullable=False, index=True)  # add_channel, remove_channel, etc.
    description = Column(Text, nullable=True)

    # ========== Task Data (JSON serialized) ==========
    task_data = Column(Text, nullable=True)  # JSON

    # ========== Execution ==========
    scheduled_for = Column(DateTime, nullable=False, index=True)
    is_executed = Column(Boolean, default=False, index=True)
    execution_result = Column(Text, nullable=True)
    executed_at = Column(DateTime, nullable=True)

    # ========== Retry Logic ==========
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    last_error = Column(Text, nullable=True)

    # ========== Status ==========
    is_active = Column(Boolean, default=True, index=True)

    # ========== Timestamps ==========
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ==========================================
# MODULE: ADMIN ACCOUNTS
# PURPOSE: Store admin user credentials
# ==========================================

class AdminUser(Base):
    """
    Represents an admin user for the panel.
    Stores credentials and access information.
    """
    __tablename__ = "admin_users"

    # ========== Primary Key ==========
    id = Column(Integer, primary_key=True, index=True)

    # ========== Credentials ==========
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # ========== Status ==========
    is_active = Column(Boolean, default=True, index=True)
    is_superuser = Column(Boolean, default=False)

    # ========== Access Tracking ==========
    last_login = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0)

    # ========== Timestamps ==========
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ==========================================
# MODULE: ACTIVITY LOGGING
# PURPOSE: Audit trail for admin actions
# ==========================================

class AdminActivityLog(Base):
    """
    Logs all admin panel actions for audit trail.
    """
    __tablename__ = "admin_activity_logs"

    # ========== Primary Key ==========
    id = Column(Integer, primary_key=True, index=True)

    # ========== Admin Information ==========
    admin_id = Column(Integer, ForeignKey("admin_users.id"), nullable=True, index=True)
    admin_username = Column(String(255), nullable=False, index=True)

    # ========== Action Information ==========
    action = Column(String(255), nullable=False, index=True)  # create, update, delete, etc.
    entity_type = Column(String(50), nullable=False, index=True)  # user, button, etc.
    entity_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)  # JSON details

    # ========== IP Address ==========
    ip_address = Column(String(50), nullable=True)

    # ========== Timestamps ==========
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
