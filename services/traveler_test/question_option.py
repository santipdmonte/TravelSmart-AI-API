from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import Depends, HTTPException
from models.traveler_test.question_option import QuestionOption
from schemas.traveler_test.question_option import (
    QuestionOptionCreate, 
    QuestionOptionUpdate
)
from dependencies import get_db
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


class QuestionOptionService:
    """Service class for QuestionOption CRUD operations and business logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== CRUD OPERATIONS ====================
    
    def create_question_option(self, option_data: QuestionOptionCreate) -> QuestionOption:
        """Create a new question option"""
    # Validate that the question exists and is active (not soft-deleted)
        from models.traveler_test.question import Question
        question = self.db.query(Question).filter(
            and_(
                Question.id == option_data.question_id,
                Question.deleted_at.is_(None)
            )
        ).first()
        
        if not question:
            raise ValueError(f"Question with ID {option_data.question_id} not found")
        
        # Create option
        db_option = QuestionOption(**option_data.dict())
        self.db.add(db_option)
        self.db.commit()
        self.db.refresh(db_option)
        
        return db_option
    
    def get_question_option_by_id(self, option_id: uuid.UUID) -> Optional[QuestionOption]:
        """Get a question option by ID"""
        return self.db.query(QuestionOption).filter(
            and_(
                QuestionOption.id == option_id,
                QuestionOption.deleted_at.is_(None)
            )
        ).first()
    
    def get_question_options_by_question(self, question_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[QuestionOption]:
        """Get all options for a specific question"""
        # Ensure both the option and its parent question are not soft-deleted
        from models.traveler_test.question import Question
        return (
            self.db.query(QuestionOption)
            .join(Question, Question.id == QuestionOption.question_id)
            .filter(
                and_(
                    QuestionOption.question_id == question_id,
                    QuestionOption.deleted_at.is_(None),
                    Question.deleted_at.is_(None),
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_all_question_options(self, skip: int = 0, limit: int = 100) -> List[QuestionOption]:
        """Get all question options"""
        return self.db.query(QuestionOption).filter(
            QuestionOption.deleted_at.is_(None)
        ).offset(skip).limit(limit).all()
    
    def get_active_question_options(self, skip: int = 0, limit: int = 100) -> List[QuestionOption]:
        """Get all active question options (not deleted)"""
        return self.db.query(QuestionOption).filter(
            QuestionOption.deleted_at.is_(None)
        ).offset(skip).limit(limit).all()
    
    def update_question_option(self, option_id: uuid.UUID, option_data: QuestionOptionUpdate) -> Optional[QuestionOption]:
        """Update a question option"""
        option = self.get_question_option_by_id(option_id)
        if not option:
            return None
        
        # Update fields
        update_data = option_data.dict(exclude_unset=True)
        # If moving option to another question, validate new parent is active
        if 'question_id' in update_data:
            from models.traveler_test.question import Question
            new_q = self.db.query(Question).filter(
                and_(
                    Question.id == update_data['question_id'],
                    Question.deleted_at.is_(None)
                )
            ).first()
            if not new_q:
                raise ValueError(f"Target question with ID {update_data['question_id']} not found or is deleted")
        for field, value in update_data.items():
            setattr(option, field, value)
        
        self.db.commit()
        self.db.refresh(option)
        return option
    
    def soft_delete_question_option(self, option_id: uuid.UUID) -> bool:
        """Soft delete a question option"""
        option = self.get_question_option_by_id(option_id)
        if not option:
            return False
        
        option.deleted_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def restore_question_option(self, option_id: uuid.UUID) -> Optional[QuestionOption]:
        """Restore a soft-deleted question option"""
        option = self.db.query(QuestionOption).filter(
            and_(
                QuestionOption.id == option_id,
                QuestionOption.deleted_at.is_not(None)
            )
        ).first()
        
        if not option:
            return None
        
        option.deleted_at = None
        self.db.commit()
        self.db.refresh(option)
        return option
    
    def delete_question_option_permanently(self, option_id: uuid.UUID) -> bool:
        """Permanently delete a question option"""
        option = self.get_question_option_by_id(option_id)
        if not option:
            return False
        
        self.db.delete(option)
        self.db.commit()
        return True
    
    # ==================== BUSINESS LOGIC METHODS ====================
    
    def get_question_option_statistics(self) -> Dict[str, Any]:
        """Get statistics about question options"""
        total_options = self.db.query(QuestionOption).filter(
            QuestionOption.deleted_at.is_(None)
        ).count()
        
        deleted_options = self.db.query(QuestionOption).filter(
            QuestionOption.deleted_at.is_not(None)
        ).count()
        
        # Get options with images
        options_with_images = self.db.query(QuestionOption).filter(
            and_(
                QuestionOption.image_url.is_not(None),
                QuestionOption.deleted_at.is_(None)
            )
        ).count()
        
        # Get options with descriptions
        options_with_descriptions = self.db.query(QuestionOption).filter(
            and_(
                QuestionOption.description.is_not(None),
                QuestionOption.deleted_at.is_(None)
            )
        ).count()
        
        # Get average options per question
        from models.traveler_test.question import Question
        total_questions = self.db.query(Question).filter(
            Question.deleted_at.is_(None)
        ).count()
        
        avg_options_per_question = total_options / total_questions if total_questions > 0 else 0
        
        return {
            "total_options": total_options,
            "deleted_options": deleted_options,
            "active_options": total_options,
            "options_with_images": options_with_images,
            "options_with_descriptions": options_with_descriptions,
            "total_questions": total_questions,
            "average_options_per_question": round(avg_options_per_question, 2)
        }
    
    def search_question_options(self, query: str, skip: int = 0, limit: int = 100) -> List[QuestionOption]:
        """Search question options by text"""
        return self.db.query(QuestionOption).filter(
            and_(
                or_(
                    QuestionOption.option.ilike(f"%{query}%"),
                    QuestionOption.description.ilike(f"%{query}%")
                ),
                QuestionOption.deleted_at.is_(None)
            )
        ).offset(skip).limit(limit).all()
    
    def get_options_by_question_category(self, category: str, skip: int = 0, limit: int = 100) -> List[QuestionOption]:
        """Get options for questions in a specific category"""
        from models.traveler_test.question import Question
        
        return self.db.query(QuestionOption).join(Question).filter(
            and_(
                Question.category == category,
                Question.deleted_at.is_(None),
                QuestionOption.deleted_at.is_(None)
            )
        ).offset(skip).limit(limit).all()
    
    def bulk_create_options(self, options_data: List[QuestionOptionCreate]) -> List[QuestionOption]:
        """Create multiple question options at once"""
        created_options = []
        
        try:
            for option_data in options_data:
                # Validate that the question exists
                from models.traveler_test.question import Question
                question = self.db.query(Question).filter(
                    and_(
                        Question.id == option_data.question_id,
                        Question.deleted_at.is_(None)
                    )
                ).first()
                
                if not question:
                    raise ValueError(f"Question with ID {option_data.question_id} not found")
                
                # Create option
                db_option = QuestionOption(**option_data.dict())
                self.db.add(db_option)
                created_options.append(db_option)
            
            self.db.commit()
            
            # Refresh all created options
            for option in created_options:
                self.db.refresh(option)
            
            return created_options
            
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to create options: {str(e)}")
    
    def get_options_with_scores(self, question_id: Optional[uuid.UUID] = None) -> List[Dict[str, Any]]:
        """Get options with their associated scores"""
        from models.traveler_test.question import Question
        query = (
            self.db.query(QuestionOption)
            .join(Question, Question.id == QuestionOption.question_id)
            .filter(
                and_(
                    QuestionOption.deleted_at.is_(None),
                    Question.deleted_at.is_(None),
                )
            )
        )
        
        if question_id:
            query = query.filter(QuestionOption.question_id == question_id)
        
        options = query.all()
        
        result = []
        for option in options:
            option_data = {
                "id": option.id,
                "option": option.option,
                "description": option.description,
                "image_url": option.image_url,
                "question_id": option.question_id,
                "scores": []
            }
            
            # Get scores for this option
            for score in option.question_option_scores:
                if not score.deleted_at:
                    option_data["scores"].append({
                        "traveler_type_id": score.traveler_type_id,
                        "score": score.score
                    })
            
            result.append(option_data)
        
        return result


def get_question_option_service(db: Session = Depends(get_db)) -> QuestionOptionService:
    """Dependency to get QuestionOptionService instance"""
    return QuestionOptionService(db)
