from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from dependencies import get_db
from services.traveler_test.user_traveler_test import UserTravelerTestService, get_user_traveler_test_service
from schemas.traveler_test.user_traveler_test import (
    UserTravelerTestCreate, 
    UserTravelerTestUpdate, 
    UserTravelerTestResponse, 
    UserTravelerTestDetailResponse,
    UserTravelerTestStats
)
from utils.jwt_utils import get_current_active_user, get_admin_user
from models.user import User
from datetime import datetime

router = APIRouter(prefix="/traveler-tests", tags=["Traveler Tests"])

# ==================== CRUD ROUTES ====================

@router.post("/", response_model=UserTravelerTestResponse, status_code=status.HTTP_201_CREATED)
async def create_user_traveler_test(
    response: Response,
    current_user: User = Depends(get_current_active_user),
    test_service: UserTravelerTestService = Depends(get_user_traveler_test_service)
):
    """Create a new traveler test for the current user"""
    try:
        # If there's already an active test, return it (idempotent behavior)
        existing = test_service.get_active_test_by_user(current_user.id)
        if existing:
            response.status_code = status.HTTP_200_OK
            return UserTravelerTestResponse.model_validate(existing)

        test_data = UserTravelerTestCreate(
            user_id=current_user.id,
            started_at=datetime.now()
        )
        
        test = test_service.create_user_traveler_test(test_data)
        return UserTravelerTestResponse.model_validate(test)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create traveler test: {str(e)}"
        )


@router.get("/{test_id}", response_model=UserTravelerTestDetailResponse)
async def get_user_traveler_test(
    test_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    test_service: UserTravelerTestService = Depends(get_user_traveler_test_service)
):
    """Get a specific traveler test by ID"""
    test = test_service.get_user_traveler_test_by_id(test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Traveler test not found"
        )
    
    # Ensure user can only access their own tests (unless admin)
    if test.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return UserTravelerTestDetailResponse.model_validate(test)

@router.post("/{test_id}/complete", response_model=UserTravelerTestResponse)
async def complete_user_traveler_test(
    test_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    test_service: UserTravelerTestService = Depends(get_user_traveler_test_service)
):
    """Complete a traveler test"""
    # First get the test to check ownership
    test = test_service.get_user_traveler_test_by_id(test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Traveler test not found"
        )
    
    # Ensure user can only complete their own tests (unless admin)
    if test.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        completed_test = test_service.complete_user_traveler_test(test_id)
        if not completed_test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Traveler test not found"
            )
        
        return UserTravelerTestResponse.model_validate(completed_test)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete traveler test: {str(e)}"
        )

@router.get("/user/me", response_model=List[UserTravelerTestResponse])
async def get_my_traveler_tests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    test_service: UserTravelerTestService = Depends(get_user_traveler_test_service)
):
    """Get all traveler tests for the current user"""
    tests = test_service.get_user_traveler_tests_by_user(current_user.id, skip=skip, limit=limit)
    return [UserTravelerTestResponse.model_validate(test) for test in tests]


@router.get("/user/me/active", response_model=UserTravelerTestDetailResponse)
async def get_my_active_test(
    current_user: User = Depends(get_current_active_user),
    test_service: UserTravelerTestService = Depends(get_user_traveler_test_service)
):
    """Get the active (incomplete) traveler test for the current user"""
    test = test_service.get_active_test_by_user(current_user.id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active test found"
        )
    
    return UserTravelerTestDetailResponse.model_validate(test)


@router.get("/user/me/completed", response_model=List[UserTravelerTestResponse])
async def get_my_completed_tests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    test_service: UserTravelerTestService = Depends(get_user_traveler_test_service)
):
    """Get completed traveler tests for the current user"""
    tests = test_service.get_completed_tests_by_user(current_user.id, skip=skip, limit=limit)
    return [UserTravelerTestResponse.model_validate(test) for test in tests]


@router.put("/{test_id}", response_model=UserTravelerTestResponse)
async def update_user_traveler_test(
    test_id: uuid.UUID,
    test_data: UserTravelerTestUpdate,
    current_user: User = Depends(get_current_active_user),
    test_service: UserTravelerTestService = Depends(get_user_traveler_test_service)
):
    """Update a traveler test"""
    # First get the test to check ownership
    test = test_service.get_user_traveler_test_by_id(test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Traveler test not found"
        )
    
    # Ensure user can only update their own tests (unless admin)
    if test.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    updated_test = test_service.update_user_traveler_test(test_id, test_data)
    if not updated_test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Traveler test not found"
        )
    
    return UserTravelerTestResponse.model_validate(updated_test)

@router.delete("/{test_id}")
async def delete_user_traveler_test(
    test_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    test_service: UserTravelerTestService = Depends(get_user_traveler_test_service)
):
    """Soft delete a traveler test"""
    # First get the test to check ownership
    test = test_service.get_user_traveler_test_by_id(test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Traveler test not found"
        )
    
    # Ensure user can only delete their own tests (unless admin)
    if test.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    success = test_service.soft_delete_user_traveler_test(test_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Traveler test not found"
        )
    
    return {"message": "Traveler test deleted successfully"}


@router.post("/{test_id}/restore", response_model=UserTravelerTestResponse)
async def restore_user_traveler_test(
    test_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    test_service: UserTravelerTestService = Depends(get_user_traveler_test_service)
):
    """Restore a soft-deleted traveler test (admin only)"""
    restored_test = test_service.restore_user_traveler_test(test_id)
    if not restored_test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Traveler test not found or not deleted"
        )
    
    return UserTravelerTestResponse.model_validate(restored_test)


# ==================== BUSINESS LOGIC ROUTES ====================

@router.get("/{test_id}/stats", response_model=UserTravelerTestStats)
async def get_test_stats(
    test_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    test_service: UserTravelerTestService = Depends(get_user_traveler_test_service)
):
    """Get statistics for a specific test"""
    # First get the test to check ownership
    test = test_service.get_user_traveler_test_by_id(test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Traveler test not found"
        )
    
    # Ensure user can only access their own test stats (unless admin)
    if test.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    stats = test_service.get_test_stats(test_id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test statistics not found"
        )
    
    return stats


@router.get("/user/me/history")
async def get_my_test_history(
    current_user: User = Depends(get_current_active_user),
    test_service: UserTravelerTestService = Depends(get_user_traveler_test_service)
):
    """Get comprehensive test history for the current user"""
    history = test_service.get_user_test_history(current_user.id)
    return history


# ==================== ADMIN ROUTES ====================

@router.get("/admin/all", response_model=List[UserTravelerTestResponse])
async def get_all_traveler_tests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    admin_user: User = Depends(get_admin_user),
    test_service: UserTravelerTestService = Depends(get_user_traveler_test_service)
):
    """Get all traveler tests (admin only)"""
    tests = test_service.get_all_user_traveler_tests(skip=skip, limit=limit)
    return [UserTravelerTestResponse.model_validate(test) for test in tests]


@router.get("/admin/analytics")
async def get_test_analytics(
    admin_user: User = Depends(get_admin_user),
    test_service: UserTravelerTestService = Depends(get_user_traveler_test_service)
):
    """Get analytics for all tests (admin only)"""
    analytics = test_service.get_test_analytics()
    return analytics


@router.get("/admin/user/{user_id}", response_model=List[UserTravelerTestResponse])
async def get_user_traveler_tests(
    user_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    admin_user: User = Depends(get_admin_user),
    test_service: UserTravelerTestService = Depends(get_user_traveler_test_service)
):
    """Get all traveler tests for a specific user (admin only)"""
    tests = test_service.get_user_traveler_tests_by_user(user_id, skip=skip, limit=limit)
    return [UserTravelerTestResponse.model_validate(test) for test in tests]


@router.get("/{traveler_test_id}/scores")
async def get_test_scores(
    traveler_test_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    test_service: UserTravelerTestService = Depends(get_user_traveler_test_service)
):
    """Get scores for a specific test"""
    scores = test_service.get_test_scores(traveler_test_id)
    return scores

@router.get("/{traveler_test_id}/user-traveler-type")
async def calculate_user_traveler_type(
    traveler_test_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    test_service: UserTravelerTestService = Depends(get_user_traveler_test_service)
):
    """Calculate the traveler type for a specific test"""
    user_traveler_type = test_service.get_user_traveler_type_by_scores(traveler_test_id)
    return user_traveler_type