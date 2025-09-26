from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt
import time


class State(TypedDict):
    query: str
    cities_day: dict[str, int]
    cities_day_confirmed: bool
    cities_suggested: list[str]
    cities_feedback: str
    activities: dict[str, list[str]]
    activities_suggested: list[str]
    activities_confirmed: bool
    activities_feedback: str
    total_days: int
    transportation_insights: dict[str, str]
    accommodations_insights: dict[str, str]

# Generate a path as if the input is Europe

def days_in_cities_router(state: State):
    # The user declare an specific days in cities? If not, feedback days in cities
    days_in_cities_confirmed = state["cities_day_confirmed"]

    if days_in_cities_confirmed:
        return "buffer"
    
    return "suggest_cities" 

def activities_router(state: State):
    # The user declare an specific days in cities? If not, feedback days in cities
    activities_confirmed = state["activities_confirmed"]

    if activities_confirmed:
        return "generate_detailed_itinerary"
    
    return "suggest_activities" 

def buffer_router(state: State):
    if len(state['cities_day']) < 2:
        return ["suggest_activities", "generate_accommodation_insights"]
    
    return ["suggest_activities", "generate_transportation_insights", "generate_accommodation_insights"] 

def buffer(state: State):
    pass

def join(state: State):
    pass


# ========= Suggest nodes ============


def suggest_cities(state: State):
    time.sleep(3)
    # LLM that suggests cities for each country
    return {"cities_day": {"Madrid": 3, "Berlin": 3, "Rome": 3, "Madrid": 3}}

def suggest_activities(state: State):
    time.sleep(5)
    # LLM that suggests imperdibles activities for each city (the user select or deselect the activities that want to do)
    return {"activities": {"Madrid": ["Visit the Eiffel Tower", "Visit the Brandenburg Gate", "Visit the Colosseum", "Visit the Prado Museum"], "Berlin": ["Visit the Eiffel Tower", "Visit the Brandenburg Gate", "Visit the Colosseum", "Visit the Prado Museum"], "Rome": ["Visit the Eiffel Tower", "Visit the Brandenburg Gate", "Visit the Colosseum", "Visit the Prado Museum"], "Madrid": ["Visit the Eiffel Tower", "Visit the Brandenburg Gate", "Visit the Colosseum", "Visit the Prado Museum"]}}


# ========= Feedback nodes ============


def feedback_days_in_cities(state: State):

    user_feedback = interrupt(  
        f"Se sugirieron las siguientes ciudades: {state["cities_day"]}. "
        "¿Estás de acuerdo? [Si (s)] (Mencionar cambios si no estas de acuerdo)"
    )

    user_feedback = user_feedback.lower()

    if user_feedback == "s" or user_feedback == "si":
        return {"cities_day_confirmed": True}
    
    return {"cities_day_confirmed": False, "cities_feedback": user_feedback}


def feedback_activities(state: State):

    user_feedback = interrupt(  
        f"Se sugirieron las siguientes actividades: {state["activities"]}. "
        "¿Estás de acuerdo? [Si (s)] (Mencionar cambios si no estas de acuerdo)"
    )

    user_feedback = user_feedback.lower()

    if user_feedback == "s" or user_feedback == "si":
        return {"activities_confirmed": True}
    
    return {"activities_confirmed": False, "activities_feedback": user_feedback}


# ========= Generate nodes ============

def generate_detailed_itinerary(state: State):
    # Agent that generates a detailed itinerary for each city
    activities_dict = {
        "Madrid": ["Visit the Eiffel Tower", "Visit the Brandenburg Gate", "Visit the Colosseum", "Visit the Prado Museum"], 
        "Berlin": ["Visit the Eiffel Tower", "Visit the Brandenburg Gate", "Visit the Colosseum", "Visit the Prado Museum"],
        "Rome": ["Visit the Eiffel Tower", "Visit the Brandenburg Gate", "Visit the Colosseum", "Visit the Prado Museum"], 
        "Madrid": ["Visit the Eiffel Tower", "Visit the Brandenburg Gate", "Visit the Colosseum", "Visit the Prado Museum"]}
    return {"activities": activities_dict}

def generate_transportation_insights(state: State):
    # LLM that suggests transportation for each city connection
    time.sleep(10)
    return {"transportation_insights": {"Madrid - Berlin": "Train", "Berlin - Rome": "Bus", "Rome - Madrid": "Car", "Madrid - Rome": "Plane"}}

def generate_accommodation_insights(state: State):
    # LLM that suggests accommodation for each city
    time.sleep(3)
    return {"accommodations_insights": {"Madrid": "Hotel", "Berlin": "Hostel", "Rome": "Hotel", "Madrid": "Hotel"}}



graph_builder = StateGraph(State)

graph_builder.add_node("suggest_cities", suggest_cities)
graph_builder.add_node("suggest_activities", suggest_activities)
graph_builder.add_node("feedback_days_in_cities", feedback_days_in_cities)
graph_builder.add_node("feedback_activities", feedback_activities)
graph_builder.add_node("generate_detailed_itinerary", generate_detailed_itinerary)
graph_builder.add_node("generate_transportation_insights", generate_transportation_insights)
graph_builder.add_node("generate_accommodation_insights", generate_accommodation_insights)
graph_builder.add_node("buffer", buffer)
graph_builder.add_node("join", join)

graph_builder.add_edge(START, "suggest_cities")
graph_builder.add_edge("suggest_cities", "feedback_days_in_cities")
graph_builder.add_conditional_edges("feedback_days_in_cities", days_in_cities_router, ["suggest_cities", "buffer"])
graph_builder.add_conditional_edges("feedback_activities", activities_router, ["suggest_activities", "generate_detailed_itinerary"])

graph_builder.add_edge("suggest_activities", "feedback_activities")
graph_builder.add_conditional_edges("buffer", buffer_router, ["suggest_activities", "generate_transportation_insights", "generate_accommodation_insights"])
graph_builder.add_edge("generate_accommodation_insights", "join")
graph_builder.add_edge("generate_transportation_insights", "join")
graph_builder.add_edge("generate_detailed_itinerary", "join")
graph_builder.add_edge("join", END)


graph = graph_builder.compile()