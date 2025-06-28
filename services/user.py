from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import Depends
from models.user import User, UserStatusEnum, UserRoleEnum
from schemas.user import UserCreate, UserUpdate, UserLogin, UserPasswordChange, UserPasswordReset, UserPasswordResetConfirm
from dependencies import get_db
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
import uuid
import hashlib
import secrets
import bcrypt
import asyncio


class UserService:
    """Service class for user CRUD operations and business logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== AUTHENTICATION METHODS ====================
    
    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user with hashed password"""
        # Check if email already exists
        if self.get_user_by_email(user_data.email):
            raise ValueError("Email already registered")
        
        # Check if username already exists (if provided)
        if user_data.username and self.get_user_by_username(user_data.username):
            raise ValueError("Username already taken")
        
        # Hash password
        password_hash = self._hash_password(user_data.password)
        
        # Create user data without password
        user_dict = user_data.dict(exclude={'password'})
        user_dict['password_hash'] = password_hash
        
        # Generate email verification token
        verification_token = self._generate_token()
        user_dict['email_verification_token'] = verification_token
        user_dict['email_verification_token_expires'] = datetime.utcnow() + timedelta(hours=24)

        # TODO: send email to user with verification token
        
        # Create user
        db_user = User(**user_dict)
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        # self._send_verification_email(db_user.email, verification_token)
        print(f"TODO:Verification email sent to {db_user.email} with token {verification_token}")
        
        return db_user
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = self.get_user_by_email(email)
        if not user:
            return None
        
        if not self._verify_password(password, user.password_hash):
            # Record failed login attempt
            self.record_failed_login(user.id)
            return None
        
        # Check if account is locked
        if self.is_account_locked(user):
            return None
        
        return user
    
    def record_login(self, user_id: uuid.UUID, location_data: Optional[Dict] = None, user_agent: Optional[str] = None) -> bool:
        """Record successful login with location data from third-party API"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Update login tracking
        user.last_login_at = user.current_login_at
        user.last_login_location = user.current_login_location
        user.current_login_at = datetime.utcnow()
        user.current_login_location = location_data
        user.login_count += 1
        user.failed_login_attempts = 0  # Reset failed attempts
        user.last_activity_at = datetime.utcnow()
        
        if user_agent:
            user.last_user_agent = user_agent
        
        self.db.commit()
        return True
    
    def record_failed_login(self, user_id: uuid.UUID, location_data: Optional[Dict] = None) -> bool:
        """Record failed login attempt with location data"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.failed_login_attempts += 1
        user.last_failed_login_at = datetime.utcnow()
        user.last_failed_login_location = location_data
        
        # Lock account after 5 failed attempts for 30 minutes
        if user.failed_login_attempts >= 5:
            user.account_locked_until = datetime.utcnow() + timedelta(minutes=30)
        
        self.db.commit()
        return True
    
    def is_account_locked(self, user: User) -> bool:
        """Check if user account is currently locked"""
        if user.account_locked_until is not None:
            return datetime.utcnow() < user.account_locked_until.replace(tzinfo=None)
        return False
    
    def unlock_account(self, user_id: uuid.UUID) -> bool:
        """Manually unlock a user account"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.account_locked_until = None
        user.failed_login_attempts = 0
        self.db.commit()
        return True
    
    # ==================== USER CRUD METHODS ====================
    
    def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by UUID (excluding soft deleted)"""
        return self.db.query(User).filter(
            and_(
                User.id == user_id,
                User.deleted_at.is_(None)
            )
        ).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email (excluding soft deleted)"""
        return self.db.query(User).filter(
            and_(
                User.email == email,
                User.deleted_at.is_(None)
            )
        ).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username (excluding soft deleted)"""
        return self.db.query(User).filter(
            and_(
                User.username == username,
                User.deleted_at.is_(None)
            )
        ).first()
    
    def get_users(self, skip: int = 0, limit: int = 100, status: Optional[UserStatusEnum] = None) -> List[User]:
        """Get all users with optional filtering"""
        query = self.db.query(User).filter(User.deleted_at.is_(None))
        
        if status:
            query = query.filter(User.status == status.value)
        
        return query.offset(skip).limit(limit).all()
    
    def search_users(self, query: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Search users by email, username, or display name"""
        search_filter = or_(
            User.email.ilike(f"%{query}%"),
            User.username.ilike(f"%{query}%"),
            User.display_name.ilike(f"%{query}%")
        )
        return self.db.query(User).filter(
            and_(
                search_filter,
                User.deleted_at.is_(None)
            )
        ).offset(skip).limit(limit).all()
    
    def update_user(self, user_id: uuid.UUID, user_data: UserUpdate) -> Optional[User]:
        """Update an existing user"""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Check if username is being changed and is available
        if user_data.username and user_data.username != user.username:
            if self.get_user_by_username(user_data.username):
                raise ValueError("Username already taken")
        
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def soft_delete_user(self, user_id: uuid.UUID) -> bool:
        """Soft delete a user"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.deleted_at = datetime.utcnow()
        user.status = UserStatusEnum.INACTIVE.value
        self.db.commit()
        return True
    
    def restore_user(self, user_id: uuid.UUID) -> Optional[User]:
        """Restore a soft-deleted user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user or user.deleted_at is None:
            return None
        
        user.deleted_at = None
        user.status = UserStatusEnum.ACTIVE.value
        self.db.commit()
        self.db.refresh(user)
        return user
    
    # ==================== BUSINESS LOGIC METHODS ====================
    
    def can_create_trip(self, user: User) -> bool:
        """Check if user can create new trips based on subscription limits"""
        if user.subscription_type in ['premium', 'enterprise']:
            return True
        # Free users have a limit of 5 trips
        return user.total_trips_created < 5
    
    def get_notification_preference(self, user: User, notification_type: str) -> bool:
        """Get specific notification preference for user"""
        if user.notification_preferences and isinstance(user.notification_preferences, dict):
            return user.notification_preferences.get(notification_type, True)
        return True
    
    def update_notification_preferences(self, user_id: uuid.UUID, preferences: Dict[str, bool]) -> bool:
        """Update user notification preferences"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.notification_preferences = preferences
        self.db.commit()
        return True
    
    def add_visited_country(self, user_id: uuid.UUID, country_code: str) -> bool:
        """Add a country to user's visited countries list"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        if user.countries_visited is None:
            user.countries_visited = []
        
        if country_code not in user.countries_visited:
            user.countries_visited.append(country_code)
            self.db.commit()
        
        return True
    
    def increment_trip_count(self, user_id: uuid.UUID, completed: bool = False) -> bool:
        """Increment user's trip counters"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.total_trips_created += 1
        if completed:
            user.total_trips_completed += 1
        
        self.db.commit()
        return True
    
    def update_activity(self, user_id: uuid.UUID) -> bool:
        """Update user's last activity timestamp"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.last_activity_at = datetime.utcnow()
        self.db.commit()
        return True
    
    # ==================== PASSWORD MANAGEMENT ====================
    
    def change_password(self, user_id: uuid.UUID, password_data: UserPasswordChange) -> bool:
        """Change user password"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Verify current password
        if not self._verify_password(password_data.current_password, user.password_hash):
            return False
        
        # Update password
        user.password_hash = self._hash_password(password_data.new_password)
        user.password_changed_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def request_password_reset(self, email: str) -> Optional[str]:
        """Request password reset and return reset token"""
        user = self.get_user_by_email(email)
        if not user:
            return None
        
        # Generate reset token
        reset_token = self._generate_token()
        user.password_reset_token = reset_token
        user.password_reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        
        self.db.commit()
        return reset_token
    
    def reset_password(self, reset_data: UserPasswordResetConfirm) -> bool:
        """Reset password using reset token"""
        user = self.db.query(User).filter(
            and_(
                User.password_reset_token == reset_data.token,
                User.password_reset_token_expires > datetime.utcnow(),
                User.deleted_at.is_(None)
            )
        ).first()
        
        if not user:
            return False
        
        # Update password and clear reset token
        user.password_hash = self._hash_password(reset_data.new_password)
        user.password_reset_token = None
        user.password_reset_token_expires = None
        user.password_changed_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    # ==================== EMAIL VERIFICATION ====================
    
    def verify_email(self, token: str) -> bool:
        """Verify user email using verification token"""
        user = self.db.query(User).filter(
            and_(
                User.email_verification_token == token,
                User.email_verification_token_expires > datetime.utcnow(),
                User.deleted_at.is_(None)
            )
        ).first()
        
        if not user:
            return False
        
        # Mark email as verified
        user.email_verified = True
        user.email_verified_at = datetime.utcnow()
        user.email_verification_token = None
        user.email_verification_token_expires = None
        user.status = UserStatusEnum.ACTIVE.value
        
        self.db.commit()
        return True
    
    def resend_verification_email(self, email: str) -> Optional[str]:
        """Resend email verification token"""
        user = self.get_user_by_email(email)
        if not user or user.email_verified:
            return None
        
        # Generate new verification token
        verification_token = self._generate_token()
        user.email_verification_token = verification_token
        user.email_verification_token_expires = datetime.utcnow() + timedelta(hours=24)
        
        self.db.commit()
        return verification_token
    
    # ==================== STATISTICS AND ANALYTICS ====================
    
    def get_user_stats(self) -> Dict[str, int]:
        """Get user statistics"""
        total_users = self.db.query(User).filter(User.deleted_at.is_(None)).count()
        active_users = self.db.query(User).filter(
            and_(
                User.status == UserStatusEnum.ACTIVE.value,
                User.deleted_at.is_(None)
            )
        ).count()
        verified_users = self.db.query(User).filter(
            and_(
                User.email_verified == True,
                User.deleted_at.is_(None)
            )
        ).count()
        premium_users = self.db.query(User).filter(
            and_(
                User.subscription_type.in_(['premium', 'enterprise']),
                User.deleted_at.is_(None)
            )
        ).count()
        
        today = datetime.utcnow().date()
        users_created_today = self.db.query(User).filter(
            and_(
                func.date(User.created_at) == today,
                User.deleted_at.is_(None)
            )
        ).count()
        
        # First day of current month
        first_day_of_month = today.replace(day=1)
        users_created_this_month = self.db.query(User).filter(
            and_(
                func.date(User.created_at) >= first_day_of_month,
                User.deleted_at.is_(None)
            )
        ).count()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "verified_users": verified_users,
            "premium_users": premium_users,
            "users_created_today": users_created_today,
            "users_created_this_month": users_created_this_month
        }
    
    def get_user_activity_stats(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """Get activity statistics for a specific user"""
        user = self.get_user_by_id(user_id)
        if not user:
            return {}
        
        days_since_registration = (datetime.utcnow() - user.created_at.replace(tzinfo=None)).days
        days_since_last_login = None
        if user.last_login_at:
            days_since_last_login = (datetime.utcnow() - user.last_login_at.replace(tzinfo=None)).days
        
        return {
            "days_since_registration": days_since_registration,
            "days_since_last_login": days_since_last_login,
            "total_logins": user.login_count,
            "total_trips_created": user.total_trips_created,
            "total_trips_completed": user.total_trips_completed,
            "countries_visited_count": len(user.countries_visited) if user.countries_visited else 0,
            "is_premium": user.subscription_type in ['premium', 'enterprise'],
            "account_age_days": days_since_registration
        }
    
    # ==================== PRIVATE HELPER METHODS ====================
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def _generate_token(self) -> str:
        """Generate secure random token"""
        return secrets.token_urlsafe(32)

    async def _send_verification_email_async(self, email: str, user_name: str, token: str) -> bool:
        """Send email verification email asynchronously"""
        try:
            from services.email_service import get_email_service
            email_service = get_email_service()
            return await email_service.send_verification_email(email, user_name, token)
        except Exception as e:
            print(f"Error sending verification email to {email}: {e}")
            return False

    def _send_verification_email(self, email: str, token: str, user_name: str = "User") -> bool:
        """Send verification email (sync wrapper)"""
        try:
            # Run async function in background
            asyncio.create_task(self._send_verification_email_async(email, user_name, token))
            return True
        except Exception as e:
            print(f"Error scheduling verification email: {e}")
            return False

    async def _send_password_reset_email_async(self, email: str, user_name: str, token: str) -> bool:
        """Send password reset email asynchronously"""
        try:
            from services.email_service import get_email_service
            email_service = get_email_service()
            return await email_service.send_password_reset_email(email, user_name, token)
        except Exception as e:
            print(f"Error sending password reset email to {email}: {e}")
            return False

    def _send_password_reset_email(self, email: str, token: str, user_name: str = "User") -> bool:
        """Send password reset email (sync wrapper)"""
        try:
            asyncio.create_task(self._send_password_reset_email_async(email, user_name, token))
            return True
        except Exception as e:
            print(f"Error scheduling password reset email: {e}")
            return False

    async def _send_welcome_email_async(self, email: str, user_name: str) -> bool:
        """Send welcome email asynchronously"""
        try:
            from services.email_service import get_email_service
            email_service = get_email_service()
            return await email_service.send_welcome_email(email, user_name)
        except Exception as e:
            print(f"Error sending welcome email to {email}: {e}")
            return False

    def _send_welcome_email(self, user: User) -> bool:
        """Send welcome email (sync wrapper)"""
        try:
            user_name = user.full_name or user.display_name or user.username or "User"
            asyncio.create_task(self._send_welcome_email_async(user.email, user_name))
            return True
        except Exception as e:
            print(f"Error scheduling welcome email: {e}")
            return False


# ==================== DEPENDENCY INJECTION ====================

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Dependency injection for UserService"""
    return UserService(db)
