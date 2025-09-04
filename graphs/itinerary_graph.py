from langgraph.graph import START, END, StateGraph
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from prompts.itinerary_prompt import get_itinerary_prompt
from dotenv import load_dotenv

from schemas.itinerary import ItineraryGenerate


load_dotenv()

from states.itinerary import (
    ViajeState
)

def generate_main_itinerary(state: ItineraryGenerate):
    """Generar el plan de viaje
    
    Args:
        state: Input state
    """

    print(f"Initail State: {state}")

    # Generar el plan de viaje
    model = ChatOpenAI(model="gpt-5-mini")

    structured_llm = model.with_structured_output(ViajeState)
    results = structured_llm.invoke(
    # results = model.invoke(
        [
            SystemMessage(content=get_itinerary_prompt(state))#,
        ]
    )

    print(f"State: {results}")

    return results 


# Add nodes
builder = StateGraph(ViajeState, input=ItineraryGenerate, output=ViajeState)
builder.add_node("generate_main_itinerary", generate_main_itinerary)

# Add edges
builder.add_edge(START, "generate_main_itinerary")
builder.add_edge("generate_main_itinerary", END)

itinerary_graph = builder.compile()
