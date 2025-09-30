from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt
import time
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from pydantic import Field


# class CityDay(TypedDict):
#     city: str = Field(..., description="Ciudad")
#     days: int = Field(..., description="Cantidad de dias en la ciudad")

class CitiesDayStructured(TypedDict):
    cities_day: dict[str, int] = Field(..., description="Ciudades y cantidad dedias para un viaje")
    cities_alternative: list[str] = Field(..., description="Ciudades alternativas para visitar en el viaje")

model = ChatOpenAI(model="gpt-5-mini")
model_structured = model.with_structured_output(CitiesDayStructured)

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


def get_cities_and_days_prompt(state: State):
    return [SystemMessage(content=f"""
<System>
Rol: Experto en planificacion de viajes y guia de viajes.
</System>

<Context>
El viaje sera realizado por una familia de 4 personas con 2 hijos de 20 y 22 años.
Su objetivo de viaje es conocer los lugares mas turisicos de la ciudad.
La temporada del viaje es en verano.
Para este viaje quieren tener un ritmo dinamico.
El objetivo del viaje es conocer los lugares mas turisicos.
</Context>

<Input>
{state["query"]}
</Input>

<Instructions>
Sugere ciudades y cantidad de dias para un viaje.
Tene en cuenta las preferencias del viajero.
Sugere ciudades alternativas para visitar en el viaje.
El viajero va a tener la posibilidad de aprovar las ciudades y cantidad de dias que se sugieren. O seleccionar las ciudades alternativas.

{"" if not state["cities_feedback"] else f"El feedback del viajero es: {state["cities_feedback"]}"}
</Instructions>

"""
)]


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
    
    output = model_structured.invoke(get_cities_and_days_prompt(state))
    
    print(f"\n\nOutput: {output}\n\n")
    return {"cities_day": output['cities_day'], "cities_alternative": output['cities_alternative']}

# ========= Feedback nodes ============


def feedback_cities_and_days(state: State):

    user_feedback = interrupt(  
        f"Se sugirieron las siguientes ciudades: {state["cities_day"]}. y las siguientes ciudades alternativas: {state["cities_alternative"]}. "
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