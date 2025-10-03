from langchain_core.messages import SystemMessage, HumanMessage
from typing import Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from typing_extensions import TypedDict
from graphs.activities_city import OUTPUT_TEMPLATE
from tools.web_search import web_search
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from pydantic import Field, BaseModel

from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    temperature=0.4,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

from dotenv import load_dotenv
load_dotenv()

class ActivityItineraryOutput(BaseModel):
    titulo: str = Field(..., description="El titulo o nombre de la actividad propuesta")
    descripcion: str = Field(..., description="La descripcion de la actividad (breve)")
    horarios: str = Field(description="Los horarios de la actividad (rango o abrir/cerrar o recomendaciones)")
    precio: str = Field(description="El precio de la actividad (aproximar si aplica)")
    requisitos_reserva: str = Field(description="Los requisitos de reserva de la actividad (si aplica)")
    enlace: str = Field(description="El enlace de la actividad (link de reserva o página oficial, evitar enlaces no oficiales)(si aplica)")
    ubicacion: str = Field(description="La ubicacion de la actividad (dirección / barrio / zona)")
    transporte_recomendado: str = Field(description="El transporte recomendado para la actividad desde la actividad previa")

# Structured output
class DailyItineraryOutput(BaseModel):
    dia: str = Field(..., description="El dia del itinerario (1, 2, 3, etc.)")
    ciudad: str = Field(..., description="La ciudad del dia correspondiente")
    pais: str = Field(..., description="El pais del dia correspondiente")
    titulo: str = Field(..., description="Titulo del dia correspondiente. 'Dia X - <Ciudad>: <Breve titulo del dia>'")
    actividades_mañana: list[ActivityItineraryOutput] = Field(description="Lista de actividades para la mañana (si aplica)")
    actividades_tarde: list[ActivityItineraryOutput] = Field(..., description="Lista de actividades para la tarde")
    actividades_noche: list[ActivityItineraryOutput] = Field(description="Lista de actividades para la noche (si aplica)")
    # notas_dia: str = Field(description="Notas del dia correspondiente")

class ItineraryOutput(BaseModel):
    itinerario_diario: list[DailyItineraryOutput] = Field(..., description="Lista con el itinerario diario completo de cada dia")
    resumen_itinerario: str = Field(..., description="Resumen del itinerario")
    recomendaciones_generales: str = Field(..., description="Recomendaciones generales para el viaje")
    actividades_extras: str = Field(..., description="Actividades no incluidas en el itinerario, que le pueden interesar al usuario")


class CityState(TypedDict):
    city: str
    days: str

class ItinerariesState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    itinerary_metadata: dict
    cities: list[CityState]
    final_itinerary: ItineraryOutput


def get_itinerary_prompt(state: ItinerariesState):
    print(f"\n\nstate['cities']: {state['cities']}\n\n")
    return [
        SystemMessage(content=f"""
<System>
Rol: Experto en planificacion de viajes y guia de viajes.
</System>

<Instructions>
📌 Consideraciones clave:
- Crea un itinerario de viaje detallado para cada dia.
- El primer día suele tener menos tiempo disponible por la llegada a la ciudad. 
- Las mañanas de los dias de cambio de destino, sugeri actividades livianas y flexibles en base a la hora de llegada y chekin del alojamiento.
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

</Instructions>

{OUTPUT_TEMPLATE}

<Reasoning>
Objetivo: generar un itinerario práctico y accionable tomando en cuenta las preferencias y restricciones.

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
1. Sitio oficial de turismo de las ciudades / oficina de turismo municipal.
2. Horarios y precios actualizados (sitios oficiales o páginas de venta autorizada).

Reglas de verificación y fuentes:
- Si dos fuentes confiables discrepan >15% en precio o horario, marcar ambos y recomendar confirmar en el sitio oficial.
- Incluir máximo 1–2 enlaces por actividad (preferir enlace de reserva o página oficial).
- Citar/registrar la fuente más relevante para cada dato clave (horario/precio/reserva).

Salida / restricciones:
- La respuesta final debe ser **solo** el itinerario en markdown.
- No usar horarios exactos; solo rangos de apertura/cierre cuando sea relevante.
- Añadir al final sección "Extras fuera del itinerario" y "Recomendaciones prácticas" (transporte, seguridad, apps).
- Si no hay resultados fiables para una actividad, marcar "información no verificada — confirmar en sitio oficial".

Limitaciones y fallbacks:
- No incluir enlaces no oficiales para reservas de tours o entradas (evitar revendedores).
</Reasoning>
"""),
        HumanMessage(content=f"""
Las ciudades del viaje son:
{f"\n".join([f"  - {city['city']} ({city['days']} días)" for city in state['cities']])}

Las preferencias del usuario son:
{f"\n".join([f"  - {key}: {value}" for key, value in state['itinerary_metadata'].items() if value])}
""")
    ]



"""

- city: Sydney
  days: "4"
- city: Queenstown
  days: "4"
- city: Auckland
  days: "4"

when: verano
trip_type: pareja
city_view: turista
budget: confort
travel_pace: activo


"""
    
    

def web_search_planner(state: ItinerariesState):
    return {"messages": [llm_with_tools.invoke(get_itinerary_prompt(state))]}


def generate_itineraries(state: ItinerariesState):
    result = llm_structured.invoke(get_itinerary_prompt(state) + state["messages"])
    return {"final_itinerary": result}



llm_structured = llm.with_structured_output(ItineraryOutput)
llm_with_tools = llm.bind_tools([web_search])

# Tool node
tools = [web_search]
tool_node = ToolNode(tools=tools)

# Nodes
graph_builder = StateGraph(ItinerariesState)
graph_builder.add_node("tools", tool_node)
graph_builder.add_node("web_search_planner", web_search_planner)
graph_builder.add_node("generate_itineraries", generate_itineraries)

# Edges
# graph_builder.add_edge(START, "web_search_planner")
# graph_builder.add_edge("web_search_planner", "tools")
# graph_builder.add_edge("tools", "generate_itineraries")
graph_builder.add_edge(START, "generate_itineraries")
graph_builder.add_edge("generate_itineraries", END)

graph = graph_builder.compile()