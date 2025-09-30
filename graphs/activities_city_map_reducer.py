from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from langgraph.types import Send
from langgraph.graph import StateGraph, START, END
import operator
import time
from graphs.activities_city import graph as activities_city_graph

class ItineraryState(TypedDict):
    city: str
    days: str
    itinerary: str
    itinerary_resume: str

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    city: str
    days: int
    itineraries: Annotated[list[ItineraryState], operator.add]


def generate_itinerary(state: State):
    time.sleep(3)
    itinerary = ItineraryState(
        city=state["city"], 
        days=state["days"], 
        itinerary=f"Itinerario para {state['city']} durante {state['days']} dias",
        itinerary_resume=f"Resumen del itinerario para {state['city']} durante {state['days']} dias"
    )
    return {"itineraries": [itinerary]}


sub_graph_builder = StateGraph(State)

sub_graph_builder.add_node("generate_itinerary", generate_itinerary)
sub_graph_builder.add_edge(START, "generate_itinerary")
sub_graph_builder.add_edge("generate_itinerary", END)

sub_graph = sub_graph_builder.compile()



class CityState(TypedDict):
    city: str
    days: str


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    itineraries: Annotated[list[ItineraryState], operator.add]
    cities: list[CityState]
    final_itinerary: dict


def map(state: State):
    pass


def reduce(state: State):
    final_itinerary = {}
    for itinerary in state["itineraries"]:
        final_itinerary[itinerary["city"]] = itinerary["itinerary"]
    return {"final_itinerary": final_itinerary}


def continue_to_itineraries(state: State):
    return [Send("generate_itinerary", city) for city in state["cities"]]

graph_builder = StateGraph(State)

graph_builder.add_node("map", map)
graph_builder.add_node("generate_itinerary", generate_itinerary) # Testing
# graph_builder.add_node("generate_itinerary", activities_city_graph)
graph_builder.add_node("reduce", reduce)

graph_builder.add_edge(START, "map")
graph_builder.add_conditional_edges("map", continue_to_itineraries, ["generate_itinerary"])
graph_builder.add_edge("generate_itinerary", "reduce")
graph_builder.add_edge("reduce", END)

graph = graph_builder.compile()

state = {
    "cities": [
        {"city": "Madrid", "days": "3"},
        {"city": "Barcelona", "days": "3"},
        {"city": "Valencia", "days": "3"},
    ]
}

# [{"city": "Madrid", "days": "3"}, {"city": "Paris", "days": "5"}]