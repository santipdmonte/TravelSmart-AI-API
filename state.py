from typing import List, Optional
from pydantic import BaseModel

    
class TransporteEntreDestinosState(BaseModel):
    origen: str
    destino: str
    tipo: str      # Avion, Tren, Bus, Auto, Barco, etc.

class ActividadState(BaseModel):
    nombre: str
    descripcion: str

class DiaDestinoState(BaseModel):
    posicion_dia: int
    actividades: list[ActividadState]

class DestinoState(BaseModel):
    nombre_destino: str
    cantidad_dias_en_destino: int
    dias_destino: List[DiaDestinoState] 

class ViajeStateInput(BaseModel):
    nombre_viaje: str 
    cantidad_dias: int
    # presupuesto: Optional[int] = None
    # estacion: Optional[str] = None  # Estacion de Año (Verano, Otoño, Invierno, Primavera)

class ViajeState(BaseModel):
    nombre_viaje: str
    cantidad_dias: int
    destino_general: str
    # presupuesto: Optional[int] = None
    # estacion: Optional[str] = None  # Estacion de Año (Verano, Otoño, Invierno, Primavera)
    destinos: List[DestinoState]
    transportes_entre_destinos: Optional[List[TransporteEntreDestinosState]] = None

class ViajeStateModify(BaseModel):
    itinerario_actual: ViajeState
    prompt: str
