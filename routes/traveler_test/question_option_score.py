from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid

from database import get_db
from services.traveler_test.question_option_score import QuestionOptionScoreService, get_question_option_score_service
from schemas.traveler_test.question_option_score import (
    QuestionOptionScoreCreate, 
    QuestionOptionScoreUpdate, 
    QuestionOptionScoreResponse, 
    QuestionOptionScoreDetailResponse
)
from dependencies import get_current_active_user, get_current_active_admin_user
from models.user import User

router = APIRouter(prefix="/question-option-scores", tags=["Question Option Scores"])

# ==================== CRUD ROUTES ====================

@router.post("/", response_model=QuestionOptionScoreResponse, status_code=status.HTTP_201_CREATED)
async def create_question_option_score(
    score_data: QuestionOptionScoreCreate,
    admin_user: User = Depends(get_current_active_admin_user),
    score_service: QuestionOptionScoreService = Depends(get_question_option_score_service)
):
    """Create a new question option score (admin only)"""
    try:
        score = score_service.create_question_option_score(score_data)
        return QuestionOptionScoreResponse.model_validate(score)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create question option score: {str(e)}"
        )


@router.get("/{score_id}", response_model=QuestionOptionScoreDetailResponse)
async def get_question_option_score(
    score_id: uuid.UUID,
    score_service: QuestionOptionScoreService = Depends(get_question_option_score_service)
):
    """Get a specific question option score by ID"""
    score = score_service.get_question_option_score_by_id(score_id)
    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question option score not found"
        )
    
    return QuestionOptionScoreDetailResponse.model_validate(score)


@router.get("/", response_model=List[QuestionOptionScoreResponse])
async def get_all_question_option_scores(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    score_service: QuestionOptionScoreService = Depends(get_question_option_score_service)
):
    """Get all question option scores"""
    scores = score_service.get_all_question_option_scores(skip=skip, limit=limit)
    return [QuestionOptionScoreResponse.model_validate(score) for score in scores]


@router.get("/option/{question_option_id}", response_model=List[QuestionOptionScoreResponse])
async def get_scores_by_question_option(
    question_option_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    score_service: QuestionOptionScoreService = Depends(get_question_option_score_service)
):
    """Get all scores for a specific question option"""
    scores = score_service.get_scores_by_question_option(question_option_id, skip=skip, limit=limit)
    return [QuestionOptionScoreResponse.model_validate(score) for score in scores]


@router.get("/traveler-type/{traveler_type_id}", response_model=List[QuestionOptionScoreResponse])
async def get_scores_by_traveler_type(
    traveler_type_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    score_service: QuestionOptionScoreService = Depends(get_question_option_score_service)
):
    """Get all scores for a specific traveler type"""
    scores = score_service.get_scores_by_traveler_type(traveler_type_id, skip=skip, limit=limit)
    return [QuestionOptionScoreResponse.model_validate(score) for score in scores]


@router.get("/option/{question_option_id}/traveler-type/{traveler_type_id}", response_model=QuestionOptionScoreDetailResponse)
async def get_score_by_option_and_type(
    question_option_id: uuid.UUID,
    traveler_type_id: uuid.UUID,
    score_service: QuestionOptionScoreService = Depends(get_question_option_score_service)
):
    """Get a score by question option ID and traveler type ID"""
    score = score_service.get_score_by_option_and_type(question_option_id, traveler_type_id)
    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question option score not found"
        )
    
    return QuestionOptionScoreDetailResponse.model_validate(score)


@router.put("/{score_id}", response_model=QuestionOptionScoreResponse)
async def update_question_option_score(
    score_id: uuid.UUID,
    score_data: QuestionOptionScoreUpdate,
    admin_user: User = Depends(get_current_active_admin_user),
    score_service: QuestionOptionScoreService = Depends(get_question_option_score_service)
):
    """Update a question option score (admin only)"""
    try:
        updated_score = score_service.update_question_option_score(score_id, score_data)
        if not updated_score:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question option score not found"
            )
        
        return QuestionOptionScoreResponse.model_validate(updated_score)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{score_id}")
async def delete_question_option_score(
    score_id: uuid.UUID,
    admin_user: User = Depends(get_current_active_admin_user),
    score_service: QuestionOptionScoreService = Depends(get_question_option_score_service)
):
    """Soft delete a question option score (admin only)"""
    success = score_service.soft_delete_question_option_score(score_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question option score not found"
        )
    
    return {"message": "Question option score deleted successfully"}


@router.post("/{score_id}/restore", response_model=QuestionOptionScoreResponse)
async def restore_question_option_score(
    score_id: uuid.UUID,
    admin_user: User = Depends(get_current_active_admin_user),
    score_service: QuestionOptionScoreService = Depends(get_question_option_score_service)
):
    """Restore a soft-deleted question option score (admin only)"""
    restored_score = score_service.restore_question_option_score(score_id)
    if not restored_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question option score not found or not deleted"
        )
    
    return QuestionOptionScoreResponse.model_validate(restored_score)


@router.delete("/{score_id}/permanent")
async def delete_question_option_score_permanently(
    score_id: uuid.UUID,
    admin_user: User = Depends(get_current_active_admin_user),
    score_service: QuestionOptionScoreService = Depends(get_question_option_score_service)
):
    """Permanently delete a question option score (admin only)"""
    success = score_service.delete_question_option_score_permanently(score_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question option score not found"
        )
    
    return {"message": "Question option score permanently deleted"}


# ==================== BUSINESS LOGIC ROUTES ====================

@router.post("/bulk", response_model=List[QuestionOptionScoreResponse], status_code=status.HTTP_201_CREATED)
async def bulk_create_question_option_scores(
    scores_data: List[QuestionOptionScoreCreate],
    admin_user: User = Depends(get_current_active_admin_user),
    score_service: QuestionOptionScoreService = Depends(get_question_option_score_service)
):
    """Create multiple question option scores at once (admin only)"""
    try:
        created_scores = score_service.bulk_create_scores(scores_data)
        return [QuestionOptionScoreResponse.model_validate(score) for score in created_scores]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create question option scores: {str(e)}"
        )


@router.get("/stats/overview")
async def get_question_option_score_statistics(
    admin_user: User = Depends(get_current_active_admin_user),
    score_service: QuestionOptionScoreService = Depends(get_question_option_score_service)
):
    """Get question option score statistics (admin only)"""
    stats = score_service.get_question_option_score_statistics()
    return stats


@router.get("/question/{question_id}")
async def get_scores_by_question(
    question_id: uuid.UUID,
    score_service: QuestionOptionScoreService = Depends(get_question_option_score_service)
):
    """Get all scores for a specific question"""
    scores = score_service.get_scores_by_question(question_id)
    return scores


@router.get("/category/{category}")
async def get_scores_by_question_category(
    category: str,
    score_service: QuestionOptionScoreService = Depends(get_question_option_score_service)
):
    """Get all scores for questions in a specific category"""
    scores = score_service.get_scores_by_question_category(category)
    return scores


@router.get("/matrix/")
async def get_score_matrix(
    question_ids: Optional[List[uuid.UUID]] = Query(None, description="Filter by specific question IDs"),
    score_service: QuestionOptionScoreService = Depends(get_question_option_score_service)
):
    """Get a score matrix for questions and traveler types"""
    matrix = score_service.get_score_matrix(question_ids)
    return matrix


# ==================== PUBLIC ROUTES ====================

@router.get("/public/all", response_model=List[QuestionOptionScoreResponse])
async def get_public_question_option_scores(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    score_service: QuestionOptionScoreService = Depends(get_question_option_score_service)
):
    """Get all active question option scores (public endpoint)"""
    scores = score_service.get_active_question_option_scores(skip=skip, limit=limit)
    return [QuestionOptionScoreResponse.model_validate(score) for score in scores]


@router.get("/public/option/{question_option_id}", response_model=List[QuestionOptionScoreResponse])
async def get_public_scores_by_question_option(
    question_option_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    score_service: QuestionOptionScoreService = Depends(get_question_option_score_service)
):
    """Get all scores for a specific question option (public endpoint)"""
    scores = score_service.get_scores_by_question_option(question_option_id, skip=skip, limit=limit)
    return [QuestionOptionScoreResponse.model_validate(score) for score in scores]


@router.get("/public/traveler-type/{traveler_type_id}", response_model=List[QuestionOptionScoreResponse])
async def get_public_scores_by_traveler_type(
    traveler_type_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    score_service: QuestionOptionScoreService = Depends(get_question_option_score_service)
):
    """Get all scores for a specific traveler type (public endpoint)"""
    scores = score_service.get_scores_by_traveler_type(traveler_type_id, skip=skip, limit=limit)
    return [QuestionOptionScoreResponse.model_validate(score) for score in scores]


@router.get("/public/question/{question_id}")
async def get_public_scores_by_question(
    question_id: uuid.UUID,
    score_service: QuestionOptionScoreService = Depends(get_question_option_score_service)
):
    """Get all scores for a specific question (public endpoint)"""
    scores = score_service.get_scores_by_question(question_id)
    return scores


@router.get("/public/category/{category}")
async def get_public_scores_by_question_category(
    category: str,
    score_service: QuestionOptionScoreService = Depends(get_question_option_score_service)
):
    """Get all scores for questions in a specific category (public endpoint)"""
    scores = score_service.get_scores_by_question_category(category)
    return scores
