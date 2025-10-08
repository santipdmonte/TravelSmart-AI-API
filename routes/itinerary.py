from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from database import get_db
from services.itinerary import ItineraryService, get_itinerary_service
from schemas.itinerary import (
    ItineraryCreate, 
    ItineraryUpdate, 
    ItineraryResponse, 
    ItineraryList,
    ItineraryGenerate
)
from dependencies import get_current_user_optional
from utils.session import get_session_id_from_request
from models.user import User
from fastapi.responses import StreamingResponse

itinerary_router = APIRouter(prefix="/api/itineraries", tags=["itineraries"])


@itinerary_router.post("/", response_model=ItineraryResponse, status_code=201)
def create_itinerary(
    itinerary_data: ItineraryCreate,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Create a new itinerary"""
    service = get_itinerary_service(db)
    
    # Get session_id only if user is not authenticated
    session_id = None if current_user else get_session_id_from_request(request)
    
    try:
        return service.create_itinerary(itinerary_data, current_user, session_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating itinerary: {str(e)}")


@itinerary_router.post("/generate", response_model=ItineraryResponse)
def generate_itinerary(
    itinerary_data: ItineraryGenerate,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Generate an itinerary"""
    service = get_itinerary_service(db)
    
    # Get session_id only if user is not authenticated
    session_id = None if current_user else get_session_id_from_request(request)
    
    return service.generate_itinerary(itinerary_data, current_user, session_id)


@itinerary_router.get("/{itinerary_id}", response_model=ItineraryResponse)
def get_itinerary(
    itinerary_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get a specific itinerary by UUID"""
    service = get_itinerary_service(db)
    itinerary = service.get_itinerary_by_id(itinerary_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    return itinerary


@itinerary_router.get("/slug/{slug}", response_model=ItineraryResponse)
def get_itinerary_by_slug(
    slug: str,
    db: Session = Depends(get_db)
):
    """Get a specific itinerary by slug"""
    service = get_itinerary_service(db)
    itinerary = service.get_itinerary_by_slug(slug)
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    return itinerary


@itinerary_router.get("/", response_model=List[ItineraryList])
def get_itineraries(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """Get itineraries for current user or session"""
    service = get_itinerary_service(db)
    
    if current_user:
        return service.get_itineraries_by_user(str(current_user.id), skip, limit)
    else:
        session_id = get_session_id_from_request(request)
        return service.get_itineraries_by_session(session_id, skip, limit)


@itinerary_router.get("/public/list", response_model=List[ItineraryList])
def get_public_itineraries(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """Get all public itineraries"""
    service = get_itinerary_service(db)
    return service.get_public_itineraries(skip, limit)


@itinerary_router.get("/search/", response_model=List[ItineraryList])
def search_itineraries(
    q: str = Query(..., min_length=2, description="Search query for trip name or destination"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """Search public itineraries by trip name or destination"""
    service = get_itinerary_service(db)
    return service.search_itineraries(q, skip, limit)


@itinerary_router.put("/{itinerary_id}", response_model=ItineraryResponse)
def update_itinerary(
    itinerary_id: uuid.UUID,
    itinerary_data: ItineraryUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing itinerary"""
    service = get_itinerary_service(db)
    updated_itinerary = service.update_itinerary(itinerary_id, itinerary_data)
    if not updated_itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    return updated_itinerary


@itinerary_router.delete("/{itinerary_id}", status_code=204)
def soft_delete_itinerary(
    itinerary_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Soft delete an itinerary"""
    service = get_itinerary_service(db)
    success = service.soft_delete_itinerary(itinerary_id)
    if not success:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    return {"message": "Itinerary deleted successfully"}


@itinerary_router.delete("/{itinerary_id}/permanent", status_code=204)
def hard_delete_itinerary(
    itinerary_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Permanently delete an itinerary"""
    service = get_itinerary_service(db)
    success = service.hard_delete_itinerary(itinerary_id)
    if not success:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    return {"message": "Itinerary permanently deleted"}


@itinerary_router.post("/{itinerary_id}/restore", response_model=ItineraryResponse)
def restore_itinerary(
    itinerary_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Restore a soft-deleted itinerary"""
    service = get_itinerary_service(db)
    restored_itinerary = service.restore_itinerary(itinerary_id)
    if not restored_itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found or not deleted")
    return restored_itinerary


@itinerary_router.get("/stats/summary")
def get_itinerary_stats(
    user_id: Optional[str] = Query(None, description="Get stats for specific Auth0 user"),
    session_id: Optional[uuid.UUID] = Query(None, description="Get stats for specific session UUID"),
    db: Session = Depends(get_db)
):
    """Get itinerary statistics for a user or session"""
    if not user_id and not session_id:
        raise HTTPException(status_code=400, detail="Either user_id or session_id must be provided")
    
    service = get_itinerary_service(db)
    stats = service.get_itinerary_stats(user_id, session_id)
    
    if "error" in stats:
        raise HTTPException(status_code=400, detail=stats["error"])
    
    return stats


@itinerary_router.get("/user/{user_id}", response_model=List[ItineraryList])
def get_user_itineraries(
    user_id: str,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """Get all itineraries for a specific Auth0 user"""
    service = get_itinerary_service(db)
    return service.get_itineraries_by_user(user_id, skip, limit)

@itinerary_router.get("/{itinerary_id}/accommodations/links")
def get_accommodations_links(
    itinerary_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get the accommodations links for an itinerary"""
    service = get_itinerary_service(db)
    return service.get_accommodations_links(itinerary_id)

@itinerary_router.get("/session/{session_id}", response_model=List[ItineraryList])
def get_session_itineraries(
    session_id: uuid.UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """Get all itineraries for a specific session UUID"""
    service = get_itinerary_service(db)
    return service.get_itineraries_by_session(session_id, skip, limit)


@itinerary_router.post("/{itinerary_id}/agent/{thread_id}/messages")
def send_message_to_itinerary_agent(
    itinerary_id: uuid.UUID,
    thread_id: str,
    message: str,
    db: Session = Depends(get_db)
):
    """Send a message to an itinerary agent"""

    service = get_itinerary_service(db)

    result = service.send_agent_message(itinerary_id, thread_id, message)
    if not result:
        raise HTTPException(status_code=404, detail="Agent thread not found or invalid")
    return result


@itinerary_router.get("/{itinerary_id}/agent/{thread_id}/messages/stream")
def send_message_to_itinerary_agent_stream(
    itinerary_id: uuid.UUID,
    thread_id: str,
    message: str,
    db: Session = Depends(get_db)
):
    """Send a message to an itinerary agent and stream the response"""

    service = get_itinerary_service(db)

    return StreamingResponse(service.send_agent_message_stream(itinerary_id, thread_id, message), media_type="text/event-stream")   


@itinerary_router.get("/agent/{thread_id}")
def get_agent_state(
    thread_id: str,
    itinerary_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get the state of an itinerary agent"""
    service = get_itinerary_service(db)
    status = service.get_itinerary_by_id(itinerary_id).status
    if status == "confirmed":
        agent_str = "activities_chat_agent"
    else:
        agent_str = "itinerary_agent"
    agent_state = service.get_agent_state(thread_id, agent_str)
    if not agent_state:
        raise HTTPException(status_code=404, detail="Agent thread not found or invalid")
    return agent_state


from graphs.route import generate_route as generate_route_ai
from states.route import RouteStateInput

@itinerary_router.post("/route")
def generate_route(
    itinerary_data: RouteStateInput,
    # request: Request,
    # current_user: Optional[User] = Depends(get_current_user_optional),
    # db: Session = Depends(get_db)
):
    """Generate a route for an itinerary"""
    state = generate_route_ai(itinerary_data)

    return state


@itinerary_router.post("/{itinerary_id}/route_confirmed")
def confirm_route(
    itinerary_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Generate activities for a city"""
    itinerary_service = get_itinerary_service(db)
    itinerary = itinerary_service.itinerary_route_confirmed(itinerary_id)
    if not itinerary:
        print(f"\n\nItinerary not found\n\n")
        raise HTTPException(status_code=404, detail="Itinerary not found")
    return itinerary