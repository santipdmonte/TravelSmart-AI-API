"""
agent_planner_graph.py
This graph is used to create a react agent with a custom state and tools.
"""

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.prebuilt import InjectedState
from pydantic import Field
from langchain_core.messages import AnyMessage
from typing import Annotated, Any
from enum import Enum

from langmem.short_term import SummarizationNode
from langchain_core.messages.utils import count_tokens_approximately
from langchain_core.tools import InjectedToolCallId
from langgraph.types import Command
from langchain_core.messages import ToolMessage

from states.itinerary import ViajeState
from states.daily_activities import DailyItineraryOutput

from langgraph.types import interrupt


from utils.llm import llm, llm_cheap
from utils.utils import update_activities_day

# Define model and checkpointer
# model = ChatOpenAI(model="gpt-5-mini")
model = llm
web_search_model = "gpt-5-mini"
checkpointer = MemorySaver()

# ==== Custom state ====
summarization_node = SummarizationNode( 
    token_counter=count_tokens_approximately,
    model=model,
    max_tokens=1500,
    max_summary_tokens=500,
    output_messages_key="llm_input_messages",
)


class CustomState(AgentState):
    context: dict[str, Any]  # Used to store context of the summarization_node, to prevent the need of summarizing the context in all the runs
    itinerary: ViajeState

# ==== Prompt ====
PROMPT = """
<Rols>
Eres un asistente de viajes que ayuda a los usuarios a planificar sus viajes y a resolver sus dudas. 
Eres colaborativo y tienes un tono persona y agradable.
</Rol>

<Instructions>
- Responde las dudas del cliente de forma clara y concisa.
- Puedes usar la herramienta web_search para buscar informacion en la web.
- Puedes usar la herramienta replace_string_in_itinerary para hacer modificaciones al itinerario.
- Si el cliente te hace una aclaracion que consideres importante. Puedes usar la herramienta add_memory_notes para agregar las notas a la memoria del usuario o del itinerario.

</Instructions>

<Tools>
Usa la herramienta replace_string_in_itinerary para modificar el itinerario. Con esta herramienta puedes reemplazar un string exacto en el itinerario.
Los input de esta herramienta son de tipo string. y deben ir entre comillas dobles. No pueden ingresar valores de tipo int, float, bool, dict, list, etc.

Cuando el usuario te hace una aclaracion que consideres importante. Puedes usar la herramienta add_memory_notes para agregar las notas a la memoria del usuario o del itinerario.
La memoria del usuario persitira para los diferentes itinerarios.
La memoria del itinerario solo persitira para este itinerario en particular.
Las preferencias generales del usuario guardalas como memoria del usuario, las preferencias puntuales para este viaje guardalas como memoria del itinerario.
</Tools>

"""

def prompt(
    state: CustomState
):
    itinerary = state["itinerary"]
    system_msg = f"{PROMPT} El itinerario actual es: {itinerary}"
    return [{"role": "system", "content": system_msg}] + list(state["messages"])


# ==== Tools ====
# # ==== Memory Notes ====
# class MemoryNotesType(Enum):
#     USER_NOTES = "user_notes"
#     ITINERARY_NOTES = "itinerary_notes"

# def add_memory_notes(
#     notas: str = Field(..., description="Recordatorio de preferencia del usaurio, para este viaje o para su perfil"), 
#     type: MemoryNotesType = Field(..., description="Tipo de notas a agregar. USER_NOTES o ITINERARY_NOTES.")
# ):
#     """
#     Agrega notas a la memoria del usuario o del itinerario.
#     El tipo de notas puede ser USER_NOTES o ITINERARY_NOTES.
#     USER_NOTES son notas que permanecen en la memoria del usuario. Estas notas se usaran para futuras conversaciones y generaciones de itinertios personalizados.
#     ITINERARY_NOTES son notas que permanecen en la memoria del itinerario. Estas notas se usaran para este itiinerario en particular.
#     """
#     print(f"====\n \n Notes: {notas} \n Type: {type} \n ====")
#     # TODO: Add the notes to DB
#     return f"Notes added to the memory. Type: {type}"

def modify_activities(
    tool_call_id: Annotated[str, InjectedToolCallId],
    new_activities_day: DailyItineraryOutput = Field(..., description="Nuevo dia con las actividades modificadas"),
    new_activities_day_modifications_summary: str = Field(..., description="Resumen de las modificaciones a realizar en el dia"),
    titulo_dia: str = Field(..., description="El titulo del dia correspondiente. 'Dia X - <Ciudad>: <Breve titulo del dia>'"),
    itinerary: Annotated[ViajeState | None, InjectedState("itinerary")] = None,
) :
    """
    Modify the itinerary.
    
    input:
        - new_activities_day: DailyItineraryOutput
        - new_activities_day_modifications_summary: str
        - titulo_dia: str
        - itinerary: ViajeState
    """

    user_feedback = interrupt(  
        f"Se van a aplicar las siguientes modificaciones al dia: {new_activities_day_modifications_summary}. "
        "¿Estás de acuerdo? [Si (s)] (Mencionar cambios si no estas de acuerdo)"
    )

    user_feedback = user_feedback["messages"].lower()

    print(f"====\n \n User feedback: {user_feedback} \n ====")

    if user_feedback == "s" or user_feedback == "si":

        new_itinerary = update_activities_day(itinerary.model_dump(), new_activities_day.model_dump(), titulo_dia)

        print(f"====\n \n New itinerary: {new_itinerary} \n ====")

        if not new_itinerary:
            return Command(update={
                "messages": [
                    ToolMessage(
                        "Error updating activities in the itinerary",
                        tool_call_id=tool_call_id
                    )
                ]
            })

        return Command(update={
            "itinerary": new_itinerary,
            # update the message history
            "messages": [
                ToolMessage(
                    "Successfully applied itinerary modifications",
                    tool_call_id=tool_call_id
                )
            ]
        }) 
    
    else:
        return Command(update={
            "messages": [
                ToolMessage(
                    f"El usuario no aceptó las modificaciones al itinerario, esta fue su respuesta: {user_feedback}",
                    tool_call_id=tool_call_id
                )
            ]
        })

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

# tools = [replace_string_in_itinerary, web_search]
tools = [web_search, modify_activities]


# ==== Create agents ====
activities_chat_agent = create_react_agent(
    model,
    tools=tools,
    prompt=prompt,
    checkpointer=checkpointer,
    state_schema=CustomState,
    # pre_model_hook=summarization_node, 
)
