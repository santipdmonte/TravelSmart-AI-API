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

from state import ViajeState

from langgraph.types import interrupt


# Define model and checkpointer
model = ChatOpenAI(model="gpt-5-mini")
web_search_model = "gpt-5"
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
    # itinerary: str
    user_name: str
    user_id: str


# ==== Prompt ====
PROMPT = """
Eres un asistente de viajes que ayuda a los usuarios a planificar sus viajes. 
Eres el un experto en ajustar itinerarios de viajes segun las necesidades del usuario.
"""

def prompt(
    state: CustomState
):
    user_name = state["user_name"]
    itinerary = state["itinerary"]
    system_msg = f"{PROMPT} El itinerario actual es: {itinerary}"
    return [{"role": "system", "content": system_msg}] + list(state["messages"])


# ==== Tools ====
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

tools = [apply_itinerary_modifications, web_search]


# ==== Create agents ====
itinerary_agent = create_react_agent(
    model,
    tools=tools,
    prompt=prompt,
    checkpointer=checkpointer,
    state_schema=CustomState,
    # pre_model_hook=summarization_node, 
)
