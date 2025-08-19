from sqlalchemy import Column, Integer, String, Text, Float, Date, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from datetime import datetime, date, timedelta
import enum
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class UserStatusEnum(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class UserRoleEnum(enum.Enum):
    USER = "user"
    PREMIUM = "premium"
    ADMIN = "admin"
    MODERATOR = "moderator"


class CurrencyEnum(enum.Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CAD = "CAD"
    AUD = "AUD"
    CHF = "CHF"
    CNY = "CNY"
    INR = "INR"
    BRL = "BRL"


class TravelStyleEnum(enum.Enum):
    BUDGET = "budget"
    MID_RANGE = "mid_range"
    LUXURY = "luxury"
    BACKPACKER = "backpacker"
    BUSINESS = "business"
    FAMILY = "family"
    SOLO = "solo"
    COUPLE = "couple"
    GROUP = "group"


class User(Base):
    __tablename__ = "users"

    # Primary identification
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Authentication fields
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(50), nullable=True, unique=True, index=True)
    
    # Basic profile information
    first_name: Mapped[str] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str] = mapped_column(String(100), nullable=True)
    display_name: Mapped[str] = mapped_column(String(150), nullable=True)
    
    # Profile details
    profile_picture_url: Mapped[str] = mapped_column(String(500), nullable=True)
    bio: Mapped[str] = mapped_column(Text, nullable=True)
    date_of_birth: Mapped[Date] = mapped_column(Date, nullable=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=True)
    
    # Location information
    country: Mapped[str] = mapped_column(String(100), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), nullable=True, default="UTC")
    
    # Account status and role
    status: Mapped[str] = mapped_column(String(30), nullable=False, default=UserStatusEnum.PENDING_VERIFICATION.value)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=UserRoleEnum.USER.value)
    
    # Email verification
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email_verified_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    email_verification_token: Mapped[str] = mapped_column(String(255), nullable=True, unique=True)
    email_verification_token_expires: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Password reset
    password_reset_token: Mapped[str] = mapped_column(String(255), nullable=True, unique=True)
    password_reset_token_expires: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    password_changed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Travel preferences
    preferred_currency: Mapped[str] = mapped_column(String(3), nullable=False, default=CurrencyEnum.USD.value)
    preferred_travel_style: Mapped[str] = mapped_column(String(20), nullable=True)
    travel_interests: Mapped[JSON] = mapped_column(JSON, nullable=True)  # Array of interests like ['adventure', 'culture', 'food']
    dietary_restrictions: Mapped[JSON] = mapped_column(JSON, nullable=True)  # Array of dietary needs
    accessibility_needs: Mapped[JSON] = mapped_column(JSON, nullable=True)  # Array of accessibility requirements
    
    # Travel experience
    countries_visited: Mapped[JSON] = mapped_column(JSON, nullable=True)  # Array of country codes
    languages_spoken: Mapped[JSON] = mapped_column(JSON, nullable=True)  # Array of language codes
    travel_experience_level: Mapped[str] = mapped_column(String(20), nullable=True)  # beginner, intermediate, expert
    
    # Preferences and settings
    notification_preferences: Mapped[JSON] = mapped_column(JSON, nullable=True)  # Email, push, SMS preferences
    privacy_settings: Mapped[JSON] = mapped_column(JSON, nullable=True)  # Profile visibility, data sharing preferences
    measurement_system: Mapped[str] = mapped_column(String(10), nullable=False, default="metric")  # metric or imperial
    
    # Subscription and billing
    subscription_type: Mapped[str] = mapped_column(String(20), nullable=False, default="free")  # free, premium, enterprise
    subscription_start_date: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    subscription_end_date: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Social features
    is_public_profile: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    allow_friend_requests: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    share_travel_stats: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Security and authentication tracking
    last_login_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_location: Mapped[JSON] = mapped_column(JSON, nullable=True)  # Store location data from third-party API
    current_login_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    current_login_location: Mapped[JSON] = mapped_column(JSON, nullable=True)  # Store location data from third-party API
    login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_failed_login_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failed_login_location: Mapped[JSON] = mapped_column(JSON, nullable=True)  # Store location data from third-party API
    account_locked_until: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Session management
    active_sessions: Mapped[JSON] = mapped_column(JSON, nullable=True)  # Store active session tokens/IDs
    last_activity_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Two-factor authentication
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    two_factor_secret: Mapped[str] = mapped_column(String(255), nullable=True)
    backup_codes: Mapped[JSON] = mapped_column(JSON, nullable=True)  # Array of backup codes for 2FA
    
    # Marketing and communication
    marketing_consent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    newsletter_subscribed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Analytics and tracking
    total_trips_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_trips_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    favorite_destinations: Mapped[JSON] = mapped_column(JSON, nullable=True)  # Top destinations based on user activity
    
    # Onboarding and user journey
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    onboarding_step: Mapped[int] = mapped_column(Integer, nullable=True)  # Current step in onboarding process
    first_trip_created: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # GDPR and data management
    data_processing_consent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    data_export_requested_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    data_deletion_requested_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Audit fields
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)  # Soft delete
    
    # Referral system
    referral_code: Mapped[str] = mapped_column(String(20), nullable=True, unique=True, index=True)
    referred_by_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    referral_earnings: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    
    # Device and browser tracking
    last_user_agent: Mapped[str] = mapped_column(Text, nullable=True)
    preferred_language: Mapped[str] = mapped_column(String(10), nullable=True, default="en")

    # Traveler profile
    traveler_type_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("traveler_types.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    traveler_type = relationship("TravelerType", back_populates="users", passive_deletes=True)
    
    def __str__(self):
        return self.display_name or self.username or self.email

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', status='{self.status}')>"
    
    @property
    def full_name(self):
        """Returns the full name of the user"""
        if self.first_name is not None and self.last_name is not None:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.display_name or self.username
    
    @property
    def is_premium(self):
        """Check if user has premium subscription"""
        return self.subscription_type in ['premium', 'enterprise']
    
    @property
    def is_active(self):
        """Check if user account is active"""
        return self.status == UserStatusEnum.ACTIVE.value and not self.is_locked
    
    @property
    def is_locked(self):
        """Check if account is currently locked"""
        if self.account_locked_until is not None:
            return datetime.utcnow() < self.account_locked_until.replace(tzinfo=None)
        return False
    
    @property
    def age(self):
        """Calculate user age from date of birth"""
        if self.date_of_birth is not None:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
    
    @property
    def days_since_last_login(self):
        """Calculate days since last login"""
        if self.last_login_at is not None:
            return (datetime.utcnow() - self.last_login_at.replace(tzinfo=None)).days
        return None
    

