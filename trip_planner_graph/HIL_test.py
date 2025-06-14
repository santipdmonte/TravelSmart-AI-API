from langgraph.graph import START, END, StateGraph
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver

from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class State(BaseModel):
    itinerary: str
    user_feedback: str

def generate_main_itinerary(state: State):
    """
    Generate itinerary graph example
    """

    print('--- [Generate itinerary] ---')

    state.itinerary = "Ejemplo de itinerario"

    return state

def human_feedback(state: State):
    """
    Human feedback graph example
    """

    print('--- [Human feedback] ---')
    interrupt_message = f"¿Quieres modificar el itinerario? [{state.itinerary} | {state.user_feedback}]"
    print(interrupt_message)
    feedback = interrupt(interrupt_message)
    state.user_feedback = feedback

    return state


def should_continue(state: State):
    """
    Should continue graph example
    """

    print(f'--- [Should continue] | [{state.user_feedback}]---')

    user_feedback = state.user_feedback

    if (isinstance(user_feedback, bool) and user_feedback is False) or (isinstance(user_feedback, str) and user_feedback.lower() == "false"):
        print('--- [END] ---')
        return Command(goto=END)
    
    # Modify Itinerary
    elif isinstance(user_feedback, str):
        return Command(goto="modify_itinerary", update={"user_feedback": user_feedback})
    
    else:
        raise TypeError(f"Interrupt value of type {type(user_feedback)} is not supported.")
    

def modify_itinerary(state: State):
    """
    Modify itinerary graph example
    """

    print('--- [Modify itinerary] ---')

    state.itinerary = "Itinerario Modificado"

    return state

# Add nodes
builder = StateGraph(State)
builder.add_node("generate_main_itinerary", generate_main_itinerary)
builder.add_node("human_feedback", human_feedback)
builder.add_node("modify_itinerary", modify_itinerary)
builder.add_node("should_continue", should_continue)

# Add edges
builder.add_edge(START, "generate_main_itinerary")
builder.add_edge("generate_main_itinerary", "human_feedback")
builder.add_edge("human_feedback", "should_continue")
builder.add_edge("modify_itinerary", "human_feedback")

checkpointer = MemorySaver()

print("--- [Graph] ---")

graph = builder.compile(checkpointer=checkpointer)

