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

def cities_and_days_router(state: State):
    # The user declare an specific days in cities? If not, feedback days in cities
    cities_and_days_confirmed = state["cities_day_confirmed"]

    if cities_and_days_confirmed:
        return "buffer"
    
    return "suggest_cities_and_days" 

def buffer_router(state: State):
    if len(state['cities_day']) < 2:
        return ["generate_accommodation_insights"]
    
    return ["generate_transportation_insights", "generate_accommodation_insights"] 

def buffer(state: State):
    pass

def join(state: State):
    pass


# ========= Suggest nodes ============


def suggest_cities_and_days(state: State):
    time.sleep(3)
    # LLM that suggests cities for each country
    return {"cities_day": {"Madrid": 3, "Berlin": 3, "Rome": 3, "Madrid": 3}}

# ========= Feedback nodes ============


def feedback_cities_and_days(state: State):

    user_feedback = interrupt(  
        f"Se sugirieron las siguientes ciudades: {state["cities_day"]}. "
        "¿Estás de acuerdo? [Si (s)] (Mencionar cambios si no estas de acuerdo)"
    )

    user_feedback = user_feedback.lower()

    if user_feedback == "s" or user_feedback == "si":
        return {"cities_day_confirmed": True}
    
    return {"cities_day_confirmed": False, "cities_feedback": user_feedback}



# ========= Generate nodes ============

def generate_transportation_insights(state: State):
    # LLM that suggests transportation for each city connection
    time.sleep(10)
    return {"transportation_insights": {"Madrid - Berlin": "Train", "Berlin - Rome": "Bus", "Rome - Madrid": "Car", "Madrid - Rome": "Plane"}}

def generate_accommodation_insights(state: State):
    # LLM that suggests accommodation for each city
    time.sleep(3)
    return {"accommodations_insights": {"Madrid": "Hotel", "Berlin": "Hostel", "Rome": "Hotel", "Madrid": "Hotel"}}



graph_builder = StateGraph(State)

graph_builder.add_node("suggest_cities_and_days", suggest_cities_and_days)
graph_builder.add_node("feedback_cities_and_days", feedback_cities_and_days)
graph_builder.add_node("generate_transportation_insights", generate_transportation_insights)
graph_builder.add_node("generate_accommodation_insights", generate_accommodation_insights)
graph_builder.add_node("buffer", buffer)
graph_builder.add_node("join", join)

graph_builder.add_edge(START, "suggest_cities_and_days")
graph_builder.add_edge("suggest_cities_and_days", "feedback_cities_and_days")
graph_builder.add_conditional_edges("feedback_cities_and_days", cities_and_days_router, ["suggest_cities_and_days", "buffer"])

graph_builder.add_conditional_edges("buffer", buffer_router, ["generate_transportation_insights", "generate_accommodation_insights"])
graph_builder.add_edge("generate_accommodation_insights", "join")
graph_builder.add_edge("generate_transportation_insights", "join")
graph_builder.add_edge("join", END)


graph = graph_builder.compile()