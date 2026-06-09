# ==========================================
# MODULE: PYDANTIC SCHEMAS
# PURPOSE: Request/Response validation and serialization
# ==========================================

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, validator
from app.models import ButtonType, UserStatus, TicketStatus, BroadcastStatus


# ==========================================
# USER SCHEMAS
# ==========================================

class UserBase(BaseModel):
    """Base user schema with common fields"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user"""
    telegram_id: int
    referral_code: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for updating user"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    phone: Optional[str] = None
    points: Optional[int] = None
    status: Optional[UserStatus] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    telegram_id: int
    status: UserStatus
    points: int
    total_points_earned: int
    referral_count: int
    joined_date: datetime
    last_activity: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class UserDetailResponse(UserResponse):
    """Detailed user response with additional data"""
    referral_code: Optional[str] = None
    ban_reason: Optional[str] = None
    message_count: int


# ==========================================
# POINTS SCHEMAS
# ==========================================

class UserPointsHistoryResponse(BaseModel):
    """Schema for points transaction"""
    id: int
    user_id: int
    points: int
    reason: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AddPointsRequest(BaseModel):
    """Schema for adding points to user"""
    user_id: int
    points: int = Field(..., gt=0)
    reason: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class RemovePointsRequest(BaseModel):
    """Schema for removing points from user"""
    user_id: int
    points: int = Field(..., gt=0)
    reason: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


# ==========================================
# BUTTON SCHEMAS
# ==========================================

class ButtonBase(BaseModel):
    """Base button schema"""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    button_type: ButtonType = ButtonType.TEXT
    required_points: int = Field(default=0, ge=0)
    content_text: Optional[str] = None
    content_url: Optional[str] = None


class ButtonCreate(ButtonBase):
    """Schema for creating button"""
    parent_id: Optional[int] = None
    order: int = 0


class ButtonUpdate(BaseModel):
    """Schema for updating button"""
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    button_type: Optional[ButtonType] = None
    required_points: Optional[int] = None
    content_text: Optional[str] = None
    content_url: Optional[str] = None
    parent_id: Optional[int] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None
    is_visible: Optional[bool] = None


class ButtonResponse(ButtonBase):
    """Schema for button response"""
    id: int
    parent_id: Optional[int] = None
    level: int
    order: int
    is_active: bool
    is_visible: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ButtonDetailResponse(ButtonResponse):
    """Detailed button response with children"""
    children: List['ButtonResponse'] = []


ButtonDetailResponse.model_rebuild()


# ==========================================
# MEDIA SCHEMAS
# ==========================================

class MediaFileResponse(BaseModel):
    """Schema for media file response"""
    id: int
    original_name: str
    file_path: str
    file_size: int
    file_type: str
    mime_type: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# CHANNEL SCHEMAS
# ==========================================

class ChannelBase(BaseModel):
    """Base channel schema"""
    name: str = Field(..., min_length=1, max_length=255)
    channel_username: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    channel_type: str = "channel"


class ChannelCreate(ChannelBase):
    """Schema for creating channel"""
    add_at_date: Optional[datetime] = None
    remove_at_date: Optional[datetime] = None


class ChannelUpdate(BaseModel):
    """Schema for updating channel"""
    name: Optional[str] = None
    channel_username: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    add_at_date: Optional[datetime] = None
    remove_at_date: Optional[datetime] = None


class ChannelResponse(ChannelBase):
    """Schema for channel response"""
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# SUPPORT TICKET SCHEMAS
# ==========================================

class SupportTicketBase(BaseModel):
    """Base support ticket schema"""
    subject: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)


class SupportTicketCreate(SupportTicketBase):
    """Schema for creating support ticket"""
    user_id: int


class SupportTicketUpdate(BaseModel):
    """Schema for updating support ticket"""
    status: Optional[TicketStatus] = None
    admin_response: Optional[str] = None
    is_resolved: Optional[bool] = None
    is_archived: Optional[bool] = None


class SupportTicketResponse(SupportTicketBase):
    """Schema for support ticket response"""
    id: int
    ticket_number: str
    user_id: int
    status: TicketStatus
    is_resolved: bool
    is_archived: bool
    admin_response: Optional[str] = None
    created_at: datetime
    response_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==========================================
# BROADCAST SCHEMAS
# ==========================================

class BroadcastCampaignBase(BaseModel):
    """Base broadcast campaign schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    content_type: str
    content_text: Optional[str] = None
    target_type: str = "all"


class BroadcastCampaignCreate(BroadcastCampaignBase):
    """Schema for creating broadcast campaign"""
    selected_user_ids: Optional[List[int]] = None


class BroadcastCampaignUpdate(BaseModel):
    """Schema for updating broadcast campaign"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[BroadcastStatus] = None
    scheduled_at: Optional[datetime] = None


class BroadcastCampaignResponse(BroadcastCampaignBase):
    """Schema for broadcast campaign response"""
    id: int
    status: BroadcastStatus
    total_recipients: int
    sent_count: int
    failed_count: int
    success_rate: float
    created_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# SCHEDULER SCHEMAS
# ==========================================

class ScheduledTaskBase(BaseModel):
    """Base scheduled task schema"""
    task_name: str = Field(..., min_length=1, max_length=255)
    task_type: str
    description: Optional[str] = None
    scheduled_for: datetime


class ScheduledTaskCreate(ScheduledTaskBase):
    """Schema for creating scheduled task"""
    task_data: Optional[str] = None


class ScheduledTaskResponse(ScheduledTaskBase):
    """Schema for scheduled task response"""
    id: int
    is_executed: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# ADMIN SCHEMAS
# ==========================================

class AdminUserBase(BaseModel):
    """Base admin user schema"""
    username: str = Field(..., min_length=3, max_length=255)
    email: EmailStr


class AdminUserCreate(AdminUserBase):
    """Schema for creating admin user"""
    password: str = Field(..., min_length=8)
    is_superuser: bool = False


class AdminUserUpdate(BaseModel):
    """Schema for updating admin user"""
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)


class AdminUserResponse(AdminUserBase):
    """Schema for admin user response"""
    id: int
    is_active: bool
    is_superuser: bool
    last_login: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# AUTHENTICATION SCHEMAS
# ==========================================

class LoginRequest(BaseModel):
    """Schema for login request"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Schema for login response"""
    access_token: str
    token_type: str = "bearer"
    admin: AdminUserResponse


class TokenData(BaseModel):
    """Schema for JWT token data"""
    username: Optional[str] = None
    user_id: Optional[int] = None


# ==========================================
# DASHBOARD SCHEMAS
# ==========================================

class DashboardStats(BaseModel):
    """Schema for dashboard statistics"""
    total_users: int
    active_users: int
    total_buttons: int
    support_tickets_open: int
    total_referrals: int
    broadcast_stats: dict


class AdminActivityLogResponse(BaseModel):
    """Schema for admin activity log response"""
    id: int
    admin_username: str
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
