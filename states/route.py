from typing import List
from pydantic import BaseModel
from typing import Optional

class DestinoState(BaseModel):
    ciudad: str
    pais: str
    pais_codigo: str
    coordenadas: str
    dias_en_destino: int
    breve_descripcion_destino: str

class RouteState(BaseModel):
    cantidad_dias: int
    nombre_viaje: str
    justificacion_ruta_elegida: str
    destinos: List[DestinoState]

class RouteStateOutput(BaseModel):
    rutas: List[RouteState]

class RouteStateInput(BaseModel):
    destino_general: str 
    cantidad_dias: int
    objetivo_viaje: str
    temporada_viaje: str
    user_feedback: Optional[str] = None
    ruta_seleccionada: Optional[RouteState] = None
