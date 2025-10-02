from typing import Annotated
import uuid

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, AnyMessage, ToolMessage
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_community.tools import TavilySearchResults
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import BaseModel, Field
from tools.geocoding_tool import batch_geocode_attractions
from tools.wikipedia_tool import batch_get_wikipedia_images

from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model


class AttractionsData (BaseModel):
    attraction: str = Field(..., description="Atracción")
    latitude: float = Field(..., description="Latitud")
    longitude: float = Field(..., description="Longitud")
    full_address: str = Field(..., description="Dirección")
    images: list[str] = Field(..., description="Imágenes")

class ItineraryDaily(BaseModel):
    itinerary: str = Field(..., description="Itinerario diario completo")
    itinerary_resume: str = Field(..., description="Resumen del itinerario diario")
    attractions_list: list[str] = Field(..., description="Lista de atracciones")

class ItineraryState(TypedDict):
    city: str
    country: str
    days: str
    itinerary: str
    itinerary_resume: str
    attractions_data: dict[str, AttractionsData]

class State(TypedDict):
    city: str
    country: str
    days: int
    feedback: str | None = None
    tmp_itinerary: str | None = None
    final_itinerary: str | None = None
    attractions_list: list[str] | None = None
    itineraries: list[ItineraryState]
    tool_calling: bool = False
    messages: Annotated[list[AnyMessage], add_messages]


# ## 1) Datos necesarios (Rellenar antes de la corrección)
# - Fecha y hora de llegada (ej.: 2025-06-10 09:30) (si aplica)
# - Fecha y hora de salida (ej.: 2025-06-15 21:00) (si aplica)
# - Medios de transporte entre destinos (vuelo/tren/bus/coche) y horarios si ya los tienes  
# - Duración prevista en cada lugar y alojamiento reservado (nombre, dirección, check-in / check-out)  
# - Prioridades / intereses (marca todos los que apliquen: museos, naturaleza, gastronomía, playa, compras, vida nocturna, senderismo, descanso)  
# - Número de viajeros y si hay niños/personas con movilidad reducida  
# - Presupuesto aproximado por persona (si aplica)  
# - Restricciones alimentarias o de salud relevantes

OUTPUT_TEMPLATE = """

### Formato de salida por día

**Día X – Breve resumen del día**  

- **Mañana**  
  - *Actividad [Nombre o enlace]:
    - Descripción: breve descripción de la actividad  
    - Horarios: apertura/cierre o mejor rango del día (si aplica)
    - Precio: (aproximado / descuentos / gratuidades) (si aplica)
    - Duración sugerida: (ej. 1–2h / medio día / día completo)  
    - Reserva: (link de reserva o “no requiere”)  
    - Ubicación: (dirección / barrio / zona)  
    - Transporte recomendado: (tiempo estimado / medio desde centro o actividad previa)  

- **Tarde**  
  - *Actividad 2*: [Nombre o enlace]  
    - (mismos subcampos)  

- **Noche**  
  - *Actividad 3* (cena / espectáculo / paseo nocturno)  
    - (mismos subcampos)  

- **Notas del día**: tips extra (p. ej. dejar margen entre actividades, recomendaciones de comida local, recordatorio de reservas).  

---

### Extras fuera del itinerario
- Otras actividades interesantes no incluidas
- Recomendaciones prácticas y consejos útiles (transporte local, seguridad, apps, costumbres)

"""

ADDITIONAL_CONTEXT = """
El viaje sera realizado por una familia de 4 personas con 2 hijos de 20 y 22 años.
Su objetivo de viaje es conocer los lugares mas turisicos de la ciudad.
La temporada del viaje es en verano.
Para este viaje quieren tener un ritmo dinamico.
"""

def get_itinerary_prompt(state: State):
    return [SystemMessage(content=f"""
<System>
Rol: Experto en planificacion de viajes y guia de viajes.
</System>

<Context>
Tu objetivo es generar un itinerario útil para realizar en {state["city"]} durante {state["days"]} días.
{ADDITIONAL_CONTEXT}
</Context>

<Instructions>
📌 Consideraciones clave:
- Crea un itinerario de viaje detallado para cada dia.
- El primer día suele tener menos tiempo disponible por la llegada a la ciudad.
- Separa las actividades según el **momento del día recomendado** (mañana, tarde, noche). 
- No uses horarios exactos, solo menciona **rangos de apertura o cierre** si son importantes.
- Para cada actividad incluye: breve descripción, precios aproximados, duración sugerida, requisitos de reserva y ubicación.
- Incluye el **mejor transporte recomendado** desde el centro o desde la actividad previa.
- Agrupa actividades cercanas en el mismo día para optimizar desplazamientos.
- Indica si hay que reservar con antelación e incluye enlaces cuando corresponda.
- Fuera de la planificación diaria, menciona otras actividades interesantes que no entraron en el itinerario.
- Añade recomendaciones útiles del destino (transporte local, seguridad, apps, costumbres).
- Usa un lenguaje neutro / latinoamericano.
- La respuesta final debe ser solo el itinerario, sin explicaciones adicionales.
- La respuesta debe ser en formato markdown.

Tienes un límite de {(int(state["days"]) * 2) + 2} búsquedas web. Planifica las búsquedas y ejecútalas todas al mismo tiempo para obtener la información relevante.
</Instructions>

{OUTPUT_TEMPLATE}

<Reasoning>
Objetivo: generar un itinerario práctico y accionable para {state["city"]} durante {state["days"]} días, tomando en cuenta las preferencias y restricciones.

Supuestos principales:
- Si existe arrival_datetime/ departure_datetime, ajustar primer y último día (primer día más corto si la llegada es tarde).
- Idioma de salida: español (neutro / latinoamericano).
- Priorizar fuentes oficiales (sitios de atracciones, oficinas de turismo, operadores) para horarios, precios y reservas. Si no hay datos oficiales, usar fuentes secundarias y marcar como estimado.
- No incluir actividades ilegales o peligrosas; indicar recomendaciones de seguridad genéricas.

Heurística de planificación diaria:
1. Agrupar actividades por **zona/barrio** para minimizar desplazamientos.
2. Día 1: plan más liviano para acomodación/llegadas.
3. Para cada actividad devolver: descripción breve, horarios (rango o abrir/cerrar), precio aproximado (rango), duración sugerida, requisito de reserva (sí/no + link), ubicación (dirección/barrio), transporte recomendado y accesibilidad.

Plan de búsquedas (usar hasta N búsquedas; priorizar en este orden):
1. Sitio oficial de turismo de {state["city"]} / oficina de turismo municipal.
2. Horarios y precios actualizados (sitios oficiales o páginas de venta autorizada).

Reglas de verificación y fuentes:
- Si dos fuentes confiables discrepan >15% en precio o horario, marcar ambos y recomendar confirmar en el sitio oficial.
- Incluir máximo 1–2 enlaces por actividad (preferir enlace de reserva o página oficial).
- Citar/registrar la fuente más relevante para cada dato clave (horario/precio/reserva).

Salida / restricciones:
- La respuesta final debe ser **solo** el itinerario en markdown según OUTPUT_TEMPLATE.
- No usar horarios exactos; solo rangos de apertura/cierre cuando sea relevante.
- Añadir al final sección “Extras fuera del itinerario” y “Recomendaciones prácticas” (transporte, seguridad, apps).
- Si no hay resultados fiables para una actividad, marcar “información no verificada — confirmar en sitio oficial”.

Limitaciones y fallbacks:
- Si se alcanza el límite de búsquedas antes de cubrir todos los elementos, priorizar: 1) imperdibles de cada día, 2) reservas necesarias, 3) transporte entre actividades; y marcar lo que quedó como “verificar”.
- No incluir enlaces no oficiales para reservas de tours o entradas (evitar revendedores).
</Reasoning>


""")]

def get_feedback_fixer_prompt(state: State):
    return [SystemMessage(content=f"""
Eres un asistente de viajes con 15 años de experiencia que ayuda a los usuarios a planificar actividades en su viaje. 

Feedback: 
<feedback>
{state["feedback"]}
</feedback>

Ajusta el itinerario de viaje en base al feedback dado.
Mantene el formato del itinerario de viaje. Ajustar unicamente los puntos que se mencionan en el feedback. Mantener links de las actividades.

📌 Consideraciones clave:
- El primer día suele tener menos tiempo disponible por la llegada a la ciudad.
- Separa las actividades según el **momento del día recomendado** (mañana, tarde, noche). 
- No uses horarios exactos, solo menciona **rangos de apertura o cierre** si son importantes.
- Para cada actividad incluye: breve descripción, precios aproximados, duración sugerida, requisitos de reserva y ubicación.
- Incluye el **mejor transporte recomendado** desde el centro o desde la actividad previa.
- Agrupa actividades cercanas en el mismo día para optimizar desplazamientos.
- Indica si hay que reservar con antelación e incluye enlaces cuando corresponda.
- Fuera de la planificación diaria, menciona otras actividades interesantes que no entraron en el itinerario.
- Añade recomendaciones útiles del destino (transporte local, seguridad, apps, costumbres).
- Usa un lenguaje neutro / latinoamericano.
- La respuesta final debe ser solo el itinerario, sin explicaciones adicionales.
- La respuesta debe ser en formato markdown.

El itinerario debe mantener exactamente el mismo formato, modificando unicamente los puntos que el supervisor te indique.
No agregues ningun otro texto adicional. Tu respuesta sera utilizada directamente en el itinerario final de viaje.
Responde en formato markdown.

<Itinerario de viaje>
{state["tmp_itinerary"]}
</Itinerario de viaje>

{OUTPUT_TEMPLATE}
""")]

def get_feedback_provider_prompt(itinerary: str):
    return [SystemMessage(content=f"""
    Eres un experto en planificacion de viajes, el encargado de proporcionar feedback sobre el itinerario de viaje.
    Considera el contexto adicional:
    {ADDITIONAL_CONTEXT}

    <Itinerario de viaje>
    {itinerary}
    </Itinerario de viaje>

    Provee feedback sobre el itinerario de viaje.
    El feedback se debe enfocar en las cosas a ajustar en el itinerario.
    El feedback debe ser puntual y específico. Las cosas que no sean relevantes para el itinerario no las menciones.
    Mencionar unicamente los cambios sugeridos. Las cosas que esten bien del itinerario no las menciones.
    Si consideras que el itinerario es perfecto, no sugieras cambios.
    Si unicamente econtras 1 cosa a mejorar, sugeri solo ese cambio.
    Evita hacer sugerencias innecesarias.
    """)]


# Nodes

def web_search_planner(state: State):
    print("\n\nweb_search_planner\n\n")

    response = llm_with_tools.invoke(get_itinerary_prompt(state))

    return {"messages": [response]}


def initial_itinerary_agent(state: State):
    print("\n\ninitial_itinerary_agent\n\n")
    thread_id = config["configurable"]["thread_id"]

    response = llm.invoke(get_itinerary_prompt(state) + state["messages"])

    city = state["city"]
    days = state["days"]
    with open(f"examples/activities_city_{city}_{days}_{thread_id}_tmp.md", "w") as f:
        f.write(response.content)

    return {"tmp_itinerary": response.content}


def feedback_provider_agent(state: State):
    print("\n\nfeedback_provider_agent\n\n")
    response = llm.invoke(get_feedback_provider_prompt(state["tmp_itinerary"]))
    city = state["city"]
    days = state["days"]
    thread_id = config["configurable"]["thread_id"]
    with open(f"examples/activities_city_{city}_{days}_{thread_id}_feedback.md", "w") as f:
        f.write(response.content)

    return {"feedback": response.content}


def feedback_fixer_agent(state: State):
    print("\n\nfeedback_fixer_agent\n\n")
    llm_structured = llm.with_structured_output(ItineraryDaily)
    response = llm_structured.invoke(get_feedback_fixer_prompt(state))
    city = state["city"]
    days = state["days"]
    thread_id = config["configurable"]["thread_id"]
    with open(f"examples/attractions_city_{city}_{days}_{thread_id}_final.md", "w") as f:
        f.write(response.itinerary)

    itinerary = ItineraryState(
        city=city,
        days=days,
        itinerary=response.itinerary,
        itinerary_resume=response.itinerary_resume
    )

    return {
        "final_itinerary": response.itinerary, 
        "final_itinerary_resume": response.itinerary_resume,
        "attractions_list": response.attractions_list,
        "itineraries": [itinerary]
    }

def itinerary_attractions_data():#state: State):
    print("\n\nitinerary_attractions_data\n\n")

    # attractions_list = state["attractions_list"]
    # country = state["country"]
    country = "FR"
    attractions_list = ["Torre Eiffel", "Louvre Museum", "Arc de Triomphe"]
    
    # Get coordinates of each attraction
    attractions_data = batch_geocode_attractions(
        attractions=attractions_list,
        country=country
    )

    # print(attractions_data)

    # Get images of each attraction
    attractions_images = batch_get_wikipedia_images(
        queries=attractions_list,
        language="en",
        max_images_per_query=2
    )

    # print(attractions_images)

    # Combine both dictionaries
    attractions_complete_data = {}
    for attraction_name in attractions_list:
        attractions_complete_data[attraction_name] = {
            **attractions_data.get(attraction_name, {}),
            **attractions_images.get(attraction_name, {})
        }
    
    print("\n\nCombined attractions data:\n")
    print(attractions_complete_data)

    # return {"attractions_data": attractions_complete_data}



def web_search(query: str):
    """
    Search the web for the query.
    """

    # Search
    tavily_search = TavilySearchResults(
        max_results=2,
        topic="general",
    )
    search_results = tavily_search.invoke(query)

    # Format
    formatted_results = "\n\n -- \n\n".join(
        [
            f"<Document href='{doc['url']}'/>\n{doc['content']}</Document>" 
            for doc in search_results
        ]
    )

    return {"messages": [formatted_results]}

#  Nodes
tools = [web_search]
tool_node = ToolNode(tools=tools)

graph_builder = StateGraph(State)

#  Nodes
graph_builder.add_node("tools", tool_node)
graph_builder.add_node("web_search_planner", web_search_planner)
graph_builder.add_node("initial_itinerary_agent", initial_itinerary_agent)
graph_builder.add_node("feedback_provider_agent", feedback_provider_agent)
graph_builder.add_node("feedback_fixer_agent", feedback_fixer_agent)
#  Edges
graph_builder.add_edge(START, "web_search_planner")
graph_builder.add_edge("web_search_planner", "tools")
graph_builder.add_edge("tools", "initial_itinerary_agent")
graph_builder.add_edge("initial_itinerary_agent", "feedback_provider_agent")
graph_builder.add_edge("feedback_provider_agent", "feedback_fixer_agent")
graph_builder.add_edge("feedback_fixer_agent", END)

llm = init_chat_model("openai:gpt-5-mini")
llm_with_tools = llm.bind_tools(tools)
memory = InMemorySaver()

# graph = graph_builder.compile(checkpointer=memory)
graph = graph_builder.compile()


state = {
    "feedback": None,
    "city": "Amsterdam",
    "days": 3
}

config = {"configurable": {"thread_id": str(uuid.uuid4())}}

# print(graph.invoke(state, config))


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


# if __name__ == "__main__":
#     # Ejecuta los ejemplos que quieras:
    
#     # example_basic_search()
#     # example_spanish_search()
#     # example_multiple_results()
#     itinerary_attractions_data()
#     # example_itinerary_enrichment()
#     # example_multi_language()