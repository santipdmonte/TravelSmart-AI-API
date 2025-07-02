from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from models.itinerary import Itinerary
from models.user import User
from schemas.itinerary import ItineraryCreate, ItineraryUpdate, ItineraryGenerate
from typing import List, Optional
from datetime import datetime
import uuid
from graphs.itinerary_graph import itinerary_graph
from graphs.itinerary_agent import itinerary_agent
from utils.utils import state_to_dict, detect_hil_mode
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

class ItineraryService:
    """Service class for itinerary CRUD operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_itinerary(self, itinerary_data: ItineraryCreate, user: Optional[User] = None, session_id: Optional[uuid.UUID] = None) -> Itinerary:
        """Create a new itinerary with automatic user/session assignment"""
        itinerary_dict = itinerary_data.dict()
        
        # Set user_id if user is authenticated, otherwise use session_id
        if user:
            itinerary_dict['user_id'] = str(user.id)  # Convert UUID to string for Auth0 compatibility
            itinerary_dict['session_id'] = None  # Clear session_id for authenticated users
        else:
            itinerary_dict['user_id'] = None
            itinerary_dict['session_id'] = session_id or uuid.uuid4()
        
        db_itinerary = Itinerary(**itinerary_dict)
        self.db.add(db_itinerary)
        self.db.commit()
        self.db.refresh(db_itinerary)
        
        # Update user trip count if authenticated
        if user:
            user.total_trips_created += 1
            self.db.commit()
        
        return db_itinerary

    def generate_itinerary(self, itinerary_data: ItineraryGenerate, user: Optional[User] = None, session_id: Optional[uuid.UUID] = None) -> Itinerary:
        """Generate an itinerary with automatic user/session assignment"""

        state = itinerary_graph.invoke(itinerary_data)
        details_itinerary = state_to_dict(state)

        # Set user_id if user is authenticated, otherwise use session_id
        if user:
            user_id = str(user.id)
            session_id_to_use = None
        else:
            user_id = None
            session_id_to_use = session_id or uuid.uuid4()

        db_itinerary = Itinerary(
            trip_name=itinerary_data.trip_name,
            duration_days=itinerary_data.duration_days,
            details_itinerary=details_itinerary,
            user_id=user_id,
            session_id=session_id_to_use
        )

        self.db.add(db_itinerary)
        self.db.commit()
        self.db.refresh(db_itinerary)
        
        # Update user trip count if authenticated
        if user:
            user.total_trips_created += 1
            self.db.commit()
        
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

    
    def initilize_agent(self, itinerary: Itinerary, thread_id: str):

        config: RunnableConfig = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        initial_state = {
            "itinerary": itinerary.details_itinerary,
            "user_name": "Juan",
            "user_id": "user_123",
        }

        itinerary_agent.invoke(initial_state, config=config)

        raw_state = itinerary_agent.get_state(config)
        state_dict = state_to_dict(raw_state)

        return state_dict     


    def send_agent_message(self, itinerary_id: uuid.UUID, thread_id: str, message: str):
        config: RunnableConfig = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        # TODO: Validate if the thread_id is valid

        is_hil_mode, hil_message, state_values = detect_hil_mode(itinerary_agent, config)

        if is_hil_mode:
            itinerary_agent.invoke(Command(resume={"messages": message}), config=config)

            itinerary = self.get_itinerary_by_id(itinerary_id)

            agent_state = self.get_agent_state(thread_id)

            itinerary_update = ItineraryUpdate(
                details_itinerary=agent_state[0]["itinerary"],
                trip_name=agent_state[0]["itinerary"]["nombre_viaje"],
                duration_days=agent_state[0]["itinerary"]["cantidad_dias"],
                slug=itinerary.slug,
                destination=itinerary.destination,
                start_date=itinerary.start_date,
                travelers_count=itinerary.travelers_count,
                budget=itinerary.budget,
                trip_type=itinerary.trip_type,
                tags=itinerary.tags,
                notes=itinerary.notes,
                visibility=itinerary.visibility,
                status=itinerary.status,
            )

            self.update_itinerary(itinerary_id, itinerary_update)

            return agent_state
  
        itinerary_agent.invoke({"messages": message}, config=config)

        return self.get_agent_state(thread_id)


    def get_agent_state(self, thread_id: str):
        config: RunnableConfig = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        raw_state = itinerary_agent.get_state(config)
        # TODO: Validate if the thread_id is valid
        state_dict = state_to_dict(raw_state)

        return state_dict


# Convenience functions for dependency injection
def get_itinerary_service(db: Session) -> ItineraryService:
    """Factory function to create ItineraryService instance"""
    return ItineraryService(db)
