from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid

from dependencies import get_db
from services.traveler_test.question_option import QuestionOptionService, get_question_option_service
from schemas.traveler_test.question_option import (
    QuestionOptionCreate, 
    QuestionOptionUpdate, 
    QuestionOptionResponse, 
    QuestionOptionDetailResponse
)
from utils.jwt_utils import get_current_active_user, get_admin_user
from models.user import User

router = APIRouter(prefix="/question-options", tags=["Question Options"])

# ==================== CRUD ROUTES ====================

@router.post("/", response_model=QuestionOptionResponse, status_code=status.HTTP_201_CREATED)
async def create_question_option(
    option_data: QuestionOptionCreate,
    admin_user: User = Depends(get_admin_user),
    option_service: QuestionOptionService = Depends(get_question_option_service)
):
    """Create a new question option (admin only)"""
    try:
        option = option_service.create_question_option(option_data)
        return QuestionOptionResponse.model_validate(option)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create question option: {str(e)}"
        )


@router.get("/{option_id}", response_model=QuestionOptionDetailResponse)
async def get_question_option(
    option_id: uuid.UUID,
    option_service: QuestionOptionService = Depends(get_question_option_service)
):
    """Get a specific question option by ID"""
    option = option_service.get_question_option_by_id(option_id)
    if not option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question option not found"
        )
    
    return QuestionOptionDetailResponse.model_validate(option)


@router.get("/", response_model=List[QuestionOptionResponse])
async def get_all_question_options(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    option_service: QuestionOptionService = Depends(get_question_option_service)
):
    """Get all question options"""
    options = option_service.get_all_question_options(skip=skip, limit=limit)
    return [QuestionOptionResponse.model_validate(option) for option in options]


@router.get("/question/{question_id}", response_model=List[QuestionOptionResponse])
async def get_question_options_by_question(
    question_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    option_service: QuestionOptionService = Depends(get_question_option_service)
):
    """Get all options for a specific question"""
    options = option_service.get_question_options_by_question(question_id, skip=skip, limit=limit)
    return [QuestionOptionResponse.model_validate(option) for option in options]


@router.put("/{option_id}", response_model=QuestionOptionResponse)
async def update_question_option(
    option_id: uuid.UUID,
    option_data: QuestionOptionUpdate,
    admin_user: User = Depends(get_admin_user),
    option_service: QuestionOptionService = Depends(get_question_option_service)
):
    """Update a question option (admin only)"""
    try:
        updated_option = option_service.update_question_option(option_id, option_data)
        if not updated_option:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question option not found"
            )
        
        return QuestionOptionResponse.model_validate(updated_option)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{option_id}")
async def delete_question_option(
    option_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    option_service: QuestionOptionService = Depends(get_question_option_service)
):
    """Soft delete a question option (admin only)"""
    success = option_service.soft_delete_question_option(option_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question option not found"
        )
    
    return {"message": "Question option deleted successfully"}


@router.post("/{option_id}/restore", response_model=QuestionOptionResponse)
async def restore_question_option(
    option_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    option_service: QuestionOptionService = Depends(get_question_option_service)
):
    """Restore a soft-deleted question option (admin only)"""
    restored_option = option_service.restore_question_option(option_id)
    if not restored_option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question option not found or not deleted"
        )
    
    return QuestionOptionResponse.model_validate(restored_option)


@router.delete("/{option_id}/permanent")
async def delete_question_option_permanently(
    option_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    option_service: QuestionOptionService = Depends(get_question_option_service)
):
    """Permanently delete a question option (admin only)"""
    success = option_service.delete_question_option_permanently(option_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question option not found"
        )
    
    return {"message": "Question option permanently deleted"}


# ==================== BUSINESS LOGIC ROUTES ====================

@router.post("/bulk", response_model=List[QuestionOptionResponse], status_code=status.HTTP_201_CREATED)
async def bulk_create_question_options(
    options_data: List[QuestionOptionCreate],
    admin_user: User = Depends(get_admin_user),
    option_service: QuestionOptionService = Depends(get_question_option_service)
):
    """Create multiple question options at once (admin only)"""
    try:
        created_options = option_service.bulk_create_options(options_data)
        return [QuestionOptionResponse.model_validate(option) for option in created_options]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create question options: {str(e)}"
        )


@router.get("/stats/overview")
async def get_question_option_statistics(
    admin_user: User = Depends(get_admin_user),
    option_service: QuestionOptionService = Depends(get_question_option_service)
):
    """Get question option statistics (admin only)"""
    stats = option_service.get_question_option_statistics()
    return stats


@router.get("/search/")
async def search_question_options(
    q: str = Query(..., min_length=2, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    option_service: QuestionOptionService = Depends(get_question_option_service)
):
    """Search question options by text"""
    options = option_service.search_question_options(q, skip=skip, limit=limit)
    return [QuestionOptionResponse.model_validate(option) for option in options]


@router.get("/category/{category}", response_model=List[QuestionOptionResponse])
async def get_options_by_question_category(
    category: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    option_service: QuestionOptionService = Depends(get_question_option_service)
):
    """Get options for questions in a specific category"""
    options = option_service.get_options_by_question_category(category, skip=skip, limit=limit)
    return [QuestionOptionResponse.model_validate(option) for option in options]


@router.get("/with-scores/")
async def get_options_with_scores(
    question_id: Optional[uuid.UUID] = Query(None, description="Filter by question ID"),
    option_service: QuestionOptionService = Depends(get_question_option_service)
):
    """Get options with their associated scores"""
    options_with_scores = option_service.get_options_with_scores(question_id)
    return options_with_scores


# ==================== PUBLIC ROUTES ====================

@router.get("/public/all", response_model=List[QuestionOptionResponse])
async def get_public_question_options(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    option_service: QuestionOptionService = Depends(get_question_option_service)
):
    """Get all active question options (public endpoint)"""
    options = option_service.get_active_question_options(skip=skip, limit=limit)
    return [QuestionOptionResponse.model_validate(option) for option in options]


@router.get("/public/question/{question_id}", response_model=List[QuestionOptionResponse])
async def get_public_question_options_by_question(
    question_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    option_service: QuestionOptionService = Depends(get_question_option_service)
):
    """Get all options for a specific question (public endpoint)"""
    options = option_service.get_question_options_by_question(question_id, skip=skip, limit=limit)
    return [QuestionOptionResponse.model_validate(option) for option in options]


@router.get("/public/category/{category}", response_model=List[QuestionOptionResponse])
async def get_public_options_by_question_category(
    category: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    option_service: QuestionOptionService = Depends(get_question_option_service)
):
    """Get options for questions in a specific category (public endpoint)"""
    options = option_service.get_options_by_question_category(category, skip=skip, limit=limit)
    return [QuestionOptionResponse.model_validate(option) for option in options]
