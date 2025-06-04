from langgraph.graph import START, END, StateGraph
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

from langgraph.prebuilt import create_react_agent
from tools.hotels_finder import obtener_hoteles_disponibles
from accommodation_graph.state import (
    AlojamientoInputState,
    AlojamientoState,
    DiaDestinoState
)


load_dotenv()

from state import (
    ViajeState,
    ViajeStateInput,
    ActividadState
)

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

destino_input = AlojamientoInputState (
    destino="Roma",
    cantidad_dias=3,
    dias_destino=[
        DiaDestinoState(
            posicion_dia=1,
            actividades=[]
        )
    ],
    fecha_inicio="2025-05-01",
    fecha_fin="2025-05-07"
)

obtener_hoteles_disponibles_agent = create_react_agent(
    model=model,
    tools=[
        obtener_hoteles_disponibles
    ],
    name="obtener_hoteles_disponibles_agent",
    prompt=f"Encuentra los mejores hoteles disponibles para el viaje. {destino_input}"
)

# Add nodes
builder = StateGraph(ViajeState, input=ViajeStateInput)
builder.add_node("obtener_hoteles_disponibles_agent", obtener_hoteles_disponibles_agent)

# Add edges
builder.add_edge(START, "obtener_hoteles_disponibles_agent")
builder.add_edge("obtener_hoteles_disponibles_agent", END)

graph = builder.compile()


input_state = ViajeStateInput(
    destino="Italia", 
    cantidad_dias=7, 
    # presupuesto=1000, 
    # estacion="Verano"
)

result = graph.invoke(input_state)
print(result)
