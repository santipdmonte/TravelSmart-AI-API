from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command

checkpointer = MemorySaver()

class OutputState(TypedDict):
    state: str

class OverallState(TypedDict):
    state: str
    document_path: str
    action_suggestion: str
    type_action: str
    user_feedback: str


def process_document(state: OverallState):

    print(f"process_document: {state}")

    if state["user_feedback"] != "":
        state = {
            "state": "process_document",
            "document_path": state["document_path"],
            "type_action": "generate",
            "action_suggestion": "generate the itinerary, lore ipsum",
            "user_feedback": ""
        }    

        return state

    state = {
        "state": "process_document",
        "document_path": state["document_path"],
        "type_action": "save",
        "action_suggestion": "save the docuement, lore ipsum",
        "user_feedback": ""
    }

    return state


def HIL_feedback(state: OverallState):

    print(f"HIL_feedback: {state}")

    user_feedback = interrupt(  
        f"{state["action_suggestion"]}. " # Mostar los cambios a modificar
        "¿Estás de acuerdo? [Si (s)] (Mencionar cambios si no estas de acuerdo)"
    )

    user_feedback_message = user_feedback["messages"].lower()

    if user_feedback_message in ["si", "s"]:

        if state["type_action"] == "save":
            return Command(goto="save_document")
        elif state["type_action"] == "generate":
            return Command(goto="generate_itinerary")
        
    state = {
        "state": "HIL_feedback",
        "document_path": state["document_path"],
        "action_suggestion": state["action_suggestion"],
        "type_action": state["type_action"],
        "user_feedback": user_feedback_message
    }

    return Command(goto="process_document", update=state)


def save_document(state: OverallState):

    # Logica de guardado de documento
    print(f"save_document: {state['document_path']}")

    return Command(goto=END)

def generate_itinerary(state: OverallState):
    # Logica de generacion de itinerario
    print(f"generate_itinerary: {state['action_suggestion']}")
    # Se lo tendriamos que pasar a un modelo que genere el itinerario

    return Command(goto=END)

builder = StateGraph(OverallState)
builder.add_node("process_document", process_document)
builder.add_node("HIL_feedback", HIL_feedback)
builder.add_node("save_document", save_document)
builder.add_node("generate_itinerary", generate_itinerary)

builder.add_edge(START, "process_document")
builder.add_edge("process_document", "HIL_feedback")

config = {"configurable": {"thread_id": "1"}}
graph = builder.compile(checkpointer=checkpointer)


