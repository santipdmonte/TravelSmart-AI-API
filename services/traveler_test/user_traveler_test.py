from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import Depends, HTTPException
from models.traveler_test.user_traveler_test import UserTravelerTest
from schemas.traveler_test.user_traveler_test import (
    UserTravelerTestCreate, 
    UserTravelerTestUpdate, 
    UserTravelerTestComplete,
    UserTravelerTestStats
)
from dependencies import get_db
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from models.traveler_test.traveler_type import TravelerType
from models.traveler_test.user_answers import UserAnswer
from models.traveler_test.question_option_score import QuestionOptionScore
from models.user import User
from services.traveler_test.user_answers import UserAnswerService
from schemas.traveler_test import TestHistoryDetailResponse, UserAnswerHistoryResponse

class UserTravelerTestService:
    """Service class for UserTravelerTest CRUD operations and business logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== CRUD OPERATIONS ====================
    
    def create_user_traveler_test(self, test_data: UserTravelerTestCreate) -> UserTravelerTest:
        """Create a new user traveler test"""
        # Check if user already has an active test
        existing_test = self.get_active_test_by_user(test_data.user_id)
        if existing_test:
            raise ValueError("User already has an active test session")
        
        # Create test data
        test_dict = test_data.dict()
        if not test_dict.get('started_at'):
            test_dict['started_at'] = datetime.now()
        
        # Create test
        db_test = UserTravelerTest(**test_dict)
        self.db.add(db_test)
        self.db.commit()
        self.db.refresh(db_test)
        
        return db_test
    
    def get_user_traveler_test_by_id(self, test_id: uuid.UUID) -> Optional[UserTravelerTest]:
        """Get a user traveler test by ID"""
        return self.db.query(UserTravelerTest).filter(
            and_(
                UserTravelerTest.id == test_id,
                UserTravelerTest.deleted_at.is_(None)
            )
        ).first()
    
    def get_user_traveler_tests_by_user(self, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[UserTravelerTest]:
        """Get all traveler tests for a specific user"""
        return self.db.query(UserTravelerTest).filter(
            and_(
                UserTravelerTest.user_id == user_id,
                UserTravelerTest.deleted_at.is_(None)
            )
        ).order_by(UserTravelerTest.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_active_test_by_user(self, user_id: uuid.UUID) -> Optional[UserTravelerTest]:
        """Get the active (incomplete) test for a user"""
        return self.db.query(UserTravelerTest).filter(
            and_(
                UserTravelerTest.user_id == user_id,
                UserTravelerTest.completed_at.is_(None),
                UserTravelerTest.deleted_at.is_(None)
            )
        ).first()
    
    def get_completed_tests_by_user(self, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[UserTravelerTest]:
        """Get completed traveler tests for a specific user"""
        return self.db.query(UserTravelerTest).filter(
            and_(
                UserTravelerTest.user_id == user_id,
                UserTravelerTest.completed_at.is_not(None),
                UserTravelerTest.deleted_at.is_(None)
            )
        ).order_by(UserTravelerTest.completed_at.desc()).offset(skip).limit(limit).all()
    
    def get_all_user_traveler_tests(self, skip: int = 0, limit: int = 100) -> List[UserTravelerTest]:
        """Get all user traveler tests (admin function)"""
        return self.db.query(UserTravelerTest).filter(
            UserTravelerTest.deleted_at.is_(None)
        ).order_by(UserTravelerTest.created_at.desc()).offset(skip).limit(limit).all()
    
    def update_user_traveler_test(self, test_id: uuid.UUID, test_data: UserTravelerTestUpdate) -> Optional[UserTravelerTest]:
        """Update a user traveler test"""
        test = self.get_user_traveler_test_by_id(test_id)
        if not test:
            return None
        
        # Update fields
        update_data = test_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(test, field, value)
        
        self.db.commit()
        self.db.refresh(test)
        return test
    
    def complete_user_traveler_test(self, test_id: uuid.UUID) -> Optional[UserTravelerTest]:
        """Complete a user traveler test"""
        test = self.get_user_traveler_test_by_id(test_id)
        if not test:
            return None
        
        if test.completed_at:
            raise ValueError("Test is already completed")
        
        test.completed_at = datetime.now()

        # Calculate the traveler type for the test
        traveler_type_id = self.get_user_traveler_type_by_scores(test_id)
        if traveler_type_id:
            test.traveler_type_id = traveler_type_id
            # Also update the user's current traveler profile
            user = self.db.query(User).filter(User.id == test.user_id).first()
            if user:
                user.traveler_type_id = traveler_type_id
        
        self.db.commit()
        self.db.refresh(test)
        if traveler_type_id and 'user' in locals() and user:
            self.db.refresh(user)
        return test
    
    def soft_delete_user_traveler_test(self, test_id: uuid.UUID) -> bool:
        """Soft delete a user traveler test"""
        test = self.get_user_traveler_test_by_id(test_id)
        if not test:
            return False
        
        test.deleted_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def restore_user_traveler_test(self, test_id: uuid.UUID) -> Optional[UserTravelerTest]:
        """Restore a soft-deleted user traveler test"""
        test = self.db.query(UserTravelerTest).filter(
            and_(
                UserTravelerTest.id == test_id,
                UserTravelerTest.deleted_at.is_not(None)
            )
        ).first()
        
        if not test:
            return None
        
        test.deleted_at = None
        self.db.commit()
        self.db.refresh(test)
        return test
    
    # ==================== BUSINESS LOGIC METHODS ====================

    def get_test_scores(self, user_traveler_test_id: uuid.UUID):
        """Calculate the scores for a user traveler test"""
        test = self.get_user_traveler_test_by_id(user_traveler_test_id)
        if not test:
            return None

        # Get all answers for the test
        answers = self.db.query(UserAnswer).filter(
            and_(
                UserAnswer.user_traveler_test_id == user_traveler_test_id,
                UserAnswer.deleted_at.is_(None),
            )
        ).all()

        if not answers:
            return {}

        # Get all question options scores for the test
        question_option_scores = self.db.query(
            QuestionOptionScore.traveler_type_id,
            QuestionOptionScore.score
        ).filter(
            and_(
                QuestionOptionScore.question_option_id.in_([answer.question_option_id for answer in answers]),
                QuestionOptionScore.deleted_at.is_(None),
            )
        ).all()

        # Group scores by traveler type ID and sum them
        scores = {}
        for score_record in question_option_scores:
            traveler_type_id = score_record.traveler_type_id
            score_value = score_record.score
            
            if traveler_type_id not in scores:
                scores[traveler_type_id] = 0
            
            scores[traveler_type_id] += score_value

        return scores
    
    def get_user_traveler_type_by_scores(self, user_traveler_test_id: uuid.UUID):
        """Get the traveler type ID with the highest score for a user test"""
        scores = self.get_test_scores(user_traveler_test_id)
        
        if not scores:
            return None
        
        # Find the traveler type IDs with the maximum score
        max_score = max(scores.values())
        tied_ids = [tt_id for tt_id, sc in scores.items() if sc == max_score]

        if not tied_ids:
            return None

        if len(tied_ids) == 1:
            return tied_ids[0]

        # Deterministic tiebreaker: choose the TravelerType with the oldest created_at
        # Filter out soft-deleted types for safety
        try:
            q = (
                self.db.query(TravelerType)
                .filter(TravelerType.id.in_(tied_ids), TravelerType.deleted_at.is_(None))
            )
            candidates: list[TravelerType] = q.all()
            if not candidates:
                # Fallback: if none found (shouldn't happen), return a stable choice by UUID string
                return sorted([str(x) for x in tied_ids])[0]

            # Choose the one with the smallest created_at (oldest). If any created_at is None, treat as newest.
            def sort_key(tt: TravelerType):
                return (
                    tt.created_at or datetime.max,
                    str(tt.id),  # stable fallback for identical timestamps
                )

            winner = sorted(candidates, key=sort_key)[0]
            return winner.id
        except Exception:
            # Robust fallback: stable deterministic selection by UUID string
            return uuid.UUID(sorted([str(x) for x in tied_ids])[0])
    
    def get_test_stats(self, test_id: uuid.UUID) -> Optional[UserTravelerTestStats]:
        """Get statistics for a specific test"""
        test = self.get_user_traveler_test_by_id(test_id)
        if not test:
            return None
        
        # Get total questions (this would need to be implemented based on your question model)
        total_questions = self._get_total_questions()
        
        # Get answered questions
        answered_questions = len(test.user_answers) if test.user_answers else 0
        
        # Calculate completion percentage
        completion_percentage = (answered_questions / total_questions * 100) if total_questions > 0 else 0
        
        # Estimate time remaining (assuming 2 minutes per question)
        estimated_time_remaining = None
        if not test.completed_at:
            remaining_questions = total_questions - answered_questions
            estimated_time_remaining = remaining_questions * 2  # 2 minutes per question
        
        return UserTravelerTestStats(
            total_questions=total_questions,
            answered_questions=answered_questions,
            completion_percentage=completion_percentage,
            estimated_time_remaining=estimated_time_remaining
        )
    
    def get_user_test_history(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """Get comprehensive test history for a user"""
        all_tests = self.get_user_traveler_tests_by_user(user_id, skip=0, limit=1000)
        
        completed_tests = [test for test in all_tests if test.completed_at]
        active_tests = [test for test in all_tests if not test.completed_at]
        
        # Calculate statistics
        total_tests = len(all_tests)
        completed_count = len(completed_tests)
        active_count = len(active_tests)
        
        # Average completion time
        avg_completion_time = None
        if completed_tests:
            total_time = sum(test.duration_minutes or 0 for test in completed_tests)
            avg_completion_time = total_time / completed_count
        
        # Most recent test
        latest_test = all_tests[0] if all_tests else None
        
        return {
            "total_tests": total_tests,
            "completed_tests": completed_count,
            "active_tests": active_count,
            "completion_rate": (completed_count / total_tests * 100) if total_tests > 0 else 0,
            "average_completion_time_minutes": avg_completion_time,
            "latest_test": latest_test,
            "tests": all_tests
        }
    
    def get_test_analytics(self) -> Dict[str, Any]:
        """Get analytics for all tests (admin function)"""
        total_tests = self.db.query(UserTravelerTest).filter(
            UserTravelerTest.deleted_at.is_(None)
        ).count()
        
        completed_tests = self.db.query(UserTravelerTest).filter(
            and_(
                UserTravelerTest.completed_at.is_not(None),
                UserTravelerTest.deleted_at.is_(None)
            )
        ).count()
        
        active_tests = self.db.query(UserTravelerTest).filter(
            and_(
                UserTravelerTest.completed_at.is_(None),
                UserTravelerTest.deleted_at.is_(None)
            )
        ).count()
        
        # Tests created today
        today = datetime.utcnow().date()
        today_tests = self.db.query(UserTravelerTest).filter(
            and_(
                func.date(UserTravelerTest.created_at) == today,
                UserTravelerTest.deleted_at.is_(None)
            )
        ).count()
        
        return {
            "total_tests": total_tests,
            "completed_tests": completed_tests,
            "active_tests": active_tests,
            "completion_rate": (completed_tests / total_tests * 100) if total_tests > 0 else 0,
            "tests_created_today": today_tests
        }
    
    # ==================== HELPER METHODS ====================
    
    def _get_total_questions(self) -> int:
        """Get total number of questions in the test"""
        # This should be implemented based on your question model
        # For now, returning a default value
        try:
            from models.traveler_test.question import Question
            return self.db.query(Question).filter(
                Question.deleted_at.is_(None)
            ).count()
        except ImportError:
            # Fallback if Question model is not available
            return 10  # Default number of questions

    # ==================== ADMIN HISTORY DETAILS ====================
    def get_test_history_details(self, test_id: uuid.UUID) -> Optional[TestHistoryDetailResponse]:
        """Return detailed test history with question/option texts for a given test (admin use)."""
        test = self.get_user_traveler_test_by_id(test_id)
        if not test:
            return None

        # Pull answers with joins to retrieve texts
        from models.traveler_test.user_answers import UserAnswer
        from models.traveler_test.question_option import QuestionOption
        from models.traveler_test.question import Question

        q = (
            self.db.query(
                UserAnswer.id,
                UserAnswer.created_at,
                Question.id.label("question_id"),
                Question.question.label("question_text"),
                QuestionOption.id.label("option_id"),
                QuestionOption.option.label("option_text"),
            )
            .join(QuestionOption, UserAnswer.question_option_id == QuestionOption.id)
            .join(Question, QuestionOption.question_id == Question.id)
            .filter(
                and_(
                    UserAnswer.user_traveler_test_id == test_id,
                    UserAnswer.deleted_at.is_(None),
                    Question.deleted_at.is_(None),
                    QuestionOption.deleted_at.is_(None),
                )
            )
            .order_by(UserAnswer.created_at.asc())
        )

        entries: list[UserAnswerHistoryResponse] = []
        for row in q.all():
            entries.append(
                UserAnswerHistoryResponse(
                    question_id=row.question_id,
                    question_text=row.question_text,
                    selected_option_id=row.option_id,
                    selected_option_text=row.option_text,
                    created_at=row.created_at.isoformat() if row.created_at else None,
                )
            )

        traveler_type_name: Optional[str] = None
        if test.traveler_type_id:
            tt = self.db.query(TravelerType).filter(TravelerType.id == test.traveler_type_id).first()
            traveler_type_name = tt.name if tt else None

        return TestHistoryDetailResponse(
            test_id=test.id,
            user_id=test.user_id,
            completed_at=test.completed_at.isoformat() if test.completed_at else None,
            traveler_type_id=test.traveler_type_id,
            traveler_type_name=traveler_type_name,
            answers=entries,
        )

    # ==================== SUBMIT + COMPLETE ====================
    def submit_and_complete_test(self, test_id: uuid.UUID, answers: dict[uuid.UUID, uuid.UUID]):
        """Persist the provided answers and complete the test in one transaction.

        Returns a tuple: (completed_test: UserTravelerTest, traveler_type: Optional[TravelerType], scores: dict[str, float])
        """
        # 1) Persist answers (soft-delete previous ones, insert new)
        answer_service = UserAnswerService(self.db)
        answer_service.bulk_create_user_answers(test_id, answers)

        # 2) Complete the test (sets completed_at, computes traveler_type_id, updates User)
        completed_test = self.complete_user_traveler_test(test_id)
        if not completed_test:
            raise ValueError("Traveler test not found or could not be completed")

        # 3) Compute final scores and resolve traveler type entity
        raw_scores = self.get_test_scores(test_id) or {}
        scores: dict[str, float] = {str(k): float(v) for k, v in raw_scores.items()}

        tt: TravelerType | None = None
        if completed_test.traveler_type_id:
            try:
                tt = self.db.get(TravelerType, completed_test.traveler_type_id)  # type: ignore[attr-defined]
            except Exception:
                tt = self.db.query(TravelerType).get(completed_test.traveler_type_id)  # type: ignore[attr-defined]

        return completed_test, tt, scores


def get_user_traveler_test_service(db: Session = Depends(get_db)) -> UserTravelerTestService:
    """Dependency to get UserTravelerTestService instance"""
    return UserTravelerTestService(db)
