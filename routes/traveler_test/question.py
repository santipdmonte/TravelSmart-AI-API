from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid

from dependencies import get_db
from services.traveler_test.question import QuestionService, get_question_service
from schemas.traveler_test.question import (
    QuestionCreate, 
    QuestionUpdate, 
    QuestionResponse, 
    QuestionDetailResponse
)
from utils.jwt_utils import get_current_active_user, get_admin_user
from models.user import User
from schemas.traveler_test import TestQuestionnaireResponse, QuestionWithOptionsResponse, QuestionOptionResponse

router = APIRouter(prefix="/questions", tags=["Questions"])

# ==================== CRUD ROUTES ====================

@router.post("/", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(
    question_data: QuestionCreate,
    admin_user: User = Depends(get_admin_user),
    question_service: QuestionService = Depends(get_question_service)
):
    """Create a new question (admin only)"""
    try:
        question = question_service.create_question(question_data)
        return QuestionResponse.model_validate(question)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create question: {str(e)}"
        )


@router.get("/{question_id}", response_model=QuestionDetailResponse)
async def get_question(
    question_id: uuid.UUID,
    question_service: QuestionService = Depends(get_question_service)
):
    """Get a specific question by ID"""
    question = question_service.get_question_by_id(question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    return QuestionDetailResponse.model_validate(question)


@router.get("/", response_model=List[QuestionResponse])
async def get_all_questions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    question_service: QuestionService = Depends(get_question_service)
):
    """Get all questions ordered by order"""
    questions = question_service.get_all_questions(skip=skip, limit=limit)
    return [QuestionResponse.model_validate(question) for question in questions]


@router.get("/category/{category}", response_model=List[QuestionResponse])
async def get_questions_by_category(
    category: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    question_service: QuestionService = Depends(get_question_service)
):
    """Get questions by category"""
    questions = question_service.get_questions_by_category(category, skip=skip, limit=limit)
    return [QuestionResponse.model_validate(question) for question in questions]


@router.get("/order/{order}", response_model=QuestionDetailResponse)
async def get_question_by_order(
    order: int,
    question_service: QuestionService = Depends(get_question_service)
):
    """Get a question by order (returns first match since order is no longer unique)"""
    question = question_service.get_question_by_order(order)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    return QuestionDetailResponse.model_validate(question)


@router.get("/order/{order}/all", response_model=List[QuestionResponse])
async def get_questions_by_order(
    order: int,
    question_service: QuestionService = Depends(get_question_service)
):
    """Get all questions by order (since order is no longer unique)"""
    questions = question_service.get_questions_by_order(order)
    return [QuestionResponse.model_validate(question) for question in questions]


@router.put("/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: uuid.UUID,
    question_data: QuestionUpdate,
    admin_user: User = Depends(get_admin_user),
    question_service: QuestionService = Depends(get_question_service)
):
    """Update a question (admin only)"""
    try:
        updated_question = question_service.update_question(question_id, question_data)
        if not updated_question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        
        return QuestionResponse.model_validate(updated_question)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{question_id}")
async def delete_question(
    question_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    question_service: QuestionService = Depends(get_question_service)
):
    """Soft delete a question (admin only)"""
    success = question_service.soft_delete_question(question_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    return {"message": "Question deleted successfully"}


@router.post("/{question_id}/restore", response_model=QuestionResponse)
async def restore_question(
    question_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    question_service: QuestionService = Depends(get_question_service)
):
    """Restore a soft-deleted question (admin only)"""
    restored_question = question_service.restore_question(question_id)
    if not restored_question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found or not deleted"
        )
    
    return QuestionResponse.model_validate(restored_question)


@router.delete("/{question_id}/permanent")
async def delete_question_permanently(
    question_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    question_service: QuestionService = Depends(get_question_service)
):
    """Permanently delete a question (admin only)"""
    success = question_service.delete_question_permanently(question_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    return {"message": "Question permanently deleted"}


# ==================== BUSINESS LOGIC ROUTES ====================

@router.post("/reorder")
async def reorder_questions(
    question_orders: List[Dict[str, Any]],
    admin_user: User = Depends(get_admin_user),
    question_service: QuestionService = Depends(get_question_service)
):
    """Reorder questions (admin only)"""
    try:
        success = question_service.reorder_questions(question_orders)
        if success:
            return {"message": "Questions reordered successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reorder questions"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/stats/overview")
async def get_question_statistics(
    admin_user: User = Depends(get_admin_user),
    question_service: QuestionService = Depends(get_question_service)
):
    """Get question statistics (admin only)"""
    stats = question_service.get_question_statistics()
    return stats


@router.get("/search/")
async def search_questions(
    q: str = Query(..., min_length=2, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    question_service: QuestionService = Depends(get_question_service)
):
    """Search questions by text"""
    questions = question_service.search_questions(q, skip=skip, limit=limit)
    return [QuestionResponse.model_validate(question) for question in questions]


@router.get("/next-order")
async def get_next_question_order(
    admin_user: User = Depends(get_admin_user),
    question_service: QuestionService = Depends(get_question_service)
):
    """Get the next available question order (admin only)"""
    next_order = question_service.get_next_question_order()
    return {"next_order": next_order}


@router.get("/validate-order/{order}")
async def validate_question_order(
    order: int,
    exclude_id: Optional[uuid.UUID] = Query(None, description="Question ID to exclude from validation"),
    question_service: QuestionService = Depends(get_question_service)
):
    """Validate if a question order is available (since order is no longer unique, this always returns True)"""
    is_available = question_service.validate_question_order(order, exclude_id)
    return {"order": order, "is_available": is_available}


# ==================== PUBLIC ROUTES ====================

@router.get("/public/all", response_model=List[QuestionResponse])
async def get_public_questions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    question_service: QuestionService = Depends(get_question_service)
):
    """Get all active questions (public endpoint)"""
    questions = question_service.get_active_questions(skip=skip, limit=limit)
    return [QuestionResponse.model_validate(question) for question in questions]


@router.get("/public/category/{category}", response_model=List[QuestionResponse])
async def get_public_questions_by_category(
    category: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    question_service: QuestionService = Depends(get_question_service)
):
    """Get questions by category (public endpoint)"""
    questions = question_service.get_questions_by_category(category, skip=skip, limit=limit)
    return [QuestionResponse.model_validate(question) for question in questions]


@router.get("/public/questionnaire", response_model=TestQuestionnaireResponse)
async def get_public_questionnaire(
    question_service: QuestionService = Depends(get_question_service),
):
    """Return all active questions with their active options for the public test UI.

    This endpoint guarantees that options whose parent question is deleted will not appear.
    """
    # Fetch active questions ordered
    questions = question_service.get_active_questions(skip=0, limit=1000)

    # Fetch options per question with parent-check via service in question_option
    from services.traveler_test.question_option import QuestionOptionService
    option_service = QuestionOptionService(question_service.db)

    q_with_opts: list[QuestionWithOptionsResponse] = []
    for q in questions:
        opts = option_service.get_question_options_by_question(q.id, skip=0, limit=1000)
        q_with_opts.append(
            QuestionWithOptionsResponse(
                **QuestionResponse.model_validate(q).model_dump(),
                question_options=[QuestionOptionResponse.model_validate(o) for o in opts],
            )
        )

    return TestQuestionnaireResponse(
        questions=q_with_opts,
        total_questions=len(q_with_opts),
        estimated_time_minutes=5,
    )
