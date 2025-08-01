from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, Dict, Any, List
from datetime import datetime, date
import uuid
from models.user import UserStatusEnum, UserRoleEnum, CurrencyEnum, TravelStyleEnum


class UserBase(BaseModel):
    """Base schema with common user fields"""
    email: EmailStr = Field(..., description="User's email address")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Unique username")
    first_name: Optional[str] = Field(None, max_length=100, description="User's first name")
    last_name: Optional[str] = Field(None, max_length=100, description="User's last name")
    display_name: Optional[str] = Field(None, max_length=150, description="Display name for the user")
    bio: Optional[str] = Field(None, max_length=500, description="User biography")
    date_of_birth: Optional[date] = Field(None, description="User's date of birth")
    phone_number: Optional[str] = Field(None, max_length=20, description="User's phone number")
    country: Optional[str] = Field(None, max_length=100, description="User's country")
    city: Optional[str] = Field(None, max_length=100, description="User's city")
    timezone: Optional[str] = Field("UTC", max_length=50, description="User's timezone")
    preferred_currency: CurrencyEnum = Field(CurrencyEnum.USD, description="User's preferred currency")
    preferred_travel_style: Optional[TravelStyleEnum] = Field(None, description="User's preferred travel style")
    travel_interests: Optional[List[str]] = Field(None, description="User's travel interests")
    dietary_restrictions: Optional[List[str]] = Field(None, description="User's dietary restrictions")
    accessibility_needs: Optional[List[str]] = Field(None, description="User's accessibility needs")
    countries_visited: Optional[List[str]] = Field(None, description="List of country codes visited")
    languages_spoken: Optional[List[str]] = Field(None, description="List of language codes spoken")
    travel_experience_level: Optional[str] = Field(None, description="Travel experience level")
    measurement_system: str = Field("metric", description="Preferred measurement system")
    preferred_language: str = Field("en", max_length=10, description="User's preferred language")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            date: lambda v: v.isoformat() if v else None
        }


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, description="User's password (will be hashed)")
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserUpdate(BaseModel):
    """Schema for updating an existing user"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Unique username")
    first_name: Optional[str] = Field(None, max_length=100, description="User's first name")
    last_name: Optional[str] = Field(None, max_length=100, description="User's last name")
    display_name: Optional[str] = Field(None, max_length=150, description="Display name for the user")
    bio: Optional[str] = Field(None, max_length=500, description="User biography")
    date_of_birth: Optional[date] = Field(None, description="User's date of birth")
    phone_number: Optional[str] = Field(None, max_length=20, description="User's phone number")
    country: Optional[str] = Field(None, max_length=100, description="User's country")
    city: Optional[str] = Field(None, max_length=100, description="User's city")
    timezone: Optional[str] = Field(None, max_length=50, description="User's timezone")
    preferred_currency: Optional[CurrencyEnum] = Field(None, description="User's preferred currency")
    preferred_travel_style: Optional[TravelStyleEnum] = Field(None, description="User's preferred travel style")
    travel_interests: Optional[List[str]] = Field(None, description="User's travel interests")
    dietary_restrictions: Optional[List[str]] = Field(None, description="User's dietary restrictions")
    accessibility_needs: Optional[List[str]] = Field(None, description="User's accessibility needs")
    countries_visited: Optional[List[str]] = Field(None, description="List of country codes visited")
    languages_spoken: Optional[List[str]] = Field(None, description="List of language codes spoken")
    travel_experience_level: Optional[str] = Field(None, description="Travel experience level")
    measurement_system: Optional[str] = Field(None, description="Preferred measurement system")
    preferred_language: Optional[str] = Field(None, max_length=10, description="User's preferred language")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            date: lambda v: v.isoformat() if v else None
        }


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class UserResponse(UserBase):
    """Schema for user responses - works with SQLAlchemy ORM"""
    id: uuid.UUID = Field(..., description="Primary key UUID identifier for the user")
    status: UserStatusEnum = Field(..., description="User account status")
    role: UserRoleEnum = Field(..., description="User role")
    email_verified: bool = Field(..., description="Whether email is verified")
    subscription_type: str = Field(..., description="User's subscription type")
    is_public_profile: bool = Field(..., description="Whether profile is public")
    total_trips_created: int = Field(..., description="Total number of trips created")
    total_trips_completed: int = Field(..., description="Total number of trips completed")
    onboarding_completed: bool = Field(..., description="Whether onboarding is completed")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True  # Enable ORM mode for SQLAlchemy compatibility (Pydantic V2)
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            date: lambda v: v.isoformat() if v else None
        }


class UserPublicProfile(BaseModel):
    """Schema for public user profile (limited information)"""
    id: uuid.UUID = Field(..., description="User ID")
    username: Optional[str] = Field(None, description="Username")
    display_name: Optional[str] = Field(None, description="Display name")
    bio: Optional[str] = Field(None, description="User biography")
    country: Optional[str] = Field(None, description="User's country")
    travel_interests: Optional[List[str]] = Field(None, description="Travel interests")
    countries_visited: Optional[List[str]] = Field(None, description="Countries visited")
    total_trips_created: int = Field(..., description="Total trips created")
    total_trips_completed: int = Field(..., description="Total trips completed")
    travel_experience_level: Optional[str] = Field(None, description="Travel experience level")
    
    class Config:
        from_attributes = True
        use_enum_values = True


class UserList(BaseModel):
    """Schema for listing users (admin use)"""
    id: uuid.UUID = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User's email")
    username: Optional[str] = Field(None, description="Username")
    display_name: Optional[str] = Field(None, description="Display name")
    status: UserStatusEnum = Field(..., description="Account status")
    role: UserRoleEnum = Field(..., description="User role")
    email_verified: bool = Field(..., description="Email verification status")
    subscription_type: str = Field(..., description="Subscription type")
    total_trips_created: int = Field(..., description="Total trips created")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class UserPasswordChange(BaseModel):
    """Schema for changing user password"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserPasswordReset(BaseModel):
    """Schema for password reset request"""
    email: EmailStr = Field(..., description="User's email address")


class UserPasswordResetConfirm(BaseModel):
    """Schema for confirming password reset"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserEmailVerification(BaseModel):
    """Schema for email verification"""
    token: str = Field(..., description="Email verification token")


class UserStats(BaseModel):
    """Schema for user statistics"""
    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    verified_users: int = Field(..., description="Number of verified users")
    premium_users: int = Field(..., description="Number of premium users")
    users_created_today: int = Field(..., description="Users created today")
    users_created_this_month: int = Field(..., description="Users created this month")


class UserPreferences(BaseModel):
    """Schema for user preferences"""
    notification_preferences: Optional[Dict[str, bool]] = Field(None, description="Notification preferences")
    privacy_settings: Optional[Dict[str, Any]] = Field(None, description="Privacy settings")
    marketing_consent: bool = Field(False, description="Marketing consent")
    newsletter_subscribed: bool = Field(False, description="Newsletter subscription")
    data_processing_consent: bool = Field(False, description="Data processing consent")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class EmailVerificationResponse(BaseModel):
    """Response model for email verification"""
    message: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class ResendVerificationResponse(BaseModel):
    """Response model for resend verification"""
    message: str