from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import Depends, HTTPException
from models.traveler_test.question_option_score import QuestionOptionScore
from schemas.traveler_test.question_option_score import (
    QuestionOptionScoreCreate, 
    QuestionOptionScoreUpdate
)
from database import get_db
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


class QuestionOptionScoreService:
    """Service class for QuestionOptionScore CRUD operations and business logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== CRUD OPERATIONS ====================
    
    def create_question_option_score(self, score_data: QuestionOptionScoreCreate) -> QuestionOptionScore:
        """Create a new question option score"""
        # Validate that the question option exists
        from models.traveler_test.question_option import QuestionOption
        question_option = self.db.query(QuestionOption).filter(
            and_(
                QuestionOption.id == score_data.question_option_id,
                QuestionOption.deleted_at.is_(None)
            )
        ).first()
        
        if not question_option:
            raise ValueError(f"Question option with ID {score_data.question_option_id} not found")
        
        # Validate that the traveler type exists
        from models.traveler_test.traveler_type import TravelerType
        traveler_type = self.db.query(TravelerType).filter(
            and_(
                TravelerType.id == score_data.traveler_type_id,
                TravelerType.deleted_at.is_(None)
            )
        ).first()
        
        if not traveler_type:
            raise ValueError(f"Traveler type with ID {score_data.traveler_type_id} not found")
        
        # Check if score already exists for this combination
        existing_score = self.get_score_by_option_and_type(
            score_data.question_option_id, 
            score_data.traveler_type_id
        )
        if existing_score:
            raise ValueError(f"Score already exists for question option {score_data.question_option_id} and traveler type {score_data.traveler_type_id}")
        
        # Create score
        db_score = QuestionOptionScore(**score_data.dict())
        self.db.add(db_score)
        self.db.commit()
        self.db.refresh(db_score)
        
        return db_score
    
    def get_question_option_score_by_id(self, score_id: uuid.UUID) -> Optional[QuestionOptionScore]:
        """Get a question option score by ID"""
        return self.db.query(QuestionOptionScore).filter(
            and_(
                QuestionOptionScore.id == score_id,
                QuestionOptionScore.deleted_at.is_(None)
            )
        ).first()
    
    def get_score_by_option_and_type(self, question_option_id: uuid.UUID, traveler_type_id: uuid.UUID) -> Optional[QuestionOptionScore]:
        """Get a score by question option ID and traveler type ID"""
        return self.db.query(QuestionOptionScore).filter(
            and_(
                QuestionOptionScore.question_option_id == question_option_id,
                QuestionOptionScore.traveler_type_id == traveler_type_id,
                QuestionOptionScore.deleted_at.is_(None)
            )
        ).first()
    
    def get_scores_by_question_option(self, question_option_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[QuestionOptionScore]:
        """Get all scores for a specific question option"""
        return self.db.query(QuestionOptionScore).filter(
            and_(
                QuestionOptionScore.question_option_id == question_option_id,
                QuestionOptionScore.deleted_at.is_(None)
            )
        ).offset(skip).limit(limit).all()
    
    def get_scores_by_traveler_type(self, traveler_type_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[QuestionOptionScore]:
        """Get all scores for a specific traveler type"""
        return self.db.query(QuestionOptionScore).filter(
            and_(
                QuestionOptionScore.traveler_type_id == traveler_type_id,
                QuestionOptionScore.deleted_at.is_(None)
            )
        ).offset(skip).limit(limit).all()
    
    def get_all_question_option_scores(self, skip: int = 0, limit: int = 100) -> List[QuestionOptionScore]:
        """Get all question option scores"""
        return self.db.query(QuestionOptionScore).filter(
            QuestionOptionScore.deleted_at.is_(None)
        ).offset(skip).limit(limit).all()
    
    def get_active_question_option_scores(self, skip: int = 0, limit: int = 100) -> List[QuestionOptionScore]:
        """Get all active question option scores (not deleted)"""
        return self.db.query(QuestionOptionScore).filter(
            QuestionOptionScore.deleted_at.is_(None)
        ).offset(skip).limit(limit).all()
    
    def update_question_option_score(self, score_id: uuid.UUID, score_data: QuestionOptionScoreUpdate) -> Optional[QuestionOptionScore]:
        """Update a question option score"""
        score = self.get_question_option_score_by_id(score_id)
        if not score:
            return None
        
        # Update fields
        update_data = score_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(score, field, value)
        
        self.db.commit()
        self.db.refresh(score)
        return score
    
    def soft_delete_question_option_score(self, score_id: uuid.UUID) -> bool:
        """Soft delete a question option score"""
        score = self.get_question_option_score_by_id(score_id)
        if not score:
            return False
        
        score.deleted_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def restore_question_option_score(self, score_id: uuid.UUID) -> Optional[QuestionOptionScore]:
        """Restore a soft-deleted question option score"""
        score = self.db.query(QuestionOptionScore).filter(
            and_(
                QuestionOptionScore.id == score_id,
                QuestionOptionScore.deleted_at.is_not(None)
            )
        ).first()
        
        if not score:
            return None
        
        score.deleted_at = None
        self.db.commit()
        self.db.refresh(score)
        return score
    
    def delete_question_option_score_permanently(self, score_id: uuid.UUID) -> bool:
        """Permanently delete a question option score"""
        score = self.get_question_option_score_by_id(score_id)
        if not score:
            return False
        
        self.db.delete(score)
        self.db.commit()
        return True
    
    # ==================== BUSINESS LOGIC METHODS ====================
    
    def get_question_option_score_statistics(self) -> Dict[str, Any]:
        """Get statistics about question option scores"""
        total_scores = self.db.query(QuestionOptionScore).filter(
            QuestionOptionScore.deleted_at.is_(None)
        ).count()
        
        deleted_scores = self.db.query(QuestionOptionScore).filter(
            QuestionOptionScore.deleted_at.is_not(None)
        ).count()
        
        # Get average score
        avg_score = self.db.query(func.avg(QuestionOptionScore.score)).filter(
            QuestionOptionScore.deleted_at.is_(None)
        ).scalar()
        
        # Get score distribution
        positive_scores = self.db.query(QuestionOptionScore).filter(
            and_(
                QuestionOptionScore.score > 0,
                QuestionOptionScore.deleted_at.is_(None)
            )
        ).count()
        
        negative_scores = self.db.query(QuestionOptionScore).filter(
            and_(
                QuestionOptionScore.score < 0,
                QuestionOptionScore.deleted_at.is_(None)
            )
        ).count()
        
        neutral_scores = self.db.query(QuestionOptionScore).filter(
            and_(
                QuestionOptionScore.score == 0,
                QuestionOptionScore.deleted_at.is_(None)
            )
        ).count()
        
        # Get unique question options and traveler types
        unique_question_options = self.db.query(QuestionOptionScore.question_option_id).filter(
            QuestionOptionScore.deleted_at.is_(None)
        ).distinct().count()
        
        unique_traveler_types = self.db.query(QuestionOptionScore.traveler_type_id).filter(
            QuestionOptionScore.deleted_at.is_(None)
        ).distinct().count()
        
        return {
            "total_scores": total_scores,
            "deleted_scores": deleted_scores,
            "active_scores": total_scores,
            "average_score": round(avg_score, 2) if avg_score else 0,
            "positive_scores": positive_scores,
            "negative_scores": negative_scores,
            "neutral_scores": neutral_scores,
            "unique_question_options": unique_question_options,
            "unique_traveler_types": unique_traveler_types
        }
    
    def get_scores_by_question(self, question_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get all scores for a specific question"""
        from models.traveler_test.question_option import QuestionOption
        
        scores = self.db.query(QuestionOptionScore).join(QuestionOption).filter(
            and_(
                QuestionOption.question_id == question_id,
                QuestionOption.deleted_at.is_(None),
                QuestionOptionScore.deleted_at.is_(None)
            )
        ).all()
        
        result = []
        for score in scores:
            score_data = {
                "id": score.id,
                "question_option_id": score.question_option_id,
                "traveler_type_id": score.traveler_type_id,
                "score": score.score,
                "question_option": {
                    "id": score.question_option.id,
                    "option": score.question_option.option,
                    "description": score.question_option.description
                }
            }
            result.append(score_data)
        
        return result
    
    def get_scores_by_question_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all scores for questions in a specific category"""
        from models.traveler_test.question_option import QuestionOption
        from models.traveler_test.question import Question
        
        scores = self.db.query(QuestionOptionScore).join(QuestionOption).join(Question).filter(
            and_(
                Question.category == category,
                Question.deleted_at.is_(None),
                QuestionOption.deleted_at.is_(None),
                QuestionOptionScore.deleted_at.is_(None)
            )
        ).all()
        
        result = []
        for score in scores:
            score_data = {
                "id": score.id,
                "question_option_id": score.question_option_id,
                "traveler_type_id": score.traveler_type_id,
                "score": score.score,
                "question_option": {
                    "id": score.question_option.id,
                    "option": score.question_option.option,
                    "description": score.question_option.description
                },
                "question": {
                    "id": score.question_option.question.id,
                    "question": score.question_option.question.question,
                    "category": score.question_option.question.category
                }
            }
            result.append(score_data)
        
        return result
    
    def bulk_create_scores(self, scores_data: List[QuestionOptionScoreCreate]) -> List[QuestionOptionScore]:
        """Create multiple question option scores at once"""
        created_scores = []
        
        try:
            for score_data in scores_data:
                # Check if score already exists
                existing_score = self.get_score_by_option_and_type(
                    score_data.question_option_id, 
                    score_data.traveler_type_id
                )
                if existing_score:
                    raise ValueError(f"Score already exists for question option {score_data.question_option_id} and traveler type {score_data.traveler_type_id}")
                
                # Create score
                db_score = QuestionOptionScore(**score_data.dict())
                self.db.add(db_score)
                created_scores.append(db_score)
            
            self.db.commit()
            
            # Refresh all created scores
            for score in created_scores:
                self.db.refresh(score)
            
            return created_scores
            
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to create scores: {str(e)}")
    
    def get_score_matrix(self, question_ids: Optional[List[uuid.UUID]] = None) -> Dict[str, Any]:
        """Get a score matrix for questions and traveler types"""
        from models.traveler_test.question_option import QuestionOption
        from models.traveler_test.question import Question
        from models.traveler_test.traveler_type import TravelerType
        
        query = self.db.query(QuestionOptionScore).join(QuestionOption).join(Question).join(TravelerType).filter(
            and_(
                Question.deleted_at.is_(None),
                QuestionOption.deleted_at.is_(None),
                QuestionOptionScore.deleted_at.is_(None),
                TravelerType.deleted_at.is_(None)
            )
        )
        
        if question_ids:
            query = query.filter(Question.id.in_(question_ids))
        
        scores = query.all()
        
        # Build matrix
        matrix = {}
        for score in scores:
            question_id = str(score.question_option.question.id)
            traveler_type_id = str(score.traveler_type_id)
            option_id = str(score.question_option_id)
            
            if question_id not in matrix:
                matrix[question_id] = {
                    "question": score.question_option.question.question,
                    "category": score.question_option.question.category,
                    "options": {}
                }
            
            if option_id not in matrix[question_id]["options"]:
                matrix[question_id]["options"][option_id] = {
                    "option": score.question_option.option,
                    "description": score.question_option.description,
                    "scores": {}
                }
            
            matrix[question_id]["options"][option_id]["scores"][traveler_type_id] = score.score
        
        return matrix


def get_question_option_score_service(db: Session = Depends(get_db)) -> QuestionOptionScoreService:
    """Dependency to get QuestionOptionScoreService instance"""
    return QuestionOptionScoreService(db)
