from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List, Optional

from dependencies import get_db
from services.user import UserService, get_user_service
from schemas.user import (
    UserCreate, UserUpdate, UserLogin, UserResponse, UserPublicProfile,
    UserList, UserPasswordChange, UserPasswordReset, UserPasswordResetConfirm,
    UserEmailVerification, UserStats, UserPreferences, EmailVerificationResponse, ResendVerificationResponse,
    UserWithTravelerProfile,
)
from utils.jwt_utils import (
    get_current_user, get_current_active_user, get_admin_user,
    create_token_response, verify_token
)
from models.user import User
import uuid

router = APIRouter(prefix="/auth", tags=["Authentication"])
user_router = APIRouter(prefix="/users", tags=["Users"])

# ==================== AUTHENTICATION ROUTES ====================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    user_service: UserService = Depends(get_user_service)
):
    """Register a new user"""
    try:
        user = user_service.create_user(user_data)
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login")
async def login(
    login_data: UserLogin,
    request: Request,
    user_service: UserService = Depends(get_user_service)
):
    """Authenticate user and return JWT tokens"""
    # Authenticate user
    user = user_service.authenticate_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if email is verified
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your email and verify your account."
        )
    
    # Record successful login
    # Note: In production, you'd get location from IP geolocation service
    user_agent = request.headers.get("User-Agent")
    user_service.record_login(
        user_id=user.id,
        location_data=None,  # TODO: Implement location service
        user_agent=user_agent
    )
    
    # Create token response
    token_data = create_token_response(user)
    token_data["user"] = UserResponse.model_validate(user)
    
    return token_data


@router.post("/refresh-token")
async def refresh_token(
    refresh_token: str,
    request: Request,
    user_service: UserService = Depends(get_user_service)
):
    """Refresh access token using refresh token"""
    # Verify refresh token
    payload = verify_token(refresh_token, token_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user
    user_id_str = payload.get("sub")
    user = user_service.get_user_by_id(uuid.UUID(user_id_str))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Record login activity
    user_agent = request.headers.get("User-Agent")
    user_service.record_login(
        user_id=user.id,
        location_data=None,
        user_agent=user_agent
    )
    
    # Create new token response
    return create_token_response(user)


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """Logout user (in a real app, you'd blacklist the token)"""
    # TODO: Implement token blacklisting or you can trust the token to be invalidated by the client
    return {"message": "Successfully logged out"}


# ==================== EMAIL VERIFICATION ROUTES ====================

@router.get("/verify-email", response_model=EmailVerificationResponse)
async def verify_email(
    request: Request,
    token: str = Query(..., description="Email verification token"),
    user_service: UserService = Depends(get_user_service)
):
    """Verify user email with token and return JWT tokens for auto-login"""
    success, user = user_service.verify_email(token)
    if not success or not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Record successful login for the verified user
    user_agent = request.headers.get("User-Agent")
    user_service.record_login(
        user_id=user.id,
        location_data=None,  # TODO: Implement location service
        user_agent=user_agent
    )
    
    # Create token response for auto-login
    from utils.jwt_utils import create_token_response
    token_data = create_token_response(user)
    token_data["user"] = UserResponse.model_validate(user)
    token_data["message"] = "Email verified successfully. Welcome to TravelSmart AI!"
    
    return token_data


@router.post("/resend-verification", response_model=ResendVerificationResponse)
async def resend_verification(
    email_data: UserPasswordReset,  # Reusing this schema as it only has email field
    user_service: UserService = Depends(get_user_service)
):
    """Resend email verification"""
    token = user_service.resend_verification_email(email_data.email)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not found or already verified"
        )
    
    return ResendVerificationResponse(message="Verification email sent successfully")

@router.post("/verify-email-token", response_model=EmailVerificationResponse)
async def verify_email_token(
    request: Request,
    token: str = Query(..., description="Email verification token"),
    user_service: UserService = Depends(get_user_service)
):
    """Verify email token and return user data (for frontend integration)"""
    success, user = user_service.verify_email(token)
    if not success or not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Record successful login for the verified user
    user_agent = request.headers.get("User-Agent")
    user_service.record_login(
        user_id=user.id,
        location_data=None,
        user_agent=user_agent
    )
    
    # Create token response for auto-login
    from utils.jwt_utils import create_token_response
    token_data = create_token_response(user)
    token_data["user"] = UserResponse.model_validate(user)
    token_data["message"] = "Email verified successfully. Welcome to TravelSmart AI!"
    
    return token_data


# ==================== PASSWORD MANAGEMENT ROUTES ====================

@router.post("/forgot-password")
async def forgot_password(
    email_data: UserPasswordReset,
    user_service: UserService = Depends(get_user_service)
):
    """Request password reset"""
    token = user_service.request_password_reset(email_data.email)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    
    return {"message": "Password reset email sent"}


@router.post("/reset-password")
async def reset_password(
    reset_data: UserPasswordResetConfirm,
    user_service: UserService = Depends(get_user_service)
):
    """Reset password with token"""
    try:
        success = user_service.reset_password(reset_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
    except ValueError as e: # 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return {"message": "Password reset successfully"}


@router.post("/change-password")
async def change_password(
    password_data: UserPasswordChange,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """Change user password"""
    try:
        user_service.change_password(current_user.id, password_data)
    except ValueError as e: # <-- BLOQUE AÑADIDO Y LÓGICA SIMPLIFICADA
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return {"message": "Password changed successfully"}


# ==================== USER PROFILE ROUTES ====================

@user_router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user profile"""
    return UserResponse.model_validate(current_user)


@user_router.put("/profile", response_model=UserResponse)
async def update_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """Update current user profile"""
    try:
        updated_user = user_service.update_user(current_user.id, user_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return UserResponse.model_validate(updated_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@user_router.delete("/profile")
async def delete_account(
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """Delete current user account (soft delete)"""
    success = user_service.soft_delete_user(current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "Account deleted successfully"}


# ==================== PUBLIC PROFILE ROUTES ====================

@user_router.get("/{user_id}/public", response_model=UserPublicProfile)
async def get_public_profile(
    user_id: uuid.UUID,
    user_service: UserService = Depends(get_user_service)
):
    """Get public user profile"""
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_public_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Profile is private"
        )
    
    return UserPublicProfile.model_validate(user)


# ==================== ADMIN ROUTES ====================

@user_router.get("/", response_model=List[UserList])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    admin_user: User = Depends(get_admin_user),
    user_service: UserService = Depends(get_user_service)
):
    """List all users (admin only)"""
    from models.user import UserStatusEnum
    
    status_enum = None
    if status:
        try:
            status_enum = UserStatusEnum(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status value"
            )
    
    users = user_service.get_users(skip=skip, limit=limit, status=status_enum)
    return [UserList.model_validate(user) for user in users]


@user_router.get("/with-profiles", response_model=List[UserWithTravelerProfile])
async def list_users_with_profiles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    admin_user: User = Depends(get_admin_user),
    user_service: UserService = Depends(get_user_service),
):
    """List users with their traveler profile eagerly loaded (admin only)."""
    from models.user import UserStatusEnum

    status_enum = None
    if status:
        try:
            status_enum = UserStatusEnum(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status value",
            )

    users = user_service.get_users_with_profiles(
        skip=skip, limit=limit, status=status_enum
    )
    return [UserWithTravelerProfile.model_validate(u) for u in users]


@user_router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get user by ID (admin only)"""
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)


@user_router.post("/{user_id}/unlock")
async def unlock_user_account(
    user_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    user_service: UserService = Depends(get_user_service)
):
    """Unlock user account (admin only)"""
    success = user_service.unlock_account(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "Account unlocked successfully"}


# ==================== STATISTICS ROUTES ====================

@user_router.get("/stats/overview", response_model=UserStats)
async def get_user_statistics(
    admin_user: User = Depends(get_admin_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get user statistics (admin only)"""
    stats = user_service.get_user_stats()
    return UserStats(**stats)


@user_router.get("/search")
async def search_users(
    q: str = Query(..., min_length=2, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    admin_user: User = Depends(get_admin_user),
    user_service: UserService = Depends(get_user_service)
):
    """Search users (admin only)"""
    users = user_service.search_users(q, skip=skip, limit=limit)
    return [UserList.model_validate(user) for user in users] 