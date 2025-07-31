from sqlalchemy.orm import Session
from schemas.transportation import TransportationCreate, TransportationUpdate, TransportationResponse
from models.transportation import Transportation
from models.itinerary import Itinerary
from uuid import UUID
from typing import List, Optional
from graphs.transportation_agent import generate_transportation_agent

class TransportationServices:
    def __init__(self, db: Session):
        self.db = db

    def create_transportation(self, transportation_data: TransportationCreate, itinerary_id: UUID) -> Transportation:
        db_transportation = Transportation(**transportation_data.model_dump())
        self.db.add(db_transportation)
        self.db.commit()
        self.db.refresh(db_transportation)
        
        # Actualizar el itinerario con el transportation_id
        if itinerary_id:
            itinerary = self.db.query(Itinerary).filter(
                Itinerary.itinerary_id == itinerary_id
            ).first()
            if itinerary:
                itinerary.transportation_id = db_transportation.id
                self.db.commit()
        
        return db_transportation
    
    def get_transportation_by_id(self, transportation_id: UUID) -> Transportation:
        return self.db.query(Transportation).filter(Transportation.id == transportation_id).first()
    
    def get_transportation_by_itinerary_id(self, itinerary_id: UUID) -> Optional[Transportation]:
        # Ahora buscamos desde el itinerary hacia el transportation
        itinerary = self.db.query(Itinerary).filter(Itinerary.itinerary_id == itinerary_id).first()
        if itinerary and itinerary.transportation_id:
            return self.db.query(Transportation).filter(Transportation.id == itinerary.transportation_id).first()
        return None
    
    def get_all_transportations(self) -> List[Transportation]:
        return self.db.query(Transportation).all()
    
    def update_transportation(self, transportation_id: UUID, transportation_data: TransportationUpdate) -> Transportation:
        db_transportation = self.get_transportation_by_id(transportation_id)
        if not db_transportation:
            return None
            
        # Actualizar el transportation
        for field, value in transportation_data.model_dump(exclude_unset=True).items():
            setattr(db_transportation, field, value)
        self.db.commit()
        self.db.refresh(db_transportation)
        
        return db_transportation

    def delete_transportation(self, transportation_id: UUID) -> bool:
        db_transportation = self.get_transportation_by_id(transportation_id)
        if not db_transportation:
            return False
        
        # Antes de eliminar, remover la referencia del itinerario
        # Buscar todos los itinerarios que referencien este transportation
        itineraries = self.db.query(Itinerary).filter(Itinerary.transportation_id == transportation_id).all()
        for itinerary in itineraries:
            itinerary.transportation_id = None
        
        # Eliminar el transportation
        self.db.delete(db_transportation)
        self.db.commit()
        return True

    def generate_transportation(self, itinerary_id: UUID) -> Transportation:
        itinerary = self.db.query(Itinerary).filter(Itinerary.itinerary_id == itinerary_id).first()
        if not itinerary:
            return None
        
        result = generate_transportation_agent(itinerary)

        trasnportation_details = TransportationCreate(transportation_details=result)

        return self.create_transportation(trasnportation_details, itinerary_id)