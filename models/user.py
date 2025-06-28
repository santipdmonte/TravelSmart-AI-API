from sqlalchemy import Column, Integer, String, Text, Float, Date, DateTime, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from datetime import datetime, date, timedelta
import enum
import uuid
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
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Authentication fields
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    username = Column(String(50), nullable=True, unique=True, index=True)
    
    # Basic profile information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    display_name = Column(String(150), nullable=True)
    
    # Profile details
    profile_picture_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    phone_number = Column(String(20), nullable=True)
    
    # Location information
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    timezone = Column(String(50), nullable=True, default="UTC")
    
    # Account status and role
    status = Column(String(30), nullable=False, default=UserStatusEnum.PENDING_VERIFICATION.value)
    role = Column(String(20), nullable=False, default=UserRoleEnum.USER.value)
    
    # Email verification
    email_verified = Column(Boolean, nullable=False, default=False)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    email_verification_token = Column(String(255), nullable=True, unique=True)
    email_verification_token_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Password reset
    password_reset_token = Column(String(255), nullable=True, unique=True)
    password_reset_token_expires = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Travel preferences
    preferred_currency = Column(String(3), nullable=False, default=CurrencyEnum.USD.value)
    preferred_travel_style = Column(String(20), nullable=True)
    travel_interests = Column(JSON, nullable=True)  # Array of interests like ['adventure', 'culture', 'food']
    dietary_restrictions = Column(JSON, nullable=True)  # Array of dietary needs
    accessibility_needs = Column(JSON, nullable=True)  # Array of accessibility requirements
    
    # Travel experience
    countries_visited = Column(JSON, nullable=True)  # Array of country codes
    languages_spoken = Column(JSON, nullable=True)  # Array of language codes
    travel_experience_level = Column(String(20), nullable=True)  # beginner, intermediate, expert
    
    # Preferences and settings
    notification_preferences = Column(JSON, nullable=True)  # Email, push, SMS preferences
    privacy_settings = Column(JSON, nullable=True)  # Profile visibility, data sharing preferences
    measurement_system = Column(String(10), nullable=False, default="metric")  # metric or imperial
    
    # Subscription and billing
    subscription_type = Column(String(20), nullable=False, default="free")  # free, premium, enterprise
    subscription_start_date = Column(DateTime(timezone=True), nullable=True)
    subscription_end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Social features
    is_public_profile = Column(Boolean, nullable=False, default=False)
    allow_friend_requests = Column(Boolean, nullable=False, default=True)
    share_travel_stats = Column(Boolean, nullable=False, default=False)
    
    # Security and authentication tracking
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    last_login_location = Column(JSON, nullable=True)  # Store location data from third-party API
    current_login_at = Column(DateTime(timezone=True), nullable=True)
    current_login_location = Column(JSON, nullable=True)  # Store location data from third-party API
    login_count = Column(Integer, nullable=False, default=0)
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    last_failed_login_at = Column(DateTime(timezone=True), nullable=True)
    last_failed_login_location = Column(JSON, nullable=True)  # Store location data from third-party API
    account_locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # Session management
    active_sessions = Column(JSON, nullable=True)  # Store active session tokens/IDs
    last_activity_at = Column(DateTime(timezone=True), nullable=True)
    
    # Two-factor authentication
    two_factor_enabled = Column(Boolean, nullable=False, default=False)
    two_factor_secret = Column(String(255), nullable=True)
    backup_codes = Column(JSON, nullable=True)  # Array of backup codes for 2FA
    
    # Marketing and communication
    marketing_consent = Column(Boolean, nullable=False, default=False)
    newsletter_subscribed = Column(Boolean, nullable=False, default=False)
    
    # Analytics and tracking
    total_trips_created = Column(Integer, nullable=False, default=0)
    total_trips_completed = Column(Integer, nullable=False, default=0)
    favorite_destinations = Column(JSON, nullable=True)  # Top destinations based on user activity
    
    # Onboarding and user journey
    onboarding_completed = Column(Boolean, nullable=False, default=False)
    onboarding_step = Column(Integer, nullable=True)  # Current step in onboarding process
    first_trip_created = Column(Boolean, nullable=False, default=False)
    
    # GDPR and data management
    data_processing_consent = Column(Boolean, nullable=False, default=False)
    data_export_requested_at = Column(DateTime(timezone=True), nullable=True)
    data_deletion_requested_at = Column(DateTime(timezone=True), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete
    
    # Referral system
    referral_code = Column(String(20), nullable=True, unique=True, index=True)
    referred_by_user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    referral_earnings = Column(Float, nullable=False, default=0.0)
    
    # Device and browser tracking
    last_user_agent = Column(Text, nullable=True)
    preferred_language = Column(String(10), nullable=True, default="en")
    
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
    

