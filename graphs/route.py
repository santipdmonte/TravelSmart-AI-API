from states.route import RouteStateInput, RouteStateOutput
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from dotenv import load_dotenv

load_dotenv()

# == PROMPTS ==


def get_route_prompt(state: RouteStateInput):
    PROMPT = f"""
Eres un asistente de viajes con 15 años de experiencia que ayuda a los usuarios a planificar sus rutas de viaje.
Tu objetivo es generar dos opciones de rutas de viaje para un usuario, para que elija la que mejor se adapte a sus preferencias.
Las rutas deben tener un conjunto de destinos y cantidad de dias que se debe pasar en cada destino.
Debes justificar el motivo de la ruta y la cantidad de dias que se debe pasar en cada destino.
Optimiza las rutas considerando distancias, costos, tiempos de traslado
Asegúrate de que cada destino tenga suficiente tiempo para ser disfrutado sin prisas

Destino: {state.destino_general}
Duración: {state.cantidad_dias}
Objetivo del viaje: {state.objetivo_viaje}
Temporada del viaje: {state.temporada_viaje}

#### RUTA DETALLADA POR DESTINOS
- Se considera un nuevo destino cuando el pasajero debe dormir en otro lugar que no sea el destino actual.
- Para cada destino establecer el nombre de la ciudad, pais. (Con este nombre se debe poder encontrar la ciudad en paginas de hoteles como booking.com, tripadvisor, etc.)

{f"""
Feedback del usuario: {state.user_feedback}

Crear dos nuevas rutas, a partir del feedback del usuario.
Las nuevas rutas sugeridas se deben ajustar al feedback del usuario.
""" if state.user_feedback else ""}

{f"""
El feedback del usuario hace referencia a esta ruta, considerala como punto de partida para ajustar los cambios mencionados por el usuario.
Rutas seleccionada: {state.ruta_seleccionada}
""" if state.ruta_seleccionada else ""}

"""

    return PROMPT


# == NODES ==

def generate_route(state: RouteStateInput):
    """Generar el plan de ruta
    
    Args:
        state: Input state
    """

    print(f"Initail State: {state}")

    model = ChatOpenAI(model="gpt-5-mini")
    structured_llm = model.with_structured_output(RouteStateOutput)
    results = structured_llm.invoke(
    # results = model.invoke(
        [
            SystemMessage(content=get_route_prompt(state))
        ]
    )

    print(f"State: {results}")
    return results 

