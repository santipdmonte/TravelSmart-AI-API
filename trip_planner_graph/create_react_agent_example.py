"""
create_react_agent_example.py
This example shows how to create a react agent with a custom state and tools.
"""

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.config import get_stream_writer
from langgraph.prebuilt.chat_agent_executor import AgentState
from langchain_core.messages import AnyMessage
from typing import Annotated
from langgraph.prebuilt import InjectedState

from langmem.short_term import SummarizationNode
from langchain_core.messages.utils import count_tokens_approximately
from typing import Any

from langchain_core.tools import InjectedToolCallId
from langgraph.types import Command
from langchain_core.messages import ToolMessage


# Define model and checkpointer
model = ChatOpenAI(model="gpt-4o-mini")
checkpointer = MemorySaver()
max_iterations = 3
recursion_limit = 2 * max_iterations + 1
config = {"configurable": {"thread_id": "1"}, "recursion_limit": recursion_limit}


# ==== Custom state ====
summarization_node = SummarizationNode( 
    token_counter=count_tokens_approximately,
    model=model,
    max_tokens=384,
    max_summary_tokens=128,
    output_messages_key="llm_input_messages",
)


class CustomState(AgentState):
    context: dict[str, Any]  # Used to store context of the summarization_node, to prevent the need of summarizing the context in all the runs
    itinerary: str
    user_name: str
    user_id: str


# ==== Prompt ====
PROMPT = """
Eres un asistente de viajes que ayuda a los usuarios a planificar sus viajes.
"""

def prompt(
    state: CustomState
) -> list[AnyMessage]:
    user_name = state["user_name"]
    itinerary = state["itinerary"]
    system_msg = f"{PROMPT} Your itinerary is {itinerary}"
    return [{"role": "system", "content": system_msg}] + state["messages"]


# ==== Tools ====
def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

def get_weather_tool(city: str) -> str:   # With writer you can only call the tool inside langgraph
    """Get weather for a given city."""
    writer = get_stream_writer()
    writer(f"Looking up data for city: {city}")

    return get_weather(city)

def get_user_info(
    state: Annotated[CustomState, InjectedState]
) -> str:
    """Look up user info."""
    user_id = state["user_id"]
    return "User is Juan" if user_id == "user_123" else "Unknown user"

def update_user_info(
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[CustomState, InjectedState]
) -> Command:
    """Look up and update user info."""
    user_id = state["user_id"]
    name = "John Smith" if user_id == "user_123" else "Unknown user"
    return Command(update={
        "user_name": name,
        # update the message history
        "messages": [
            ToolMessage(
                "Successfully looked up user information",
                tool_call_id=tool_call_id
            )
        ]
    })

tools = [get_weather, get_user_info, update_user_info]


# ==== Create agents ====
agent = create_react_agent(
    model,
    tools=tools,
    prompt=prompt,
    checkpointer=checkpointer,
    state_schema=CustomState,
    pre_model_hook=summarization_node, 
)

# ==== Invoke agent ====s
initial_state = {
    "itinerary": "Viaje a la playa",
    "user_name": "Juan",
    "user_id": "user_123",
    "messages": [{"role": "user", "content": "Quiero que mi itinerario ahora sea 'Viaje a la montaña'"}]
}

response = agent.invoke(
    initial_state,
    config=config,
)

print(response)