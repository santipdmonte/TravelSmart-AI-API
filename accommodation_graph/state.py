from typing import List, Optional
from pydantic import BaseModel
from state import DiaDestinoState

class AlojamientoInputState(BaseModel):
    destino: str
    cantidad_dias: int
    dias_destino: List[DiaDestinoState]
    fecha_inicio: str
    fecha_fin: str

class AlojamientoState(BaseModel):
    pass
