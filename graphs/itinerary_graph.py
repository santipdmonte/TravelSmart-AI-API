from langchain_openai import ChatOpenAI
from prompts.itinerary_prompt import get_itinerary_prompt
from schemas.itinerary import ItineraryGenerate
from states.itinerary import ViajeState
from utils.llm import llm
from utils.itinerary_validators import validate_and_fix_itinerary, log_itinerary_structure

from dotenv import load_dotenv
load_dotenv()


def generate_main_itinerary(state: ItineraryGenerate):
    """
    Genera el itinerario principal usando IA y valida la estructura.
    
    Esta función:
    1. Invoca la IA para generar el itinerario
    2. Valida que los transportes sean secuenciales
    3. Auto-corrige si es necesario
    4. Retorna el itinerario validado
    """
    
    # Invocar la IA para generar el itinerario
    llm_structured = llm.with_structured_output(ViajeState)
    viaje_state = llm_structured.invoke(get_itinerary_prompt(state))
    
    # Log de la estructura generada (para debugging)
    log_itinerary_structure(viaje_state)
    
    # Validar y corregir si es necesario
    try:
        viaje_state_validado = validate_and_fix_itinerary(viaje_state)
        return viaje_state_validado
    except ValueError as e:
        print(f"❌ ERROR CRÍTICO: No se pudo validar/corregir el itinerario: {e}")
        # En caso de error crítico, retornar el original y loggear el problema
        # En producción, podrías querer lanzar una excepción o reintentar
        print("⚠️ Retornando itinerario sin validar (REVISAR LOGS)")
        return viaje_state


# DEPRECATED
# def generate_main_itinerary(state: ItineraryGenerate):
#     """Generar el plan de viaje
    
#     Args:
#         state: Input state
#     """

#     print(f"Initail State: {state}")

#     # Generar el plan de viaje
#     model = ChatOpenAI(model="gpt-5-mini")

#     structured_llm = model.with_structured_output(ViajeState)
#     results = structured_llm.invoke(
#     # results = model.invoke(
#         [
#             SystemMessage(content=get_itinerary_prompt(state))#,
#         ]
#     )

#     print(f"State: {results}")

#     return results 


# # Add nodes
# builder = StateGraph(ViajeState, input=ItineraryGenerate, output=ViajeState)
# builder.add_node("generate_main_itinerary", generate_main_itinerary)

# # Add edges
# builder.add_edge(START, "generate_main_itinerary")
# builder.add_edge("generate_main_itinerary", END)

# itinerary_graph = builder.compile()
