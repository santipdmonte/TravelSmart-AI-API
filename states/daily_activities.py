from pydantic import BaseModel, Field

class ActivityItineraryOutput(BaseModel):
    titulo: str = Field(..., description="El titulo o nombre de la actividad propuesta")
    descripcion: str = Field(..., description="La descripcion de la actividad (breve)")
    horarios: str = Field(description="Los horarios de la actividad (rango o abrir/cerrar o recomendaciones)")
    precio: str = Field(description="El precio de la actividad (aproximar si aplica)")
    requisitos_reserva: str = Field(description="Los requisitos de reserva de la actividad (si aplica)")
    enlace: str = Field(description="El enlace de la actividad (link de reserva o página oficial, evitar enlaces no oficiales)(si aplica)")
    ubicacion: str = Field(description="La ubicacion de la actividad (dirección / barrio / zona)")
    transporte_recomendado: str = Field(description="El transporte recomendado para la actividad desde la actividad previa")

# Structured output
class DailyItineraryOutput(BaseModel):
    dia: str = Field(..., description="El dia del itinerario (1, 2, 3, etc.)")
    ciudad: str = Field(..., description="La ciudad del dia correspondiente")
    pais: str = Field(..., description="El pais del dia correspondiente")
    titulo: str = Field(..., description="Titulo del dia correspondiente. 'Dia X - <Ciudad>: <Breve titulo del dia>'")
    actividades_mañana: list[ActivityItineraryOutput] = Field(description="Lista de actividades para la mañana (si aplica)")
    actividades_tarde: list[ActivityItineraryOutput] = Field(..., description="Lista de actividades para la tarde")
    actividades_noche: list[ActivityItineraryOutput] = Field(description="Lista de actividades para la noche (si aplica)")
    # notas_dia: str = Field(description="Notas del dia correspondiente")