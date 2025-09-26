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

def continue_to_itineraries(state: State):
    return [Send("generate_itinerary", city) for city in state["cities"]]

graph_builder = StateGraph(State)

graph_builder.add_node("map", map)
graph_builder.add_node("generate_itinerary", generate_itinerary)

graph_builder.add_edge(START, "map")
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