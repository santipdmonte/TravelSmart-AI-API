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

from langgraph.types import interrupt


from utils.llm import llm, llm_cheap

# Define model and checkpointer
model = ChatOpenAI(model="gpt-4o")
# model = llm
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
- Puedes usar la herramienta apply_itinerary_modifications para hacer modificaciones al itinerario.
</Instructions>

<Tools>
Usa la herramienta apply_itinerary_modifications para modificar el itinerario. Con esta herramienta puedes aplicar modificaciones al itinerario.
</Tools>

"""

# ==== Memory Notes ====
"""

- Si el cliente te hace una aclaracion que consideres importante. Puedes usar la herramienta add_memory_notes para agregar las notas a la memoria del usuario o del itinerario.

Cuando el usuario te hace una aclaracion que consideres importante. Puedes usar la herramienta add_memory_notes para agregar las notas a la memoria del usuario o del itinerario.
La memoria del usuario persitira para los diferentes itinerarios.
La memoria del itinerario solo persitira para este itinerario en particular.
Las preferencias generales del usuario guardalas como memoria del usuario, las preferencias puntuales para este viaje guardalas como memoria del itinerario.
"""

def prompt(
    state: CustomState
):
    itinerary = state["itinerary"]
    system_msg = f"{PROMPT} El itinerario actual es: {itinerary}"
    return [{"role": "system", "content": system_msg}] + list(state["messages"])


# ==== Tools ====
# def replace_string_in_itinerary(
#     string_to_replace: str = Field(..., description="The text to replace (must be a string that matches exactly, including whitespace and indentation)"),
#     new_string: str = Field(..., description="The new text to insert in place of the old text"),
#     itinerary: Annotated[ViajeState | None, InjectedState("itinerary")] = None,
# ):
#     """
#     Reemplaza un string exacto en el itinerario. Debe ser un string que coincida exactamente, incluyendo espacios y sangría.
#     Con esta herramienta puedes agregar, modificar o quitar elementos del itinerario. Debes asegurarte de que la estructura JSON del itinerario quede correcta.
#     """
#     print(f"====\n \n string_to_replace: {string_to_replace} \n new_string: {new_string} \n ====")
#     itinerary_str = itinerary.model_dump_json()
#     count = itinerary_str.count(string_to_replace)
#     if count == 0:
#         return f"The string to replace was not found in the itinerary."
#     if count > 1:
#         return f"The string to replace was found in the itinerary {count} times. It must be replaced only once."
    
#     itinerary_str = itinerary_str.replace(string_to_replace, new_string)
#     itinerary = ViajeState.model_validate_json(itinerary_str)
#     return {"itinerary": itinerary}

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

def apply_itinerary_modifications(
    tool_call_id: Annotated[str, InjectedToolCallId],
    new_itinerary: ViajeState,
    #new_itinerary: str,
    new_itinerary_modifications_summary: str,
    # Itinerary: ItineraryState
) :
    """
    Modify the itinerary.
    
    input:
        - new_itinerary: ViajeState
        - new_itinerary_modifications_summary: str
    """

    user_feedback = interrupt(  
        f"Se van a aplicar las siguientes modificaciones al itinerario: {new_itinerary_modifications_summary}. "
        "¿Estás de acuerdo? [Si (s)] (Mencionar cambios si no estas de acuerdo)"
    )

    user_feedback = user_feedback["messages"].lower()

    print(f"====\n \n User feedback: {user_feedback} \n ====")

    if user_feedback == "s" or user_feedback == "si":
        # TODO: Apply the modifications to the itinerary in the DB

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
tools = [web_search, apply_itinerary_modifications]


# ==== Create agents ====
itinerary_agent = create_react_agent(
    model,
    tools=tools,
    prompt=prompt,
    checkpointer=checkpointer,
    state_schema=CustomState,
    # pre_model_hook=summarization_node, 
)
