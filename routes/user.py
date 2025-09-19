from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional

from services.user import UserService, get_user_service
from schemas.user import UserUpdate, UserResponse, UserPublicProfile, UserStats, UserWithTravelerProfile, UserList
from dependencies import get_current_active_user, get_current_active_admin_user
from models.user import User
from services.traveler_test.travel_style_mapping import TRAVELER_TYPE_STYLE_MAP
from services.jwt_service import JWTService, get_token_service
import uuid

user_router = APIRouter(prefix="/users", tags=["Users"])

# ==================== USER PROFILE ROUTES ====================

@user_router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user profile"""
    # Build base response
    user_resp = UserResponse.model_validate(current_user)

    # Enrich with default_travel_styles if traveler_type available
    try:
        # Prefer eager-loaded relation name if present; fallback to None
        traveler_type_obj = getattr(current_user, "traveler_type", None)
        traveler_type_name = None
        if traveler_type_obj and getattr(traveler_type_obj, "name", None):
            traveler_type_name = traveler_type_obj.name
        # If not eager-loaded, some flows might only have the id; skip DB hit and just omit defaults
        if traveler_type_name:
            user_resp.default_travel_styles = TRAVELER_TYPE_STYLE_MAP.get(traveler_type_name, None)
    except Exception:
        # Do not break the endpoint on enrichment errors
        pass

    return user_resp


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
    admin_user: User = Depends(get_current_active_admin_user),
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
    admin_user: User = Depends(get_current_active_admin_user),
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
    admin_user: User = Depends(get_current_active_admin_user),
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
    admin_user: User = Depends(get_current_active_admin_user),
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
    admin_user: User = Depends(get_current_active_admin_user),
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
    admin_user: User = Depends(get_current_active_admin_user),
    user_service: UserService = Depends(get_user_service)
):
    """Search users (admin only)"""
    users = user_service.search_users(q, skip=skip, limit=limit)
    return [UserList.model_validate(user) for user in users] 