from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model
llm = init_chat_model("openai:gpt-5-nano")


class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    thread_id: str
    feedback: str | None = None
    tmp_itinerary: str
    itinerary: str
    src: str
    messages: Annotated[list, add_messages]


def get_final_itinerary_prompt(state: State):
    PROMPT = f"""
    Eres un experto en planificacion de viajes, el encargado de ajustar el itinerario de viaje en base al feedback de tu supervisor.
    Feedback del supervisor: {state["feedback"]}
    Itinerario de viaje: {state["tmp_itinerary"]}
    Ajusta el itinerario de viaje en base al feedback del supervisor.
    Mantene el formato del itinerario de viaje. Ajustar unicamente los puntos que el supervisor te indique.
    """
    return PROMPT

graph_builder = StateGraph(State)

def itinerary_agent(state: State):
    # return {"messages": [llm.invoke(state["messages"])]}
    src = "../examples/activities_city_Miami_4_bd881ed1-1792-4ffc-9c25-0e44539261c9.md"
    tmp_itinerary = open(src, "r").read()

    if state["feedback"]:
        itinerary = "AJUSTADO"
    else:
        itinerary = tmp_itinerary

    return {"tmp_itinerary": tmp_itinerary, "src": src, "itinerary": itinerary}

def feedback_agent(state: State):
    feedback = "Día 2 podría ser muy intenso: Everglades + kayak + Key Biscayne es muchísimo para un día, especialmente con el calor de verano. Consideraría mover una actividad al día 4."
    return {"feedback": feedback}

def route_response(state: State):
    print("route_response")
    if state["feedback"]:
        print("END")
        return END
    else:
        print("feedback_agent")
        return 'feedback_agent'

# The first argument is the unique node name
# The second argument is the function or object that will be called whenever
# the node is used.

#  Nodes
tool_node = ToolNode(tools=[tool])
graph_builder.add_node("tools", tool_node)
graph_builder.add_node("itinerary_agent", itinerary_agent)
graph_builder.add_node("feedback_agent", feedback_agent)

#  Edges
graph_builder.add_edge(START, "itinerary_agent")
graph_builder.add_conditional_edges("itinerary_agent", 
    route_response,
    {
        "feedback_agent": "feedback_agent",
        END: END
    }
)
graph_builder.add_edge("feedback_agent", "itinerary_agent")

graph = graph_builder.compile()


state = {
    "thread_id": "123",
    "feedback": None
}

print(graph.invoke(state))



# def stream_graph_updates(user_input: str):
#     for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
#         for value in event.values():
#             print("Assistant:", value["messages"][-1].content)


# while True:
#     try:
#         user_input = input("User: ")
#         if user_input.lower() in ["quit", "exit", "q"]:
#             print("Goodbye!")
#             break
#         stream_graph_updates(user_input)
#     except:
#         # fallback if input() is not available
#         user_input = "What do you know about LangGraph?"
#         print("User: " + user_input)
#         stream_graph_updates(user_input)
#         break