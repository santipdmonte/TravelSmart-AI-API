from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from fastapi import Depends
from models.user import User, UserStatusEnum, UserRoleEnum, UserSocialAccount, AuthProviderType
from schemas.user import UserUpdate
from services.jwt_service import JWTService, get_token_service
from database import get_db
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import os

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


class UserService:
    """Service class for user CRUD operations and business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.token_service: JWTService = get_token_service(db)
    
    # ==================== AUTHENTICATION METHODS ====================
    
    def create_user(self, user: User) -> User:
        """Create a new user with hashed password"""
        exists_user = self.get_user_by_email(user.email)
        if exists_user:
            return exists_user

        db_user = User(user)
        self.db.add(db_user)
        self.db.commit()
        
        return db_user
    
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
        return (
            self.db.query(User)
            .options(joinedload(User.traveler_type))
            .filter(
                and_(
                    User.id == user_id,
                    User.deleted_at.is_(None)
                )
            )
            .first()
    )
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email (excluding soft deleted)"""
        return self.db.query(User).filter(
            and_(
                User.email == email,
                User.deleted_at.is_(None)
            )
        ).first()
    
    def get_users(self, skip: int = 0, limit: int = 100, status: Optional[UserStatusEnum] = None) -> List[User]:
        """Get all users with optional filtering"""
        query = (
            self.db.query(User)
            .options(joinedload(User.traveler_type))
            .filter(User.deleted_at.is_(None))
        )
        
        if status:
            query = query.filter(User.status == status.value)
        
        return query.offset(skip).limit(limit).all()

    def get_users_with_profiles(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[UserStatusEnum] = None,
    ) -> List[User]:
        """Return users eagerly loaded with traveler_type (admin listing)."""
        query = (
            self.db.query(User)
            .options(joinedload(User.traveler_type))
            .filter(User.deleted_at.is_(None))
        )
        if status:
            query = query.filter(User.status == status.value)
        return query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    
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
    
    def update_user(self, user: User, user_update: UserUpdate) -> Optional[User]:
        """Update an existing user"""
        user_update = user_update.model_dump(exclude_unset=True)
        for key, value in user_update.items():
            setattr(user, key, value)

        self.db.commit()
        self.db.refresh(user)
        return user
    
    def soft_delete_user(self, user: User) -> bool:
        """Soft delete a user"""
        user.deleted_at = datetime.utcnow()
        user.status = UserStatusEnum.INACTIVE.value
        self.db.commit()
        return True
    
    def restore_user(self, user: User) -> Optional[User]:
        """Restore a soft-deleted user"""
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

    def get_user_social_accounts(self, user: User):
        return user.social_accounts

    def get_user_social_account(self, provider_id: str):
        return self.db.query(UserSocialAccount).filter(UserSocialAccount.provider_id == provider_id).first()

    def process_google_login(self, user_info: dict):

        user = self.get_user_by_email(user_info['email'])
        if not user:
            user = User(
                email=user_info['email'],
                full_name=user_info['name'],
                first_name=user_info['given_name'],
                last_name=user_info['family_name'],
                profile_picture_url=user_info['picture'],
            )
            self.create_user(user)
        else:
            user_update = UserUpdate(
                full_name=user.full_name or user_info['name'] ,
                first_name=user.first_name or user_info['given_name'] ,
                last_name=user.last_name or user_info['family_name'] ,
                profile_picture_url=user.profile_picture_url or user_info['picture'],
            )
            self.update_user(user, user_update)

        user_social_account = self.get_user_social_account(user_info['sub'])
        if not user_social_account:
            user_social_account = UserSocialAccount(
                user_id=user.id,
                provider=AuthProviderType.GOOGLE,
                provider_id=user_info['sub'],
                email=user_info['email'],
                is_verified=user_info['email_verified'],
                name=user_info['name'],
                given_name=user_info['given_name'],
                family_name=user_info['family_name'],
                picture=user_info['picture'],
            )
            self._create_user_social_account(user_social_account)
            
        else:
            user_social_account.update_last_used()
            self.db.commit()


        # Create new app access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.token_service.create_access_token(
            data={"sub": user_info['email']}, expires_delta=access_token_expires
        )
        refresh_token = self.token_service.create_refresh_token(data={"sub": user_info['email']})
        return access_token, refresh_token
        
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
    

    def _create_user_social_account(self, user_social_account: UserSocialAccount):
        self.db.add(user_social_account)
        self.db.commit()
        self.db.refresh(user_social_account)
        return user_social_account


# ==================== DEPENDENCY INJECTION ====================

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Dependency injection for UserService"""
    return UserService(db)
