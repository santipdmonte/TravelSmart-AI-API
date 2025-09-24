from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_tavily import TavilySearch
from langgraph.checkpoint.memory import InMemorySaver

from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model


class State(TypedDict):
    feedback: str | None = None
    city: str
    days: int
    itinerary: str
    messages: Annotated[list, add_messages]


def get_itinerary_prompt(state: State):
    return f"""
Eres un asistente de viajes con 15 años de experiencia que ayuda a los usuarios a planificar las actividades que pueden realizar en su viaje. 
Tu objetivo es generar un itinerario detallado de actividades para realizar en {state["city"]} durante {state["days"]} dias.

Considera que el primer dia el viajero llega a la ciudad, por lo que tendra menos tiempo para realizar actividades.
Realiza un itinerario detallado para cada dia. 
Separa las actividades segun el momento del dia (mañana, tarde, noche, tarde-noche, etc.) recomendado para cada actividad.
Para cada actividad sugerida considera los horarios, precios, duracion, reserva e info adicional (segun corresponda a la actividad).
Considera la ubicacion de las actividades y el desplazamiento entre ellas. Intenta de agrupar actividades cercanas en el mismo dia.
Debes buscar en internet toda la informacion relevante sobre las actividades que se pueden realizar en la ciudad. 
Debes tener en cuenta y aclararle al usuario los horarios de apertura, precio y disponibilidad de las actividades.
Debes proporcionar para las actividades que proporcionen reserva previa el link de la reserva.
Tambien indica recomendaciones del destino que visita.
Recomienda la mejor forma de transporte para llegar a cada actividad.
Realiza una planificacion alternativa para un dia en el caso de lluvia.
Fuera de la planificacion diaria, mencionar otras actividades interesantes que no se inlcuyeron en la planificacion.

Planifica tu respueseta, tienes permitido usar la herramienta de busqueda web para obtener la informacion relevante que unicamente puedes obtener a traves de internet.
Tienes un limite de {(  int(state["days"]) * 2) + 2} usos de la herramienta de busqueda web. No uses la herramienta de busqueda web mas de {(int(state["days"]) * 2) + 2} veces.
Planifica las busuqedas en internet que debes hacer y realiza todas las llamadas a la herramienta al mismo tiempo.

Utiliza un lenguaje neutro o latinoamericano. La respuesta en formato markdown.
Responder unicamente con el itinerario detallado, no incluyas ningun otro texto adicional.

El viajero es de tipo aventurero y le gusta realizar actividades al aire libre.
En esta ocacion el viajero esta realizando un viaje con su grupo de amigos (23 años).
La temporada del viaje es en verano.

"""

def get_feedback_adjust_prompt(state: State):
    return f"""
    Eres un experto en planificacion de viajes, el encargado de ajustar el itinerario de viaje en base al feedback de tu supervisor.
    Feedback del supervisor: {state["feedback"]}
    Ajusta el itinerario de viaje en base al feedback del supervisor.
    Mantene el formato del itinerario de viaje. Ajustar unicamente los puntos que el supervisor te indique.
    """

def get_feedback_provider_prompt(itinerary: str):
    return f"""
    Eres un experto en planificacion de viajes, el encargado de proporcionar feedback sobre el itinerario de viaje.
    Itinerario de viaje: {itinerary}
    Provee feedback sobre el itinerario de viaje.
    Mantene el formato del itinerario de viaje.
    """


def itinerary_agent(state: State):

    if state["feedback"]:
        response = llm_with_tools.invoke(get_feedback_adjust_prompt(state))
        with open(f"../examples/activities_city_{state['city']}_{state['days']}_{config['configurable']['thread_id']}_final.md", "w") as f:
            f.write(response.content)
    else:
        response = llm_with_tools.invoke(get_itinerary_prompt(state))
        with open(f"../examples/activities_city_{state['city']}_{state['days']}_{config['configurable']['thread_id']}_tmp.md", "w") as f:
            f.write(response.content)

    return {"messages": [response]}


def feedback_agent(state: State):
    itinerary = state["messages"][-1].content

    feedback = llm.invoke(get_feedback_provider_prompt(itinerary))
    print(f"\n\nFeedback: {feedback}\n\n")

    return {"feedback": feedback}


def route_tools_and_feedback(
    state: State,
):
    """
    Use in the conditional_edge to route to the ToolNode if the last message
    has tool calls. Otherwise, check if there is feedback. If there is feedback, route to the feedback_agent.
    If there is no feedback, route to the end.
    """
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        print("\n\ntools\n\n")
        return "tools"
    
    if state["feedback"] is None:
        print("\n\nfeedback_agent\n\n")
        return "feedback_agent"

    print("\n\nEND\n\n")
    return END


# Tools
web_search = TavilySearch(
        max_results=3,
        topic="general",
        # include_answer=False,
        # include_raw_content=False,
        # include_images=False,
        # include_image_descriptions=False,
        # search_depth="basic",
        # time_range="day",
        # include_domains=None,
        # exclude_domains=None
    )

#  Nodes
tools = [web_search]
tool_node = ToolNode(tools=tools)

graph_builder = StateGraph(State)

#  Nodes
graph_builder.add_node("tools", tool_node)
graph_builder.add_node("itinerary_agent", itinerary_agent)
graph_builder.add_node("feedback_agent", feedback_agent)

#  Edges
graph_builder.add_edge(START, "itinerary_agent")
graph_builder.add_conditional_edges("itinerary_agent", 
    route_tools_and_feedback,
    {
        "tools": "tools",
        "feedback_agent": "feedback_agent",
        END: END
    }
)
graph_builder.add_edge("feedback_agent", "itinerary_agent")
graph_builder.add_edge("tools", "itinerary_agent")

llm = init_chat_model("openai:gpt-5-mini")
llm_with_tools = llm.bind_tools(tools)
memory = InMemorySaver()

graph = graph_builder.compile(checkpointer=memory)


state = {
    "feedback": None,
    "city": "Miami",
    "days": 3,}

config = {"configurable": {"thread_id": "123"}}

print(graph.invoke(state, config))

for chunk in graph.stream(state, config, stream_mode="updates"):
    print("--------------------------------\n\n")
    print(chunk)



# def stream_graph_updates(user_input: str):
#     for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
#         for value in event.values():
#             print("Assistant:", value["messages"][-1].content)


# while True:
#     try:
#         user_input = input("User: ")
#         if user_input.lower() in ["quit", "exit", "q"]:
#             print("Goodbye!")
#             break
#         stream_graph_updates(user_input)
#     except:
#         # fallback if input() is not available
#         user_input = "What do you know about LangGraph?"
#         print("User: " + user_input)
#         stream_graph_updates(user_input)
#         break