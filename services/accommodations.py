from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from uuid import UUID as UUID_TYPE
from urllib.parse import urlparse

from models.accommodations import Accommodations
from schemas.accommodations import AccommodationCreate, AccommodationUpdate
from utils.scrapper import scrape_accommodation


class AccommodationsService:
    """CRUD services for accommodations links"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, data: AccommodationCreate) -> Accommodations:
        # Check for existing by unique key (itinerary_id, url)
        existing: Optional[Accommodations] = (
            self.db.query(Accommodations)
            .filter(
                and_(
                    Accommodations.itinerary_id == data.itinerary_id,
                    Accommodations.url == str(data.url),
                )
            )
            .first()
        )

        if existing is not None:
            if existing.status == "deleted":
                # Revive deleted entry as draft
                existing.status = "draft"
                self.db.commit()
                self.db.refresh(existing)
                return existing
            # Already present and active
            raise ValueError("This accommodation is already in the list for this itinerary")

        url_str = str(data.url)
        provider = self._detect_provider(url_str)
        new_record = Accommodations(
            itinerary_id=data.itinerary_id,
            city=data.city,
            url=url_str,
            provider=provider,
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

    def _detect_provider(self, url_str: str) -> str:
        """Return provider name based on URL host."""
        try:
            host = urlparse(url_str).netloc.lower()
        except Exception:
            return "OTHER"

        if "airbnb." in host:
            return "AIRBNB"
        if "booking." in host:
            return "BOOKING"
        if "expedia." in host:
            return "EXPEDIA"
        return "OTHER"

    def scrape_url(self, url: str):
        return scrape_accommodation(url)

def get_accommodations_service(db: Session) -> AccommodationsService:
    return AccommodationsService(db)


