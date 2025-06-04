from typing import List, Optional
from pydantic import BaseModel
from state import DestinoState

class AlojamientoStateInput(BaseModel):
    destino: DestinoState   # nombre_destino, cantidad_dias_en_destino, dias_destino
    fecha_inicio: str
    cantidad_adultos: int
    cantidad_ninos: int

class AlojamientoState(BaseModel):
    pass
