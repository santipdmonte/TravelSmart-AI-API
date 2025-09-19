from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import Depends, HTTPException
from models.traveler_test.question import Question
from schemas.traveler_test.question import (
    QuestionCreate, 
    QuestionUpdate
)
from database import get_db
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


class QuestionService:
    """Service class for Question CRUD operations and business logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== CRUD OPERATIONS ====================

    def create_question(self, question_data: QuestionCreate) -> Question:
        """Create a new question"""
        # If no order is provided, assign the next available order
        if not question_data.order:
            question_data.order = self.get_next_question_order()

        # Create and persist the question
        db_question = Question(**question_data.dict())
        self.db.add(db_question)
        self.db.commit()
        self.db.refresh(db_question)
        return db_question
    
    def get_question_by_id(self, question_id: uuid.UUID) -> Optional[Question]:
        """Get a question by ID"""
        return self.db.query(Question).filter(
            and_(
                Question.id == question_id,
                Question.deleted_at.is_(None)
            )
        ).first()
    
    def get_question_by_order(self, order: int) -> Optional[Question]:
        """Get a question by order (returns first match since order is no longer unique)"""
        return self.db.query(Question).filter(
            and_(
                Question.order == order,
                Question.deleted_at.is_(None)
            )
        ).first()
    
    def get_questions_by_order(self, order: int) -> List[Question]:
        """Get all questions by order (since order is no longer unique)"""
        return self.db.query(Question).filter(
            and_(
                Question.order == order,
                Question.deleted_at.is_(None)
            )
        ).all()
    
    def get_all_questions(self, skip: int = 0, limit: int = 100) -> List[Question]:
        """Get all questions ordered by order"""
        return self.db.query(Question).filter(
            Question.deleted_at.is_(None)
        ).order_by(Question.order).offset(skip).limit(limit).all()
    
    def get_questions_by_category(self, category: str, skip: int = 0, limit: int = 100) -> List[Question]:
        """Get questions by category"""
        return self.db.query(Question).filter(
            and_(
                Question.category == category,
                Question.deleted_at.is_(None)
            )
        ).order_by(Question.order).offset(skip).limit(limit).all()
    
    def get_active_questions(self, skip: int = 0, limit: int = 100) -> List[Question]:
        """Get all active questions (not deleted)"""
        return self.db.query(Question).filter(
            Question.deleted_at.is_(None)
        ).order_by(Question.order).offset(skip).limit(limit).all()
    
    def update_question(self, question_id: uuid.UUID, question_data: QuestionUpdate) -> Optional[Question]:
        """Update a question"""
        question = self.get_question_by_id(question_id)
        if not question:
            return None
        
        # Update fields
        update_data = question_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(question, field, value)
        
        self.db.commit()
        self.db.refresh(question)
        return question
    
    def soft_delete_question(self, question_id: uuid.UUID) -> bool:
        """Soft delete a question"""
        question = self.get_question_by_id(question_id)
        if not question:
            return False
        
        question.deleted_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def restore_question(self, question_id: uuid.UUID) -> Optional[Question]:
        """Restore a soft-deleted question"""
        question = self.db.query(Question).filter(
            and_(
                Question.id == question_id,
                Question.deleted_at.is_not(None)
            )
        ).first()
        
        if not question:
            return None
        
        question.deleted_at = None
        self.db.commit()
        self.db.refresh(question)
        return question
    
    def delete_question_permanently(self, question_id: uuid.UUID) -> bool:
        """Permanently delete a question"""
        question = self.get_question_by_id(question_id)
        if not question:
            return False
        
        self.db.delete(question)
        self.db.commit()
        return True
    
    # ==================== BUSINESS LOGIC METHODS ====================
    
    def reorder_questions(self, question_orders: List[Dict[str, Any]]) -> bool:
        """Reorder questions based on provided order mappings"""
        try:
            for order_mapping in question_orders:
                question_id = order_mapping.get('question_id')
                new_order = order_mapping.get('order')
                
                if question_id and new_order is not None:
                    question = self.get_question_by_id(uuid.UUID(question_id))
                    if question:
                        question.order = new_order
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to reorder questions: {str(e)}")
    
    def get_question_statistics(self) -> Dict[str, Any]:
        """Get statistics about questions"""
        total_questions = self.db.query(Question).filter(
            Question.deleted_at.is_(None)
        ).count()
        
        deleted_questions = self.db.query(Question).filter(
            Question.deleted_at.is_not(None)
        ).count()
        
        # Get questions by category
        categories = self.db.query(Question.category).filter(
            and_(
                Question.category.is_not(None),
                Question.deleted_at.is_(None)
            )
        ).distinct().all()
        
        category_counts = {}
        for category in categories:
            if category[0]:  # category[0] is the category name
                count = self.db.query(Question).filter(
                    and_(
                        Question.category == category[0],
                        Question.deleted_at.is_(None)
                    )
                ).count()
                category_counts[category[0]] = count
        
        # Get questions with images
        questions_with_images = self.db.query(Question).filter(
            and_(
                Question.image_url.is_not(None),
                Question.deleted_at.is_(None)
            )
        ).count()
        
        return {
            "total_questions": total_questions,
            "deleted_questions": deleted_questions,
            "active_questions": total_questions,
            "questions_with_images": questions_with_images,
            "categories": category_counts,
            "total_categories": len(category_counts)
        }
    
    def search_questions(self, query: str, skip: int = 0, limit: int = 100) -> List[Question]:
        """Search questions by text"""
        return self.db.query(Question).filter(
            and_(
                or_(
                    Question.question.ilike(f"%{query}%"),
                    Question.category.ilike(f"%{query}%")
                ),
                Question.deleted_at.is_(None)
            )
        ).order_by(Question.order).offset(skip).limit(limit).all()
    
    def get_next_question_order(self) -> int:
        """Get the next available question order"""
        max_order = self.db.query(func.max(Question.order)).filter(
            and_(
                Question.order.is_not(None),
                Question.deleted_at.is_(None)
            )
        ).scalar()
        
        return (max_order or 0) + 1
    
    def validate_question_order(self, order: int, exclude_id: Optional[uuid.UUID] = None) -> bool:
        """Validate if a question order is available (since order is no longer unique, this always returns True)"""
        # Since order is no longer unique, any order value is valid
        return True


def get_question_service(db: Session = Depends(get_db)) -> QuestionService:
    """Dependency to get QuestionService instance"""
    return QuestionService(db)
