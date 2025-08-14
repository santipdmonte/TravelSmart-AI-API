from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import Depends, HTTPException
from models.traveler_test.user_answers import UserAnswer
from schemas.traveler_test.user_answers import (
    UserAnswerCreate, 
    UserAnswerUpdate,
    UserAnswerBulkCreate
)
from dependencies import get_db
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


class UserAnswerService:
    """Service class for UserAnswer CRUD operations and business logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== CRUD OPERATIONS ====================
    
    def create_user_answer(self, answer_data: UserAnswerCreate) -> UserAnswer:
        """Create a new user answer"""
        # Validate that the user traveler test exists
        from models.traveler_test.user_traveler_test import UserTravelerTest
        user_test = self.db.query(UserTravelerTest).filter(
            and_(
                UserTravelerTest.id == answer_data.user_traveler_test_id,
                UserTravelerTest.deleted_at.is_(None)
            )
        ).first()
        
        if not user_test:
            raise ValueError(f"User traveler test with ID {answer_data.user_traveler_test_id} not found")
        
        # Validate that the question option exists
        from models.traveler_test.question_option import QuestionOption
        question_option = self.db.query(QuestionOption).filter(
            and_(
                QuestionOption.id == answer_data.question_option_id,
                QuestionOption.deleted_at.is_(None)
            )
        ).first()
        
        if not question_option:
            raise ValueError(f"Question option with ID {answer_data.question_option_id} not found")
        
        # Check if an active answer already exists for this combination
        existing_answer = self.get_answer_by_test_and_option(
            answer_data.user_traveler_test_id, 
            answer_data.question_option_id
        )
        if existing_answer:
            raise ValueError(f"An active answer already exists for test {answer_data.user_traveler_test_id} and question option {answer_data.question_option_id}")
        
        # Create answer
        db_answer = UserAnswer(**answer_data.dict())
        self.db.add(db_answer)
        self.db.commit()
        self.db.refresh(db_answer)
        
        return db_answer
    
    def get_user_answer_by_id(self, answer_id: uuid.UUID) -> Optional[UserAnswer]:
        """Get a user answer by ID"""
        return self.db.query(UserAnswer).filter(
            and_(
                UserAnswer.id == answer_id,
                UserAnswer.deleted_at.is_(None)
            )
        ).first()
    
    def get_answer_by_test_and_option(self, user_traveler_test_id: uuid.UUID, question_option_id: uuid.UUID) -> Optional[UserAnswer]:
        """Get an answer by user traveler test ID and question option ID"""
        return self.db.query(UserAnswer).filter(
            and_(
                UserAnswer.user_traveler_test_id == user_traveler_test_id,
                UserAnswer.question_option_id == question_option_id,
                UserAnswer.deleted_at.is_(None)
            )
        ).first()
    
    def get_answers_by_user_test(self, user_traveler_test_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[UserAnswer]:
        """Get all active answers for a specific user traveler test"""
        return self.db.query(UserAnswer).filter(
            and_(
                UserAnswer.user_traveler_test_id == user_traveler_test_id,
                UserAnswer.deleted_at.is_(None)
            )
        ).offset(skip).limit(limit).all()
    
    def get_all_answers_by_user_test(self, user_traveler_test_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[UserAnswer]:
        """Get all answers (including deleted) for a specific user traveler test"""
        return self.db.query(UserAnswer).filter(
            UserAnswer.user_traveler_test_id == user_traveler_test_id
        ).offset(skip).limit(limit).all()
    
    def get_answers_by_user(self, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[UserAnswer]:
        """Get all answers for a specific user across all tests"""
        from models.traveler_test.user_traveler_test import UserTravelerTest
        
        return self.db.query(UserAnswer).join(UserTravelerTest).filter(
            and_(
                UserTravelerTest.user_id == user_id,
                UserTravelerTest.deleted_at.is_(None),
                UserAnswer.deleted_at.is_(None)
            )
        ).offset(skip).limit(limit).all()
    
    def get_answers_by_question_option(self, question_option_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[UserAnswer]:
        """Get all answers for a specific question option"""
        return self.db.query(UserAnswer).filter(
            and_(
                UserAnswer.question_option_id == question_option_id,
                UserAnswer.deleted_at.is_(None)
            )
        ).offset(skip).limit(limit).all()
    
    def get_all_user_answers(self, skip: int = 0, limit: int = 100) -> List[UserAnswer]:
        """Get all user answers"""
        return self.db.query(UserAnswer).filter(
            UserAnswer.deleted_at.is_(None)
        ).offset(skip).limit(limit).all()
    
    def get_active_user_answers(self, skip: int = 0, limit: int = 100) -> List[UserAnswer]:
        """Get all active user answers (not deleted)"""
        return self.db.query(UserAnswer).filter(
            UserAnswer.deleted_at.is_(None)
        ).offset(skip).limit(limit).all()
    
    def update_user_answer(self, answer_id: uuid.UUID, answer_data: UserAnswerUpdate) -> Optional[UserAnswer]:
        """Update a user answer"""
        answer = self.get_user_answer_by_id(answer_id)
        if not answer:
            return None
        
        # Update fields
        update_data = answer_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(answer, field, value)
        
        self.db.commit()
        self.db.refresh(answer)
        return answer
    
    def soft_delete_user_answer(self, answer_id: uuid.UUID) -> bool:
        """Soft delete a user answer"""
        answer = self.get_user_answer_by_id(answer_id)
        if not answer:
            return False
        
        answer.deleted_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def restore_user_answer(self, answer_id: uuid.UUID) -> Optional[UserAnswer]:
        """Restore a soft-deleted user answer"""
        answer = self.db.query(UserAnswer).filter(
            and_(
                UserAnswer.id == answer_id,
                UserAnswer.deleted_at.is_not(None)
            )
        ).first()
        
        if not answer:
            return None
        
        answer.deleted_at = None
        self.db.commit()
        self.db.refresh(answer)
        return answer
    
    def delete_user_answer_permanently(self, answer_id: uuid.UUID) -> bool:
        """Permanently delete a user answer"""
        answer = self.get_user_answer_by_id(answer_id)
        if not answer:
            return False
        
        self.db.delete(answer)
        self.db.commit()
        return True
    
    def change_user_answer(self, user_traveler_test_id: uuid.UUID, question_option_id: uuid.UUID, new_question_option_id: uuid.UUID) -> UserAnswer:
        """Change a user's answer by soft deleting the old one and creating a new one"""
        # Find the existing active answer
        existing_answer = self.get_answer_by_test_and_option(user_traveler_test_id, question_option_id)
        if not existing_answer:
            raise ValueError(f"No active answer found for test {user_traveler_test_id} and question option {question_option_id}")
        
        # Validate that the new question option exists
        from models.traveler_test.question_option import QuestionOption
        new_question_option = self.db.query(QuestionOption).filter(
            and_(
                QuestionOption.id == new_question_option_id,
                QuestionOption.deleted_at.is_(None)
            )
        ).first()
        
        if not new_question_option:
            raise ValueError(f"Question option with ID {new_question_option_id} not found")
        
        # Check if the new answer already exists
        existing_new_answer = self.get_answer_by_test_and_option(user_traveler_test_id, new_question_option_id)
        if existing_new_answer:
            raise ValueError(f"An active answer already exists for the new question option {new_question_option_id}")
        
        try:
            # Soft delete the existing answer
            existing_answer.deleted_at = datetime.utcnow()
            
            # Create the new answer
            new_answer_data = UserAnswerCreate(
                user_traveler_test_id=user_traveler_test_id,
                question_option_id=new_question_option_id
            )
            new_answer = UserAnswer(**new_answer_data.dict())
            self.db.add(new_answer)
            
            self.db.commit()
            self.db.refresh(new_answer)
            
            return new_answer
            
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to change answer: {str(e)}")
    
    # ==================== BUSINESS LOGIC METHODS ====================
    def get_user_answer_statistics(self) -> Dict[str, Any]:
        """Get statistics about user answers"""
        total_answers = self.db.query(UserAnswer).filter(
            UserAnswer.deleted_at.is_(None)
        ).count()
        
        deleted_answers = self.db.query(UserAnswer).filter(
            UserAnswer.deleted_at.is_not(None)
        ).count()
        
        # Get unique users who have answered
        from models.traveler_test.user_traveler_test import UserTravelerTest
        unique_users = self.db.query(UserAnswer).join(UserTravelerTest).filter(
            and_(
                UserTravelerTest.deleted_at.is_(None),
                UserAnswer.deleted_at.is_(None)
            )
        ).distinct(UserTravelerTest.user_id).count()
        
        # Get unique tests with answers
        unique_tests = self.db.query(UserAnswer.user_traveler_test_id).filter(
            UserAnswer.deleted_at.is_(None)
        ).distinct().count()
        
        # Get unique question options answered
        unique_question_options = self.db.query(UserAnswer.question_option_id).filter(
            UserAnswer.deleted_at.is_(None)
        ).distinct().count()
        
        # Get average answers per test
        avg_answers_per_test = total_answers / unique_tests if unique_tests > 0 else 0
        
        return {
            "total_answers": total_answers,
            "deleted_answers": deleted_answers,
            "active_answers": total_answers,
            "unique_users": unique_users,
            "unique_tests": unique_tests,
            "unique_question_options": unique_question_options,
            "average_answers_per_test": round(avg_answers_per_test, 2)
        }
    
    def bulk_create_answers(self, answers_data: UserAnswerBulkCreate) -> List[UserAnswer]:
        """Create multiple user answers at once"""
        created_answers = []
        
        try:
            # Validate that the user traveler test exists
            from models.traveler_test.user_traveler_test import UserTravelerTest
            user_test = self.db.query(UserTravelerTest).filter(
                and_(
                    UserTravelerTest.id == answers_data.user_traveler_test_id,
                    UserTravelerTest.deleted_at.is_(None)
                )
            ).first()
            
            if not user_test:
                raise ValueError(f"User traveler test with ID {answers_data.user_traveler_test_id} not found")
            
            # Validate that all question options exist
            from models.traveler_test.question_option import QuestionOption
            question_options = self.db.query(QuestionOption).filter(
                and_(
                    QuestionOption.id.in_(answers_data.answers),
                    QuestionOption.deleted_at.is_(None)
                )
            ).all()
            
            if len(question_options) != len(answers_data.answers):
                raise ValueError("Some question options not found")
            
            # Check for existing active answers
            existing_answers = self.db.query(UserAnswer).filter(
                and_(
                    UserAnswer.user_traveler_test_id == answers_data.user_traveler_test_id,
                    UserAnswer.question_option_id.in_(answers_data.answers),
                    UserAnswer.deleted_at.is_(None)
                )
            ).all()
            
            if existing_answers:
                existing_option_ids = [answer.question_option_id for answer in existing_answers]
                raise ValueError(f"Active answers already exist for question options: {existing_option_ids}")
            
            # Create answers
            for question_option_id in answers_data.answers:
                answer_data = UserAnswerCreate(
                    user_traveler_test_id=answers_data.user_traveler_test_id,
                    question_option_id=question_option_id
                )
                
                db_answer = UserAnswer(**answer_data.dict())
                self.db.add(db_answer)
                created_answers.append(db_answer)
            
            self.db.commit()
            
            # Refresh all created answers
            for answer in created_answers:
                self.db.refresh(answer)
            
            return created_answers
            
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to create answers: {str(e)}")
    
    def get_user_test_progress(self, user_traveler_test_id: uuid.UUID) -> Dict[str, Any]:
        """Get progress information for a user test"""
        # Get total questions
        from models.traveler_test.question import Question
        total_questions = self.db.query(Question).filter(
            Question.deleted_at.is_(None)
        ).count()
        
        # Get answered questions
        answered_questions = self.db.query(UserAnswer).filter(
            and_(
                UserAnswer.user_traveler_test_id == user_traveler_test_id,
                UserAnswer.deleted_at.is_(None)
            )
        ).count()
        
        # Calculate completion percentage
        completion_percentage = (answered_questions / total_questions * 100) if total_questions > 0 else 0
        
        # Get test details
        from models.traveler_test.user_traveler_test import UserTravelerTest
        test = self.db.query(UserTravelerTest).filter(
            and_(
                UserTravelerTest.id == user_traveler_test_id,
                UserTravelerTest.deleted_at.is_(None)
            )
        ).first()
        
        return {
            "user_traveler_test_id": user_traveler_test_id,
            "total_questions": total_questions,
            "answered_questions": answered_questions,
            "completion_percentage": round(completion_percentage, 2),
            "is_completed": test.is_completed if test else False,
            "started_at": test.started_at if test else None,
            "completed_at": test.completed_at if test else None
        }
    
    def get_user_answers_with_details(self, user_traveler_test_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get user answers with detailed information"""
        from models.traveler_test.question_option import QuestionOption
        from models.traveler_test.question import Question
        
        answers = self.db.query(UserAnswer).join(QuestionOption).join(Question).filter(
            and_(
                UserAnswer.user_traveler_test_id == user_traveler_test_id,
                UserAnswer.deleted_at.is_(None),
                QuestionOption.deleted_at.is_(None),
                Question.deleted_at.is_(None)
            )
        ).all()
        
        result = []
        for answer in answers:
            answer_data = {
                "id": answer.id,
                "user_traveler_test_id": answer.user_traveler_test_id,
                "question_option_id": answer.question_option_id,
                "created_at": answer.created_at,
                "question": {
                    "id": answer.question_option.question.id,
                    "question": answer.question_option.question.question,
                    "category": answer.question_option.question.category,
                    "order": answer.question_option.question.order
                },
                "question_option": {
                    "id": answer.question_option.id,
                    "option": answer.question_option.option,
                    "description": answer.question_option.description
                }
            }
            result.append(answer_data)
        
        return result

    def bulk_create_user_answers(self, user_traveler_test_id: uuid.UUID, answers: Dict[uuid.UUID, uuid.UUID]) -> List[UserAnswer]:
        """Atomically replace all answers for a given test with the provided mapping.

        Args:
            user_traveler_test_id: The test session ID.
            answers: Dict mapping question_id -> question_option_id.

        Returns:
            List of created UserAnswer records.

        Behavior:
            - Validates test exists and is active (not soft-deleted).
            - Validates each provided option exists and belongs to the given question.
            - Soft-deletes any existing active answers for the test, then inserts the new set.
            - Commits the transaction upon success, otherwise rolls back.
        """
        if not answers:
            raise ValueError("Answers payload cannot be empty")

        from models.traveler_test.user_traveler_test import UserTravelerTest
        from models.traveler_test.question_option import QuestionOption
        from models.traveler_test.question import Question

        # Validate test exists
        test = self.db.query(UserTravelerTest).filter(
            and_(
                UserTravelerTest.id == user_traveler_test_id,
                UserTravelerTest.deleted_at.is_(None),
            )
        ).first()
        if not test:
            raise ValueError(f"User traveler test with ID {user_traveler_test_id} not found")

        # Collect ids
        question_ids = list(answers.keys())
        option_ids = list(answers.values())

        # Validate questions exist
        existing_questions = self.db.query(Question.id).filter(
            and_(
                Question.id.in_(question_ids),
                Question.deleted_at.is_(None),
            )
        ).all()
        if len(existing_questions) != len(question_ids):
            raise ValueError("Some questions in the submission were not found or have been deleted")

        # Fetch options and map id -> question_id
        options = self.db.query(QuestionOption.id, QuestionOption.question_id).filter(
            and_(
                QuestionOption.id.in_(option_ids),
                QuestionOption.deleted_at.is_(None),
            )
        ).all()
        if len(options) != len(option_ids):
            raise ValueError("Some question options in the submission were not found or have been deleted")

        option_to_question = {row.id: row.question_id for row in options}

        # Validate each mapping option belongs to the provided question
        for q_id, opt_id in answers.items():
            owner_q = option_to_question.get(opt_id)
            if owner_q is None or owner_q != q_id:
                raise ValueError(f"Option {opt_id} does not belong to question {q_id}")

        created: List[UserAnswer] = []
        try:
            # Soft-delete existing active answers for this test to avoid duplicates
            self.db.query(UserAnswer).filter(
                and_(
                    UserAnswer.user_traveler_test_id == user_traveler_test_id,
                    UserAnswer.deleted_at.is_(None),
                )
            ).update({UserAnswer.deleted_at: datetime.utcnow()}, synchronize_session=False)

            # Insert new answers
            for q_id, opt_id in answers.items():
                ua = UserAnswer(
                    user_traveler_test_id=user_traveler_test_id,
                    question_option_id=opt_id,
                )
                self.db.add(ua)
                created.append(ua)

            self.db.commit()
            for ua in created:
                self.db.refresh(ua)
            return created
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to persist answers: {str(e)}")


def get_user_answer_service(db: Session = Depends(get_db)) -> UserAnswerService:
    """Dependency to get UserAnswerService instance"""
    return UserAnswerService(db)
