from typing import Annotated
import uuid

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, AnyMessage
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_community.tools import TavilySearchResults
from langgraph.checkpoint.memory import InMemorySaver

from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model


class State(TypedDict):
    city: str
    days: int
    feedback: str | None = None
    tmp_itinerary: str | None = None
    final_itinerary: str | None = None
    tool_calling: bool = False
    messages: Annotated[list[AnyMessage], add_messages]


# ## 1) Datos necesarios (Rellenar antes de la corrección)
# - Fecha y hora de llegada (ej.: 2025-06-10 09:30) (si aplica)
# - Fecha y hora de salida (ej.: 2025-06-15 21:00) (si aplica)
# - Medios de transporte entre destinos (vuelo/tren/bus/coche) y horarios si ya los tienes  
# - Duración prevista en cada lugar y alojamiento reservado (nombre, dirección, check-in / check-out)  
# - Prioridades / intereses (marca todos los que apliquen: museos, naturaleza, gastronomía, playa, compras, vida nocturna, senderismo, descanso)  
# - Número de viajeros y si hay niños/personas con movilidad reducida  
# - Presupuesto aproximado por persona (si aplica)  
# - Restricciones alimentarias o de salud relevantes

OUTPUT_TEMPLATE = """

Respetar el siguiente formato de salida (mencionado entre <output_template> y </output_template>):

<output_template>

Dia X: <breve resumen del dia>
- Mañana:
  - Actividad 1: [Nombre o enlace]  
    - Horario: (hora apertura / cierre / hora prevista)  
    - Precio: (entrada / descuentos / gratuidades)  
    - Duración estimada: (min / h)  
    - Reserva: (link de reserva o "no requiere")  
    - Ubicación: (dirección / barrio)  
    - Transporte recomendado desde zona centro o turistica / actividad anterior: (tiempo estimado / medio)
  - Actividad 2: [Nombre o enlace]  
    - (mismos subcampos)
- Tarde:
  - Actividad 3: [Nombre o enlace]  
    - (mismos subcampos)
  - Actividad 4: [Nombre o enlace]  
    - (mismos subcampos)
- Noche:
  - Actividad 5: [Nombre o enlace] (cena / evento)  
    - (mismos subcampos)
- Notas del día (reservas realizadas, tiempos de buffer, conexiones): (texto)

(Repetir bloque para cada día del viaje)

----

- Plan alternativo por lluvia:
  - Actividad A (interior): [Nombre / enlace]  
    - Horario / Precio / Reserva
  - Actividad B (interior): ...
- Otras actividades interesantes no incluidas en el plan original
- Recomendaciones de transporte local (p. ej. tarjetas de metro, apps útiles)
- Recomendaciones generales del destino (seguridad, salud, horarios locales)

</output_template>

"""

ADITIONAL_CONTEXT = """
El viajero es de tipo aventurero y le gusta realizar actividades al aire libre.
En esta ocacion el viajero esta realizando un viaje con su grupo de amigos (23 años).
La temporada del viaje es en verano.
"""

def get_itinerary_prompt(state: State):
    return [SystemMessage(content=f"""
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
Tu respuesta sera utilizada directamente en el itinerario final de viaje.

{ADITIONAL_CONTEXT}

{OUTPUT_TEMPLATE}
""")]

def get_feedback_fixer_prompt(state: State):
    return [SystemMessage(content=f"""
Eres un experto en planificacion de viajes, el encargado de ajustar el itinerario de viaje en base al feedback de tu supervisor.
Feedback del supervisor: 

<feedback>
{state["feedback"]}
</feedback>

Ajusta el itinerario de viaje en base al feedback del supervisor.
Mantene el formato del itinerario de viaje. Ajustar unicamente los puntos que el supervisor te indique. Mantener links de las actividades.

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

El itinerario debe mantener exactamente el mismo formato, modificando unicamente los puntos que el supervisor te indique.
No agregues ningun otro texto adicional. Tu respuesta sera utilizada directamente en el itinerario final de viaje.
Responde en formato markdown.

<Itinerario de viaje>
{state["tmp_itinerary"]}
</Itinerario de viaje>


{OUTPUT_TEMPLATE}
""")]

def get_feedback_provider_prompt(itinerary: str):
    return [SystemMessage(content=f"""
    Eres un experto en planificacion de viajes, el encargado de proporcionar feedback sobre el itinerario de viaje.
    Considera el contexto adicional:
    {ADITIONAL_CONTEXT}

    <Itinerario de viaje>
    {itinerary}
    </Itinerario de viaje>

    Provee feedback sobre el itinerario de viaje.
    El feedback se debe enfocar en las cosas a ajustar en el itinerario.
    El feedback debe ser puntual y específico. Las cosas que no sean relevantes para el itinerario no las menciones.
    Mencionar unicamente los cambios sugeridos. Las cosas que esten bien del itinerario no las menciones.
    Si consideras que el itinerario es perfecto, no sugieras cambios.
    Si unicamente econtras 1 cosa a mejorar, sugeri solo ese cambio.
    Evita hacer sugerencias innecesarias.
    """)]


# Nodes

def web_search_planner(state: State):
    print("\n\nweb_search_planner\n\n")

    response = llm_with_tools.invoke(get_itinerary_prompt(state))

    return {"messages": [response]}


def initial_itinerary_agent(state: State):
    print("\n\ninitial_itinerary_agent\n\n")
    thread_id = config["configurable"]["thread_id"]

    response = llm.invoke(get_itinerary_prompt(state) + state["messages"])

    city = state["city"]
    days = state["days"]
    with open(f"../examples/activities_city_{city}_{days}_{thread_id}_tmp.md", "w") as f:
        f.write(response.content)

    return {"messages": [response], "tmp_itinerary": response.content}


def feedback_provider_agent(state: State):
    print("\n\nfeedback_provider_agent\n\n")
    response = llm.invoke(get_feedback_provider_prompt(state["tmp_itinerary"]))
    city = state["city"]
    days = state["days"]
    thread_id = config["configurable"]["thread_id"]
    with open(f"../examples/activities_city_{city}_{days}_{thread_id}_feedback.md", "w") as f:
        f.write(response.content)

    return {"messages": [response], "feedback": response.content}


def feedback_fixer_agent(state: State):
    print("\n\nfeedback_fixer_agent\n\n")
    response = llm.invoke(get_feedback_fixer_prompt(state))
    city = state["city"]
    days = state["days"]
    thread_id = config["configurable"]["thread_id"]
    with open(f"../examples/activities_city_{city}_{days}_{thread_id}_final.md", "w") as f:
        f.write(response.content)

    return {"messages": [response], "final_itinerary": response.content}


# def route_tools_and_feedback(
#     state: State,
# ):
#     """
#     Use in the conditional_edge to route to the ToolNode if the last message
#     has tool calls. Otherwise, check if there is feedback. If there is feedback, route to the feedback_agent.
#     If there is no feedback, route to the end.
#     """
#     if isinstance(state, list):
#         ai_message = state[-1]
#     elif messages := state.get("messages", []):
#         ai_message = messages[-1]
#     else:
#         raise ValueError(f"No messages found in input state to tool_edge: {state}")
#     if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
#         print("\n\ntools\n\n")
#         return "tools"
    
#     if state["feedback"] is None:
#         print("\n\nfeedback_agent\n\n")
#         return "feedback_agent"

#     print("\n\nEND\n\n")
#     return END

# graph_builder.add_conditional_edges("itinerary_agent", 
#     route_tools_and_feedback,
#     {
#         "tools": "tools",
#         "feedback_agent": "feedback_agent",
#         END: END
#     }
# )


# Tools
web_search = TavilySearchResults(
        max_results=2,
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
graph_builder.add_node("web_search_planner", web_search_planner)
graph_builder.add_node("initial_itinerary_agent", initial_itinerary_agent)
graph_builder.add_node("feedback_provider_agent", feedback_provider_agent)
graph_builder.add_node("feedback_fixer_agent", feedback_fixer_agent)
#  Edges
graph_builder.add_edge(START, "web_search_planner")
graph_builder.add_edge("web_search_planner", "tools")
graph_builder.add_edge("tools", "initial_itinerary_agent")
graph_builder.add_edge("initial_itinerary_agent", "feedback_provider_agent")
graph_builder.add_edge("feedback_provider_agent", "feedback_fixer_agent")
graph_builder.add_edge("feedback_fixer_agent", END)

llm = init_chat_model("openai:gpt-5-mini")
llm_with_tools = llm.bind_tools(tools)
memory = InMemorySaver()

# graph = graph_builder.compile(checkpointer=memory)
graph = graph_builder.compile()


state = {
    "feedback": None,
    "city": "Amsterdam",
    "days": 3
}

config = {"configurable": {"thread_id": str(uuid.uuid4())}}

# print(graph.invoke(state, config))


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