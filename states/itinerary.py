from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class TrasnportEnum(str, Enum):
    AVION = "Avión"
    TREN = "Tren"
    COLECTIVO = "Colectivo"
    AUTO = "Auto"
    BARCO = "Barco"
    OTRO = "Otro"
    
class TransporteEntreDestinosState(BaseModel):
    ciudad_origen: str = Field(..., description="Ciudad de origen del transporte")
    ciudad_destino: str = Field(..., description="Ciudad de destino del transporte")
    tipo_transporte: TrasnportEnum = Field(..., description="Tipo de transporte entre destinos")
    justificacion: str = Field(..., description="Justificacion del transporte entre destino elegido")
    alternativas: List[str] = Field(..., description="Listado de alternativas de transporte entre destinos")

class DestinoState(BaseModel):
    ciudad: str = Field(..., description="Ciudad del destino")
    pais: str = Field(..., description="Pais del destino")
    pais_codigo: str = Field(..., description="Codigo del pais del destino. Ejemplo: 'AR', 'US', 'ES', etc")
    coordenadas: str = Field(..., description="Coordenadas del destino")
    dias_en_destino: int = Field(..., description="Cantidad de dias en el destino")
    # actividades_sugeridas: List[str] = Field(..., description="Listado de actividades sugeridas en el destino en base a las preferencias del usuario")
    sugerencias_alojamiento: str = Field(..., description="Sugerencias de zonas de alojamiento en el destino en base a las preferencias del usuario")

class ViajeStateInput(BaseModel):
    nombre_viaje: str 
    cantidad_dias: int

class ViajeState(BaseModel):
    ruta_elegida: str = Field(..., description="Descripcion de la ruta optima elegida en base a las preferencias del usuario")
    justificacion_ruta_elegida: str = Field(..., description="Justificacion de la ruta optima elegida en base a las preferencias del usuario")
    nombre_viaje: str = Field(..., description="Nombre del viaje segun el destino general")
    cantidad_dias: int = Field(..., description="Cantidad de dias totales del viaje completo")
    destino_general: str = Field(..., description="Destino general del viaje. Ejemplo: 'Europa', 'Asia', 'Estados Unidos', etc")
    resumen_viaje: str = Field(..., description="Resumen del viaje completo en base a las preferencias del usuario")
    destinos: List[DestinoState] = Field(..., description="Destinos del viaje completo en base a las preferencias del usuario")
    transportes_entre_destinos: Optional[List[TransporteEntreDestinosState]] = Field(..., description="Transportes entre destinos del viaje completo (si el viaje tiene mas de un destino)")
    itinerario_diario: Optional[List[Dict[str, Any]]] = Field(None, description="JSON field containing itinerary daily details")

class ViajeStateModify(BaseModel):
    itinerario_actual: ViajeState
    prompt: str
