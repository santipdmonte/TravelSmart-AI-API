from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from database import get_db
from services.traveler_test.traveler_type import TravelerTypeService, get_traveler_type_service
from schemas.traveler_test.traveler_type import (
    TravelerTypeCreate, TravelerTypeUpdate, TravelerTypeResponse, TravelerTypeDetailResponse
)

router = APIRouter(prefix="/traveler-types", tags=["Traveler Types"])


# ==================== CRUD ROUTES ====================

@router.post("/", response_model=TravelerTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_traveler_type(
    traveler_type_data: TravelerTypeCreate,
    traveler_type_service: TravelerTypeService = Depends(get_traveler_type_service)
):
    """Create a new traveler type"""
    try:
        traveler_type = traveler_type_service.create_traveler_type(traveler_type_data)
        return TravelerTypeResponse.model_validate(traveler_type)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create traveler type: {str(e)}"
        )


@router.get("/", response_model=List[TravelerTypeResponse])
async def get_traveler_types(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search term for name or description"),
    traveler_type_service: TravelerTypeService = Depends(get_traveler_type_service)
):
    """Get all traveler types with optional search and pagination"""
    try:
        if search:
            traveler_types = traveler_type_service.search_traveler_types(search, skip, limit)
        else:
            traveler_types = traveler_type_service.get_traveler_types(skip, limit)
        
        return [TravelerTypeResponse.model_validate(tt) for tt in traveler_types]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve traveler types"
        )


@router.get("/{traveler_type_id}", response_model=TravelerTypeDetailResponse)
async def get_traveler_type(
    traveler_type_id: uuid.UUID,
    traveler_type_service: TravelerTypeService = Depends(get_traveler_type_service)
):
    """Get a specific traveler type by ID with detailed information"""
    traveler_type = traveler_type_service.get_traveler_type_by_id(traveler_type_id)
    if not traveler_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Traveler type not found"
        )
    
    return TravelerTypeDetailResponse.model_validate(traveler_type)


@router.put("/{traveler_type_id}", response_model=TravelerTypeResponse)
async def update_traveler_type(
    traveler_type_id: uuid.UUID,
    traveler_type_data: TravelerTypeUpdate,
    traveler_type_service: TravelerTypeService = Depends(get_traveler_type_service)
):
    """Update an existing traveler type"""
    try:
        traveler_type = traveler_type_service.update_traveler_type(traveler_type_id, traveler_type_data)
        if not traveler_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Traveler type not found"
            )
        
        return TravelerTypeResponse.model_validate(traveler_type)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update traveler type"
        )


@router.delete("/{traveler_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_traveler_type(
    traveler_type_id: uuid.UUID,
    traveler_type_service: TravelerTypeService = Depends(get_traveler_type_service)
):
    """Soft delete a traveler type"""
    success = traveler_type_service.soft_delete_traveler_type(traveler_type_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Traveler type not found"
        )



# ==================== UTILITY ROUTES ====================

@router.get("/name/{name}", response_model=TravelerTypeResponse)
async def get_traveler_type_by_name(
    name: str,
    traveler_type_service: TravelerTypeService = Depends(get_traveler_type_service)
):
    """Get a traveler type by name"""
    traveler_type = traveler_type_service.get_traveler_type_by_name(name)
    if not traveler_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Traveler type not found"
        )
    
    return TravelerTypeResponse.model_validate(traveler_type)


@router.post("/{traveler_type_id}/restore", response_model=TravelerTypeResponse)
async def restore_traveler_type(
    traveler_type_id: uuid.UUID,
    traveler_type_service: TravelerTypeService = Depends(get_traveler_type_service)
):
    """Restore a soft-deleted traveler type"""
    traveler_type = traveler_type_service.restore_traveler_type(traveler_type_id)
    if not traveler_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Traveler type not found or not deleted"
        )
    
    return TravelerTypeResponse.model_validate(traveler_type)


@router.get("/{traveler_type_id}/in-use")
async def check_traveler_type_in_use(
    traveler_type_id: uuid.UUID,
    traveler_type_service: TravelerTypeService = Depends(get_traveler_type_service)
):
    """Check if a traveler type is currently in use"""
    in_use = traveler_type_service.is_traveler_type_in_use(traveler_type_id)
    return {"in_use": in_use}


# ==================== STATISTICS ROUTES ====================

@router.get("/stats/overview")
async def get_traveler_type_stats(
    traveler_type_service: TravelerTypeService = Depends(get_traveler_type_service)
):
    """Get traveler type statistics"""
    try:
        stats = traveler_type_service.get_traveler_type_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )


@router.get("/with-scores/", response_model=List[TravelerTypeResponse])
async def get_traveler_types_with_scores(
    traveler_type_service: TravelerTypeService = Depends(get_traveler_type_service)
):
    """Get traveler types that have associated question option scores"""
    try:
        traveler_types = traveler_type_service.get_traveler_types_with_scores()
        return [TravelerTypeResponse.model_validate(tt) for tt in traveler_types]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve traveler types with scores"
        )
