from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from langgraph.types import Send
from langgraph.graph import StateGraph, START, END
import operator
import time


class CityState(TypedDict):
    city: str
    days: str

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    itineraries: Annotated[list[str], operator.add]
    cities: list[CityState]
    final_itinerary: str


def map(state: State):
    pass

def generate_itinerary(city: CityState):
    time.sleep(3)
    return {"itineraries": [f"Itinerario para {city['city']} durante {city['days']} dias"]}

def feedback_activities(state: State):

    # user_feedback = interrupt(  
    #     f"Se sugirieron las siguientes actividades: {state["activities"]}. "
    #     "¿Estás de acuerdo? [Si (s)] (Mencionar cambios si no estas de acuerdo)"
    # )

    user_feedback = "si"

    user_feedback = user_feedback.lower()

    if user_feedback == "s" or user_feedback == "si":
        return {"activities_confirmed": True}
    
    return {"activities_confirmed": False, "activities_feedback": user_feedback}


def generate_detailed_itinerary(state: State):
    # Agent that generates a detailed itinerary for each city
    activities_dict = {
        "Madrid": ["Visit the Eiffel Tower", "Visit the Brandenburg Gate", "Visit the Colosseum", "Visit the Prado Museum"], 
        "Berlin": ["Visit the Eiffel Tower", "Visit the Brandenburg Gate", "Visit the Colosseum", "Visit the Prado Museum"],
        "Rome": ["Visit the Eiffel Tower", "Visit the Brandenburg Gate", "Visit the Colosseum", "Visit the Prado Museum"], 
        "Madrid": ["Visit the Eiffel Tower", "Visit the Brandenburg Gate", "Visit the Colosseum", "Visit the Prado Museum"]}
    return {"activities": activities_dict}


def suggest_activities(state: State):
    time.sleep(2)
    # LLM that suggests imperdibles activities for each city (the user select or deselect the activities that want to do)
    return {"activities": {"Madrid": ["Visit the Eiffel Tower", "Visit the Brandenburg Gate", "Visit the Colosseum", "Visit the Prado Museum"], "Berlin": ["Visit the Eiffel Tower", "Visit the Brandenburg Gate", "Visit the Colosseum", "Visit the Prado Museum"], "Rome": ["Visit the Eiffel Tower", "Visit the Brandenburg Gate", "Visit the Colosseum", "Visit the Prado Museum"], "Madrid": ["Visit the Eiffel Tower", "Visit the Brandenburg Gate", "Visit the Colosseum", "Visit the Prado Museum"]}}


def activities_router(state: State):
    # The user declare an specific days in cities? If not, feedback days in cities
    activities_confirmed = state["activities_confirmed"]

    if activities_confirmed:
        return "generate_detailed_itinerary"
    
    return "map" 

def continue_to_itineraries(state: State):
    return [Send("generate_itinerary", city) for city in state["cities"]]

graph_builder = StateGraph(State)

graph_builder.add_node("suggest_activities", suggest_activities)
graph_builder.add_node("feedback_activities", feedback_activities)
graph_builder.add_node("generate_detailed_itinerary", generate_detailed_itinerary)
graph_builder.add_node("map", map)
graph_builder.add_node("generate_itinerary", generate_itinerary)

graph_builder.add_edge(START, "suggest_activities")
graph_builder.add_edge("suggest_activities", "feedback_activities")
graph_builder.add_conditional_edges("feedback_activities", activities_router, ["suggest_activities", "map"])
graph_builder.add_conditional_edges("map", continue_to_itineraries, ["generate_itinerary"])
graph_builder.add_edge("generate_itinerary", END)

graph =graph_builder.compile()

state = {
    "cities": [
        {"city": "Madrid", "days": "3"},
        {"city": "Barcelona", "days": "3"},
        {"city": "Valencia", "days": "3"},
    ]
}

# graph.invoke(state)