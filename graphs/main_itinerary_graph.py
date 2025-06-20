from langgraph.graph import START, END, StateGraph
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

load_dotenv()

from state import (
    ViajeState,
    ViajeStateInput,
)

def generate_main_itinerary(state: ViajeStateInput):
    """Generar el plan de viaje
    
    Args:
        state: Input state
        
    Returns:
        State with the plan of the trip
    """

    print(f"Initail State: {state}")

    # Generar el plan de viaje
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = model.with_structured_output(ViajeState)
    results = structured_llm.invoke(
        [
            SystemMessage(content="Eres un experto en planificación de viajes"),
            HumanMessage(content=f"Genera un plan de viaje para {state.nombre_viaje} con {state.cantidad_dias} días. Incluye actividades diarias detalladas.")
        ]
    )

    return dict(results) 


# Add nodes
builder = StateGraph(ViajeState, input=ViajeStateInput)
builder.add_node("generate_main_itinerary", generate_main_itinerary)

# Add edges
builder.add_edge(START, "generate_main_itinerary")
builder.add_edge("generate_main_itinerary", END)

checkpointer = MemorySaver()

main_itinerary_graph = builder.compile() #checkpointer=checkpointer)


# input_state = ViajeStateInput(
#     destino="Italia", 
#     cantidad_dias=7, 
#     # presupuesto=1000, 
#     # estacion="Verano"
# )

# result = graph.invoke(input_state)
# print(result)
