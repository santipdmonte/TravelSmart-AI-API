from langgraph.graph import START, END, StateGraph
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
import json


from langgraph.prebuilt import create_react_agent
from tools.hotels_finder import obtener_hoteles_disponibles
from accommodation_graph.state import (
    AlojamientoStateInput,
    AlojamientoState,
)

load_dotenv()

def generar_recomendaciones_hoteles(state: AlojamientoStateInput):
    """Generar recomendaciones de hoteles para el viaje"""

    model = ChatOpenAI(model="gpt-4.1-mini-2025-04-14", temperature=0)

    obtener_hoteles_disponibles_agent = create_react_agent(
        model=model,
        tools=[
            obtener_hoteles_disponibles
        ],
        name="obtener_hoteles_disponibles_agent",
        prompt=f"Encuentra los mejores hoteles disponibles para el viaje. {state}"
    )

    return obtener_hoteles_disponibles_agent.invoke(state)

# Add nodes
builder = StateGraph(input=AlojamientoStateInput)
builder.add_node("obtener_hoteles_disponibles_agent", generar_recomendaciones_hoteles)

# Add edges
builder.add_edge(START, "obtener_hoteles_disponibles_agent")
builder.add_edge("obtener_hoteles_disponibles_agent", END)

accommodation_graph = builder.compile()
