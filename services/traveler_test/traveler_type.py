from sqlalchemy.orm import Session

from sqlalchemy import and_, or_, func
from fastapi import Depends
from models.traveler_test.traveler_type import TravelerType
from schemas.traveler_test.traveler_type import TravelerTypeCreate, TravelerTypeUpdate
from dependencies import get_db
from typing import List, Optional
from datetime import datetime
import uuid


class TravelerTypeService:
    """Service class for TravelerType CRUD operations and business logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== CRUD METHODS ====================
    
    def create_traveler_type(self, traveler_type_data: TravelerTypeCreate) -> TravelerType:
        """Create a new traveler type"""

        if self.get_traveler_type_by_name(traveler_type_data.name):
            raise ValueError("Traveler type name already exists")
        
        db_traveler_type = TravelerType(**traveler_type_data.dict())
        self.db.add(db_traveler_type)
        self.db.commit()
        self.db.refresh(db_traveler_type)
        
        return db_traveler_type
    
    def get_traveler_type_by_id(self, traveler_type_id: uuid.UUID) -> Optional[TravelerType]:
        """Get traveler type by UUID (excluding soft deleted)"""
        return self.db.query(TravelerType).filter(
            and_(
                TravelerType.id == traveler_type_id,
                TravelerType.deleted_at.is_(None)
            )
        ).first()
    
    def get_traveler_type_by_name(self, name: str) -> Optional[TravelerType]:
        """Get traveler type by name (excluding soft deleted)"""
        return self.db.query(TravelerType).filter(
            and_(
                TravelerType.name == name,
                TravelerType.deleted_at.is_(None)
            )
        ).first()
    
    def get_traveler_types(self, skip: int = 0, limit: int = 100) -> List[TravelerType]:
        """Get all traveler types with pagination (excluding soft deleted)"""
        return self.db.query(TravelerType).filter(
            TravelerType.deleted_at.is_(None)
        ).offset(skip).limit(limit).all()
    
    def search_traveler_types(self, query: str, skip: int = 0, limit: int = 100) -> List[TravelerType]:
        """Search traveler types by name or description"""
        search_filter = or_(
            TravelerType.name.ilike(f"%{query}%"),
            TravelerType.description.ilike(f"%{query}%")
        )
        return self.db.query(TravelerType).filter(
            and_(
                search_filter,
                TravelerType.deleted_at.is_(None)
            )
        ).offset(skip).limit(limit).all()
    
    def update_traveler_type(self, traveler_type_id: uuid.UUID, traveler_type_data: TravelerTypeUpdate) -> Optional[TravelerType]:
        """Update an existing traveler type"""
        traveler_type = self.get_traveler_type_by_id(traveler_type_id)
        if not traveler_type:
            return None
        
        # Check if name is being changed and is available
        if traveler_type_data.name and traveler_type_data.name != traveler_type.name:
            if self.get_traveler_type_by_name(traveler_type_data.name):
                raise ValueError("Traveler type name already exists")
        
        update_data = traveler_type_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(traveler_type, field, value)
        
        self.db.commit()
        self.db.refresh(traveler_type)
        return traveler_type
    
    def soft_delete_traveler_type(self, traveler_type_id: uuid.UUID) -> bool:
        """Soft delete a traveler type"""
        traveler_type = self.get_traveler_type_by_id(traveler_type_id)
        if not traveler_type:
            return False
        
        traveler_type.deleted_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def restore_traveler_type(self, traveler_type_id: uuid.UUID) -> Optional[TravelerType]:
        """Restore a soft-deleted traveler type"""
        traveler_type = self.db.query(TravelerType).filter(TravelerType.id == traveler_type_id).first()
        
        if not traveler_type or traveler_type.deleted_at is None:
            return None
        
        traveler_type.deleted_at = None
        self.db.commit()
        self.db.refresh(traveler_type)
        return traveler_type
    
    def hard_delete_traveler_type(self, traveler_type_id: uuid.UUID) -> bool:
        """Permanently delete a traveler type (use with caution)"""
        traveler_type = self.db.query(TravelerType).filter(TravelerType.id == traveler_type_id).first()
        if not traveler_type:
            return False
        
        self.db.delete(traveler_type)
        self.db.commit()
        return True
    
    # ==================== BUSINESS LOGIC METHODS ====================
    
    def get_traveler_types_count(self) -> int:
        """Get total count of active traveler types"""
        return self.db.query(TravelerType).filter(TravelerType.deleted_at.is_(None)).count()
    
    def get_traveler_types_with_scores(self) -> List[TravelerType]:
        """Get traveler types that have associated question option scores"""
        return self.db.query(TravelerType).filter(
            and_(
                TravelerType.deleted_at.is_(None),
                TravelerType.question_option_scores.any()
            )
        ).all()
    
    def is_traveler_type_in_use(self, traveler_type_id: uuid.UUID) -> bool:
        """Check if traveler type is being used in user tests"""
        traveler_type = self.get_traveler_type_by_id(traveler_type_id)
        if not traveler_type:
            return False
        
        return len(traveler_type.user_tests) > 0
    
    # ==================== STATISTICS METHODS ====================
    
    def get_traveler_type_stats(self) -> dict:
        """Get traveler type statistics"""
        total_types = self.get_traveler_types_count()
        types_with_scores = len(self.get_traveler_types_with_scores())
        
        # Count types created today
        today = datetime.utcnow().date()
        types_created_today = self.db.query(TravelerType).filter(
            and_(
                func.date(TravelerType.created_at) == today,
                TravelerType.deleted_at.is_(None)
            )
        ).count()
        
        return {
            "total_types": total_types,
            "types_with_scores": types_with_scores,
            "types_created_today": types_created_today
        }


# ==================== DEPENDENCY INJECTION ====================

def get_traveler_type_service(db: Session = Depends(get_db)) -> TravelerTypeService:
    """Dependency injection for TravelerTypeService"""
    return TravelerTypeService(db)
