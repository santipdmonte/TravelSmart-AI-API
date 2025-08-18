from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid

from dependencies import get_db
from services.traveler_test.user_answers import UserAnswerService, get_user_answer_service
from schemas.traveler_test.user_answers import (
    UserAnswerCreate, 
    UserAnswerUpdate, 
    UserAnswerResponse, 
    UserAnswerDetailResponse,
    UserAnswerBulkCreate
)
from utils.jwt_utils import get_current_active_user, get_admin_user
from models.user import User

router = APIRouter(prefix="/user-answers", tags=["User Answers"])

# ==================== CRUD ROUTES ====================

@router.post("/", response_model=UserAnswerResponse, status_code=status.HTTP_201_CREATED)
async def create_user_answer(
    answer_data: UserAnswerCreate,
    current_user: User = Depends(get_current_active_user),
    answer_service: UserAnswerService = Depends(get_user_answer_service)
):
    """Create a new user answer"""
    try:
        # Validate that the user owns the test
        from services.traveler_test.user_traveler_test import UserTravelerTestService
        test_service = UserTravelerTestService(answer_service.db)
        test = test_service.get_user_traveler_test_by_id(answer_data.user_traveler_test_id)
        
        if not test or test.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this test"
            )
        
        answer = answer_service.create_user_answer(answer_data)
        return UserAnswerResponse.model_validate(answer)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user answer: {str(e)}"
        )


@router.get("/{answer_id}", response_model=UserAnswerDetailResponse)
async def get_user_answer(
    answer_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    answer_service: UserAnswerService = Depends(get_user_answer_service)
):
    """Get a specific user answer by ID"""
    answer = answer_service.get_user_answer_by_id(answer_id)
    if not answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User answer not found"
        )
    
    # Validate that the user owns the test
    from services.traveler_test.user_traveler_test import UserTravelerTestService
    test_service = UserTravelerTestService(answer_service.db)
    test = test_service.get_user_traveler_test_by_id(answer.user_traveler_test_id)
    
    if not test or test.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this answer"
        )
    
    return UserAnswerDetailResponse.model_validate(answer)


@router.get("/", response_model=List[UserAnswerResponse])
async def get_all_user_answers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    admin_user: User = Depends(get_admin_user),
    answer_service: UserAnswerService = Depends(get_user_answer_service)
):
    """Get all user answers (admin only)"""
    answers = answer_service.get_all_user_answers(skip=skip, limit=limit)
    return [UserAnswerResponse.model_validate(answer) for answer in answers]


@router.get("/test/{user_traveler_test_id}", response_model=List[UserAnswerResponse])
async def get_answers_by_user_test(
    user_traveler_test_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    answer_service: UserAnswerService = Depends(get_user_answer_service)
):
    """Get all active answers for a specific user traveler test"""
    # Validate that the user owns the test
    from services.traveler_test.user_traveler_test import UserTravelerTestService
    test_service = UserTravelerTestService(answer_service.db)
    test = test_service.get_user_traveler_test_by_id(user_traveler_test_id)
    
    if not test or test.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this test"
        )
    
    answers = answer_service.get_answers_by_user_test(user_traveler_test_id, skip=skip, limit=limit)
    return [UserAnswerResponse.model_validate(answer) for answer in answers]


@router.get("/test/{user_traveler_test_id}/all", response_model=List[UserAnswerResponse])
async def get_all_answers_by_user_test(
    user_traveler_test_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    admin_user: User = Depends(get_admin_user),
    answer_service: UserAnswerService = Depends(get_user_answer_service)
):
    """Get all answers (including deleted) for a specific user traveler test (admin only)"""
    answers = answer_service.get_all_answers_by_user_test(user_traveler_test_id, skip=skip, limit=limit)
    return [UserAnswerResponse.model_validate(answer) for answer in answers]


@router.get("/user/me", response_model=List[UserAnswerResponse])
async def get_my_answers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    answer_service: UserAnswerService = Depends(get_user_answer_service)
):
    """Get all answers for the current user across all tests"""
    answers = answer_service.get_answers_by_user(current_user.id, skip=skip, limit=limit)
    return [UserAnswerResponse.model_validate(answer) for answer in answers]


@router.get("/question-option/{question_option_id}", response_model=List[UserAnswerResponse])
async def get_answers_by_question_option(
    question_option_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    admin_user: User = Depends(get_admin_user),
    answer_service: UserAnswerService = Depends(get_user_answer_service)
):
    """Get all answers for a specific question option (admin only)"""
    answers = answer_service.get_answers_by_question_option(question_option_id, skip=skip, limit=limit)
    return [UserAnswerResponse.model_validate(answer) for answer in answers]


@router.put("/{answer_id}", response_model=UserAnswerResponse)
async def update_user_answer(
    answer_id: uuid.UUID,
    answer_data: UserAnswerUpdate,
    current_user: User = Depends(get_current_active_user),
    answer_service: UserAnswerService = Depends(get_user_answer_service)
):
    """Update a user answer"""
    # First get the answer to check ownership
    answer = answer_service.get_user_answer_by_id(answer_id)
    if not answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User answer not found"
        )
    
    # Validate that the user owns the test
    from services.traveler_test.user_traveler_test import UserTravelerTestService
    test_service = UserTravelerTestService(answer_service.db)
    test = test_service.get_user_traveler_test_by_id(answer.user_traveler_test_id)
    
    if not test or test.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this answer"
        )
    
    try:
        updated_answer = answer_service.update_user_answer(answer_id, answer_data)
        if not updated_answer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User answer not found"
            )
        
        return UserAnswerResponse.model_validate(updated_answer)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{answer_id}")
async def delete_user_answer(
    answer_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    answer_service: UserAnswerService = Depends(get_user_answer_service)
):
    """Soft delete a user answer"""
    # First get the answer to check ownership
    answer = answer_service.get_user_answer_by_id(answer_id)
    if not answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User answer not found"
        )
    
    # Validate that the user owns the test
    from services.traveler_test.user_traveler_test import UserTravelerTestService
    test_service = UserTravelerTestService(answer_service.db)
    test = test_service.get_user_traveler_test_by_id(answer.user_traveler_test_id)
    
    if not test or test.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this answer"
        )
    
    success = answer_service.soft_delete_user_answer(answer_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User answer not found"
        )
    
    return {"message": "User answer deleted successfully"}


@router.post("/{answer_id}/restore", response_model=UserAnswerResponse)
async def restore_user_answer(
    answer_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    answer_service: UserAnswerService = Depends(get_user_answer_service)
):
    """Restore a soft-deleted user answer (admin only)"""
    restored_answer = answer_service.restore_user_answer(answer_id)
    if not restored_answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User answer not found or not deleted"
        )
    
    return UserAnswerResponse.model_validate(restored_answer)


@router.delete("/{answer_id}/permanent")
async def delete_user_answer_permanently(
    answer_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    answer_service: UserAnswerService = Depends(get_user_answer_service)
):
    """Permanently delete a user answer (admin only)"""
    success = answer_service.delete_user_answer_permanently(answer_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User answer not found"
        )
    
    return {"message": "User answer permanently deleted"}


@router.post("/change", response_model=UserAnswerResponse)
async def change_user_answer(
    user_traveler_test_id: uuid.UUID,
    old_question_option_id: uuid.UUID,
    new_question_option_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    answer_service: UserAnswerService = Depends(get_user_answer_service)
):
    """Change a user's answer by soft deleting the old one and creating a new one"""
    try:
        # Validate that the user owns the test
        from services.traveler_test.user_traveler_test import UserTravelerTestService
        test_service = UserTravelerTestService(answer_service.db)
        test = test_service.get_user_traveler_test_by_id(user_traveler_test_id)
        
        if not test or test.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this test"
            )
        
        new_answer = answer_service.change_user_answer(
            user_traveler_test_id, 
            old_question_option_id, 
            new_question_option_id
        )
        return UserAnswerResponse.model_validate(new_answer)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change user answer: {str(e)}"
        )


# ==================== BUSINESS LOGIC ROUTES ====================

@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def bulk_create_user_answers(
    answers_data: UserAnswerBulkCreate,
    current_user: User = Depends(get_current_active_user),
    answer_service: UserAnswerService = Depends(get_user_answer_service)
):
    """Create multiple user answers at once and return the final test result.

    This endpoint replaces any existing active answers for the given test, completes the test,
    and returns a summary including the resolved traveler type and scores. It ensures that all
    referenced questions/options are active (not soft-deleted).
    """
    try:
        # Validate that the user owns the test
        from services.traveler_test.user_traveler_test import UserTravelerTestService
        test_service = UserTravelerTestService(answer_service.db)
        test = test_service.get_user_traveler_test_by_id(answers_data.user_traveler_test_id)
        
        if not test or test.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this test"
            )

        # Persist all answers (with validation and soft-delete of existing)
        answer_service.bulk_create_answers(answers_data)

        # Complete the test and compute result
        completed_test = test_service.complete_user_traveler_test(answers_data.user_traveler_test_id)
        if not completed_test:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Traveler test not found")

        raw_scores = test_service.get_test_scores(answers_data.user_traveler_test_id) or {}
        scores = {str(k): float(v) for k, v in raw_scores.items()}

        from schemas.traveler_test.user_traveler_test import UserTravelerTestResponse
        from schemas.traveler_test.traveler_type import TravelerTypeResponse
        from models.traveler_test.traveler_type import TravelerType

        traveler_type = None
        if completed_test.traveler_type_id:
            traveler = answer_service.db.query(TravelerType).filter(TravelerType.id == completed_test.traveler_type_id).first()
            traveler_type = TravelerTypeResponse.model_validate(traveler) if traveler else None

        return {
            "user_traveler_test": UserTravelerTestResponse.model_validate(completed_test),
            "traveler_type": traveler_type,
            "scores": scores,
            "completion_time_minutes": getattr(completed_test, "duration_minutes", None),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user answers: {str(e)}"
        )


@router.get("/stats/overview")
async def get_user_answer_statistics(
    admin_user: User = Depends(get_admin_user),
    answer_service: UserAnswerService = Depends(get_user_answer_service)
):
    """Get user answer statistics (admin only)"""
    stats = answer_service.get_user_answer_statistics()
    return stats


@router.get("/test/{user_traveler_test_id}/progress")
async def get_user_test_progress(
    user_traveler_test_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    answer_service: UserAnswerService = Depends(get_user_answer_service)
):
    """Get progress information for a user test"""
    # Validate that the user owns the test
    from services.traveler_test.user_traveler_test import UserTravelerTestService
    test_service = UserTravelerTestService(answer_service.db)
    test = test_service.get_user_traveler_test_by_id(user_traveler_test_id)
    
    if not test or test.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this test"
        )
    
    progress = answer_service.get_user_test_progress(user_traveler_test_id)
    return progress


@router.get("/test/{user_traveler_test_id}/with-details")
async def get_user_answers_with_details(
    user_traveler_test_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    answer_service: UserAnswerService = Depends(get_user_answer_service)
):
    """Get user answers with detailed information"""
    # Validate that the user owns the test
    from services.traveler_test.user_traveler_test import UserTravelerTestService
    test_service = UserTravelerTestService(answer_service.db)
    test = test_service.get_user_traveler_test_by_id(user_traveler_test_id)
    
    if not test or test.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this test"
        )
    
    answers_with_details = answer_service.get_user_answers_with_details(user_traveler_test_id)
    return answers_with_details


# ==================== PUBLIC ROUTES ====================

@router.get("/public/all", response_model=List[UserAnswerResponse])
async def get_public_user_answers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    answer_service: UserAnswerService = Depends(get_user_answer_service)
):
    """Get all active user answers (public endpoint)"""
    answers = answer_service.get_active_user_answers(skip=skip, limit=limit)
    return [UserAnswerResponse.model_validate(answer) for answer in answers]


@router.get("/public/test/{user_traveler_test_id}", response_model=List[UserAnswerResponse])
async def get_public_answers_by_user_test(
    user_traveler_test_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    answer_service: UserAnswerService = Depends(get_user_answer_service)
):
    """Get all answers for a specific user traveler test (public endpoint)"""
    answers = answer_service.get_answers_by_user_test(user_traveler_test_id, skip=skip, limit=limit)
    return [UserAnswerResponse.model_validate(answer) for answer in answers]
