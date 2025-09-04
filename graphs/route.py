from schemas.itinerary import ItineraryGenerate
from pydantic import BaseModel

from langgraph.graph import START, END, StateGraph
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from dotenv import load_dotenv

load_dotenv()

# == STATES ==

class DestinationState(BaseModel):
    city_name: str
    country_name: str
    country_code: str
    coordinates: str
    days: int
    activities_suggestions: str

class RouteState(BaseModel):
    destinations: list[DestinationState]
    justification: str


# == PROMPTS ==


def get_route_prompt(state: ItineraryGenerate):
    PROMPT = f"""
    # PROMPT MAESTRO PARA GENERACIÓN DE RUTAS

    ## IDENTIDAD DEL ASISTENTE
    Eres un asistente de viajes que ayuda a los usuarios a planificar sus viajes.
    Tu objetivo es generar una ruta de viaje para un usuario.
    La ruta debe tener un conjunto de destinos y el tiempo que se debe pasar en cada destino.
    Debes justificar el motivo de la ruta y la cantidad de dias que se debe pasar en cada destino.
    Realizando una breve descripcion de las posibles actividades que realizara en cada destino.

Destino: {state.trip_name}
Duración: {state.duration_days}

{f"""
Descripcion del perfil: \n {state.traveler_profile_desc}
Tene en cuenta estas preferencias para ajustar las recomendaciones al viajero.
""" if state.traveler_profile_desc else ""
}

{f"""Preferencias puntualespara este viaje: 
{state.preferences}
*Estas son preferencias puntuales que este cliente selecciono, por lo que tienen un mayor peso sobre la descripcion del perfil""" 
if state.preferences else ""}

#### B. ITINERARIO DETALLADO POR DESTINOS Y DÍAS
**Cada destino:**
- Se considera un nuevo destino cuando el pasajero debe dormir en otro lugar que no sea el destino actual.
- Para cada destino establecer el nombre de la ciudad, pais. (Con este nombre se debe poder encontrar la ciudad en paginas de hoteles como booking.com, tripadvisor, etc.)

"""

    return PROMPT


# == NODES ==

def generate_route(state: ItineraryGenerate):
    """Generar el plan de ruta
    
    Args:
        state: Input state
    """

    print(f"Initail State: {state}")

    model = ChatOpenAI(model="gpt-5-mini")
    structured_llm = model.with_structured_output(RouteState)
    results = structured_llm.invoke(
    # results = model.invoke(
        [
            SystemMessage(content=get_route_prompt(state))
        ]
    )

    print(f"State: {results}")
    return results 

