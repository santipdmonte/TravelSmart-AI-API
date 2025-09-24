"""
agent_planner_graph.py
This graph is used to create a react agent with a custom state and tools.
"""

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt.chat_agent_executor import AgentState

from langchain_tavily import TavilySearch
from langchain_core.messages import BaseMessage

# Define model and checkpointer
model = ChatOpenAI(model="gpt-5-mini")
checkpointer = MemorySaver()

# ==== Custom state ====
class ActivitiesCityState(AgentState):
    city: str
    days: int


# ==== Prompt ====

# def get_prompt(state: ActivitiesCityState):
#     PROMPT = f"""
# Eres un asistente de viajes que ayuda a los usuarios a planificar sus viajes. 
# Tu objetivo es generar un itinerario detallado de actividades para una ciudad.
# Considera que el primer dia el viajero llega a la ciudad, por lo que tendra menos tiempo para realizar actividades.
# Debes buscar en internet toda la informacion relevante sobre las actividades que se pueden realizar en la ciudad. 
# Debes tener en cuenta y aclararle al usuario los horarios de apertura, precio y disponibilidad de las actividades.
# Debes proporcionar para las actividades que proporcionen reserva previa el link de la reserva.
# Tambien indica recomendaciones del destino que visita.
# El viajero es de tipo aventurero y le gusta realizar actividades al aire libre.

# Planifica tu respueseta, tienes permitido usar la herramienta de busqueda web para obtener la informacion relevante que unicamente puedes obtener a traves de internet.
# Tienes un limite de 10 usos de la herramienta de busqueda web. No uses la herramienta de busqueda web mas de 10 veces.

# En esta ocacion el viajero esta realizando un viaje con su grupo de amigos (23 años).

# La ciudad es {state["city"]} en {state["days"]} dias.
# """


def prompt(
    state: ActivitiesCityState
):
    system_msg = f"""
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
    return [{"role": "system", "content": system_msg}] + state["messages"]



# ==== Tools ====

# def web_search(
#     query: str
# ) -> str:
#     """
#     Search the web for the query.
#     """


#     tavily_response = TavilySearch(
#         max_results=3,
#         topic="general",
#         # include_answer=False,
#         # include_raw_content=False,
#         # include_images=False,
#         # include_image_descriptions=False,
#         # search_depth="basic",
#         # time_range="day",
#         # include_domains=None,
#         # exclude_domains=None
#     )

#     response_prompt = f"""
#     Eres un experto en turismo y busacar informacion relevante en internet. 
#     En base a la query {query}, debes responder de forma resumida y relevante sobre esta busqueda: {tavily_response}
#     """

#     response = model.invoke(response_prompt)

#     return tavily_response.invoke(query)

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

tools = [web_search]

# ==== Create agent ====

activities_city_agent = create_react_agent(
    model,
    tools=tools,
    prompt=prompt,
    checkpointer=checkpointer,
    state_schema=ActivitiesCityState,
)