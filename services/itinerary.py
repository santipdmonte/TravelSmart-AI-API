from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from models.itinerary import Itinerary
from schemas.itinerary import ItineraryCreate, ItineraryUpdate
from typing import List, Optional
from datetime import datetime
import uuid


class ItineraryService:
    """Service class for itinerary CRUD operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_itinerary(self, itinerary_data: ItineraryCreate) -> Itinerary:
        """Create a new itinerary"""
        db_itinerary = Itinerary(**itinerary_data.dict())
        self.db.add(db_itinerary)
        self.db.commit()
        self.db.refresh(db_itinerary)
        return db_itinerary
    
    def get_itinerary_by_id(self, itinerary_id: uuid.UUID) -> Optional[Itinerary]:
        """Get itinerary by UUID (excluding soft deleted)"""
        return self.db.query(Itinerary).filter(
            and_(
                Itinerary.itinerary_id == itinerary_id,
                Itinerary.deleted_at.is_(None)
            )
        ).first()
    
    def get_itinerary_by_slug(self, slug: str) -> Optional[Itinerary]:
        """Get itinerary by slug (excluding soft deleted)"""
        return self.db.query(Itinerary).filter(
            and_(
                Itinerary.slug == slug,
                Itinerary.deleted_at.is_(None)
            )
        ).first()
    
    def get_itineraries_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Itinerary]:
        """Get all itineraries for a specific Auth0 user"""
        return self.db.query(Itinerary).filter(
            and_(
                Itinerary.user_id == user_id,
                Itinerary.deleted_at.is_(None)
            )
        ).offset(skip).limit(limit).all()
    
    def get_itineraries_by_session(self, session_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Itinerary]:
        """Get all itineraries for a specific session UUID"""
        return self.db.query(Itinerary).filter(
            and_(
                Itinerary.session_id == session_id,
                Itinerary.deleted_at.is_(None)
            )
        ).offset(skip).limit(limit).all()
    
    def get_user_or_session_itineraries(self, user_id: Optional[str] = None, session_id: Optional[uuid.UUID] = None, 
                                      skip: int = 0, limit: int = 100) -> List[Itinerary]:
        """Get itineraries for either Auth0 user_id or session_id UUID"""
        if user_id:
            return self.get_itineraries_by_user(user_id, skip, limit)
        elif session_id:
            return self.get_itineraries_by_session(session_id, skip, limit)
        else:
            return []
    
    def get_public_itineraries(self, skip: int = 0, limit: int = 100) -> List[Itinerary]:
        """Get all public itineraries"""
        return self.db.query(Itinerary).filter(
            and_(
                Itinerary.visibility == "public",
                Itinerary.deleted_at.is_(None)
            )
        ).offset(skip).limit(limit).all()
    
    def search_itineraries(self, query: str, skip: int = 0, limit: int = 100) -> List[Itinerary]:
        """Search itineraries by trip name or destination"""
        search_filter = or_(
            Itinerary.trip_name.ilike(f"%{query}%"),
            Itinerary.destination.ilike(f"%{query}%")
        )
        return self.db.query(Itinerary).filter(
            and_(
                search_filter,
                Itinerary.visibility == "public",
                Itinerary.deleted_at.is_(None)
            )
        ).offset(skip).limit(limit).all()
    
    def update_itinerary(self, itinerary_id: uuid.UUID, itinerary_data: ItineraryUpdate) -> Optional[Itinerary]:
        """Update an existing itinerary"""
        db_itinerary = self.get_itinerary_by_id(itinerary_id)
        if not db_itinerary:
            return None
        
        update_data = itinerary_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_itinerary, field, value)
        
        self.db.commit()
        self.db.refresh(db_itinerary)
        return db_itinerary
    
    def soft_delete_itinerary(self, itinerary_id: uuid.UUID) -> bool:
        """Soft delete an itinerary"""
        db_itinerary = self.get_itinerary_by_id(itinerary_id)
        if not db_itinerary:
            return False
        
        db_itinerary.deleted_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def hard_delete_itinerary(self, itinerary_id: uuid.UUID) -> bool:
        """Permanently delete an itinerary"""
        db_itinerary = self.get_itinerary_by_id(itinerary_id)
        if not db_itinerary:
            return False
        
        self.db.delete(db_itinerary)
        self.db.commit()
        return True
    
    def restore_itinerary(self, itinerary_id: uuid.UUID) -> Optional[Itinerary]:
        """Restore a soft-deleted itinerary"""
        db_itinerary = self.db.query(Itinerary).filter(
            Itinerary.itinerary_id == itinerary_id
        ).first()
        
        if not db_itinerary or db_itinerary.deleted_at is None:
            return None
        
        db_itinerary.deleted_at = None
        self.db.commit()
        self.db.refresh(db_itinerary)
        return db_itinerary
    
    def get_itinerary_stats(self, user_id: Optional[str] = None, session_id: Optional[uuid.UUID] = None) -> dict:
        """Get statistics for Auth0 user's or session's itineraries"""
        base_query = self.db.query(Itinerary).filter(Itinerary.deleted_at.is_(None))
        
        if user_id:
            base_query = base_query.filter(Itinerary.user_id == user_id)
        elif session_id:
            base_query = base_query.filter(Itinerary.session_id == session_id)
        else:
            return {"error": "Either user_id or session_id must be provided"}
        
        total = base_query.count()
        draft = base_query.filter(Itinerary.status == "draft").count()
        confirmed = base_query.filter(Itinerary.status == "confirmed").count()
        public = base_query.filter(Itinerary.visibility == "public").count()
        private = base_query.filter(Itinerary.visibility == "private").count()
        
        return {
            "total_itineraries": total,
            "draft_itineraries": draft,
            "confirmed_itineraries": confirmed,
            "public_itineraries": public,
            "private_itineraries": private
        }


# Convenience functions for dependency injection
def get_itinerary_service(db: Session) -> ItineraryService:
    """Factory function to create ItineraryService instance"""
    return ItineraryService(db)
