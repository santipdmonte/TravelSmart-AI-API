from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from uuid import UUID as UUID_TYPE

from models.accommodations import Accommodations
from schemas.accommodations import AccommodationCreate, AccommodationUpdate


class AccommodationsService:
    """CRUD services for accommodations links"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, data: AccommodationCreate) -> Accommodations:
        new_record = Accommodations(
            itinerary_id=data.itinerary_id,
            city=data.city,
            url=str(data.url),
        )
        self.db.add(new_record)
        self.db.commit()
        self.db.refresh(new_record)
        return new_record

    def get_by_id(self, accommodation_id: UUID_TYPE) -> Optional[Accommodations]:
        return self.db.query(Accommodations).filter(Accommodations.id == accommodation_id).first()

    def list_by_itinerary_and_city(self, itinerary_id: UUID_TYPE, city: str, skip: int = 0, limit: int = 100) -> List[Accommodations]:
        return (
            self.db.query(Accommodations)
            .filter(and_(Accommodations.itinerary_id == itinerary_id, Accommodations.city == city))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_by_itinerary(self, itinerary_id: UUID_TYPE, skip: int = 0, limit: int = 100) -> List[Accommodations]:
        return (
            self.db.query(Accommodations)
            .filter(and_(Accommodations.itinerary_id == itinerary_id))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update(self, accommodation_id: UUID_TYPE, data: AccommodationUpdate) -> Optional[Accommodations]:
        record = self.get_by_id(accommodation_id)
        if not record:
            return None
        update_data = data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "img_urls" and value is not None:
                value = [str(u) for u in value]
            setattr(record, field, value)
        self.db.commit()
        self.db.refresh(record)
        return record

    def soft_delete(self, accommodation_id: UUID_TYPE) -> Optional[Accommodations]:
        record = self.get_by_id(accommodation_id)
        if not record:
            return None
        record.status = "deleted"
        self.db.commit()
        self.db.refresh(record)
        return record

    def hard_delete(self, accommodation_id: UUID_TYPE) -> bool:
        record = self.get_by_id(accommodation_id)
        if not record:
            return False
        self.db.delete(record)
        self.db.commit()
        return True


def get_accommodations_service(db: Session) -> AccommodationsService:
    return AccommodationsService(db)


