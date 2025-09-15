from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

class TrasnportEnum(str, Enum):
    AVION = "Avión"
    TREN = "Tren"
    COLECTIVO = "Colectivo"
    AUTO = "Auto"
    BARCO = "Barco"
    OTRO = "Otro"
    
class TransporteEntreDestinosState(BaseModel):
    ciudad_origen: str
    ciudad_destino: str
    tipo_transporte: TrasnportEnum
    justificacion: str
    alternativas: List[str]

class DestinoState(BaseModel):
    ciudad: str
    pais: str
    pais_codigo: str
    coordenadas: str
    dias_en_destino: int
    actividades_sugeridas: List[str]
    sugerencias_alojamiento: str

class ViajeStateInput(BaseModel):
    nombre_viaje: str 
    cantidad_dias: int

class ViajeState(BaseModel):
    nombre_viaje: str
    cantidad_dias: int
    destino_general: str
    resumen_viaje: str
    justificacion_ruta_elegida: str
    destinos: List[DestinoState]
    transportes_entre_destinos: Optional[List[TransporteEntreDestinosState]] = []

class ViajeStateModify(BaseModel):
    itinerario_actual: ViajeState
    prompt: str
