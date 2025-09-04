"""
agent_planner_graph.py
This graph is used to create a react agent with a custom state and tools.
"""

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt.chat_agent_executor import AgentState
from langchain_core.messages import AnyMessage
from typing import Annotated

from langmem.short_term import SummarizationNode
from langchain_core.messages.utils import count_tokens_approximately
from typing import Any

from langchain_core.tools import InjectedToolCallId
from langgraph.types import Command
from langchain_core.messages import ToolMessage

from states.itinerary import ViajeState

from langgraph.types import interrupt


# Define model and checkpointer
model = ChatOpenAI(model="gpt-5-mini")
web_search_model = "gpt-5"
checkpointer = MemorySaver()

# ==== Custom state ====
class ActivitiesCityState(AgentState):
    context: dict[str, Any]
    city: str
    days: int


# ==== Prompt ====
def generate_activities_city_prompt(state: ActivitiesCityState):
    PROMPT = f"""
Eres un asistente de viajes que ayuda a los usuarios a planificar sus viajes. 
Tu objetivo es generar un itinerario detallado de actividades para una ciudad.
Considera los tiempos del viajero y los traslados entre ciudades. 
Considera que el primer dia del viaje es el dia de llegada y el ultimo dia es el dia de salida.
Debes buscar en internet toda la informacion relevante sobre las actividades que se pueden realizar en la ciudad. 
Debes tener en cuenta los horarios de apertura, precio y disponibilidad de las actividades.
Debes proporcionar para las actividades que proporcionen reserva previa el link de la reserva.

El viajero es de tipo aventurero y le gusta realizar actividades al aire libre.

En esta ocacion el viajero esta realizando un viaje con su grupo de amigos (23 años).

El destino es {state["city"]} en {state["days"]} dias.
"""

    return PROMPT

# ==== Tools ====

def web_search(
    query: str
) -> str:
    """
    Search the web for the query.
    """
    from openai import OpenAI
    client = OpenAI()

    response = client.responses.create(
        model=web_search_model,
        tools=[{"type": "web_search"}],
        input=query
    )

    return response.output[-1].content[0].text

tools = [web_search]

# ==== Create agents ====
activities_city_agent = create_react_agent(
    model,
    tools=tools,
    prompt=generate_activities_city_prompt,
    checkpointer=checkpointer,
    state_schema=ActivitiesCityState,
)


import uuid
from langchain_core.runnables import RunnableConfig


def generate_activities_city_ai(city: str, days: int):

    config: RunnableConfig = {
        "configurable": {
            "thread_id": uuid.uuid4(),
        }
    }

    state = {
        "city": city,
        "days": days,
    }

    state = activities_city_agent.invoke(state, config=config)
    return state