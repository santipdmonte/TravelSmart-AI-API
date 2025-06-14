from langgraph.graph import START, END, StateGraph
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

load_dotenv()

from state import (
    ViajeState,
    ViajeStateModify
)

def modify_itinerary(state: ViajeStateModify):
    """Modificar el plan de viaje
    
    Args:
        state: Input state
        
    Returns:
        State with the modified plan of the trip
    """

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    # model = ChatOpenAI(model="o4-mini-2025-04-16")

    structured_llm = model.with_structured_output(ViajeState)
    results = structured_llm.invoke(
        [
            SystemMessage(content=f"""
                Eres un experto en ajustar itinerarios de viajes segun las necesidades del usuario. 
                El usuario tiene el siguiente itinerario de viaje. 
                <itinerario_actual>
                    {state.itinerario_actual}
                </itinerario_actual>

                Ahora te pide hacer unas modificaciones al plan de viaje. 
                <peticiones_usuario >
                    {state.prompt}
                </peticiones_usuario>
            """
            ),
            HumanMessage(content=f"""
                <itinerario_actual>
                    {state.itinerario_actual}
                </itinerario_actual>

                Ahora te pide hacer unas modificaciones al plan de viaje. 
                <peticiones_usuario >
                    {state.prompt}
                </peticiones_usuario>
            """)
        ]
    )

    return dict(results) 

# Add nodes
builder = StateGraph(ViajeStateModify)
builder.add_node("modify_itinerary", modify_itinerary)

# Add edges
builder.add_edge(START, "modify_itinerary")
builder.add_edge("modify_itinerary", END)

checkpointer = MemorySaver()

modify_itinerary_graph = builder.compile() #checkpointer=checkpointer)

# result = graph.invoke(input_state)
# print(result)
