"""
agent_planner_graph.py
This graph is used to create a react agent with a custom state and tools.
"""

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.prebuilt import InjectedState
from pydantic import Field
from langchain_core.messages import AnyMessage
from typing import Annotated, Any
from enum import Enum

from langmem.short_term import SummarizationNode
from langchain_core.messages.utils import count_tokens_approximately
from langchain_core.tools import InjectedToolCallId
from langgraph.types import Command
from langchain_core.messages import ToolMessage

from states.itinerary import ViajeState

from langgraph.types import interrupt

# Define model and checkpointer
model = ChatOpenAI(model="gpt-4o")
# model = llm
web_search_model = "gpt-5-mini"
checkpointer = MemorySaver()

# ==== Custom state ====
summarization_node = SummarizationNode( 
    token_counter=count_tokens_approximately,
    model=model,
    max_tokens=1500,
    max_summary_tokens=500,
    output_messages_key="llm_input_messages",
)


class CustomState(AgentState):
    context: dict[str, Any]  # Used to store context of the summarization_node, to prevent the need of summarizing the context in all the runs
    itinerary: ViajeState

# ==== Prompt ====
PROMPT = """
<Rol>
Eres un asistente de viajes experto especializado en modificar **actividades diarias** de itinerarios.
Tienes un tono colaborativo, personal y agradable, pero eres estricto con tus limitaciones.
</Rol>

<Context>
El usuario ya ha CONFIRMADO su ruta principal (destinos, ciudades, duración y transporte entre ciudades).
Ahora solo estás autorizado para ayudarlo a ajustar los detalles de su plan de actividades diarias.
El itinerario de actividades actual está disponible en el estado del sistema.
</Context>

<Instructions>
1. Responde las dudas del cliente sobre sus actividades de forma clara y concisa.
2. Puedes usar la herramienta `web_search` para buscar información actualizada (restaurantes, horarios de museos, eventos, etc.).
3. Puedes usar la herramienta `modify_activities` para aplicar cambios en las actividades diarias.
</Instructions>

<Tools>
- **web_search**: Busca información en tiempo real para ayudar al usuario con recomendaciones de actividades.
- **modify_activities**: Modifica las actividades diarias del itinerario. 
  - Input: `new_itinerary` (ViajeState completo con las modificaciones en itinerario_diario aplicadas)
  - Input: `new_itinerary_modifications_summary` (resumen de los cambios realizados)
  - Esta herramienta recibe el objeto ViajeState COMPLETO.
  - Debes pasar TODO el itinerario con las modificaciones ya aplicadas en la sección itinerario_diario.
  - NO modifiques destinos, cantidad_dias, transportes_entre_destinos, etc. SOLO itinerario_diario.
</Tools>

<STRICT_RULES>
⚠️ ESTA ES TU REGLA MÁS IMPORTANTE ⚠️

**PROHIBIDO ABSOLUTAMENTE:**
- ❌ Cambiar destinos o ciudades del viaje
- ❌ Agregar o quitar días del viaje
- ❌ Modificar la duración total del viaje
- ❌ Cambiar la cantidad de días en cada destino
- ❌ Modificar el transporte entre ciudades
- ❌ Alterar el orden de los destinos
- ❌ Usar la herramienta `apply_itinerary_modifications` (NO tienes acceso a ella)

**PERMITIDO:**
- ✅ Modificar actividades dentro de un día (museos, restaurantes, horarios)
- ✅ Agregar o quitar actividades de un día específico
- ✅ Cambiar el orden de actividades dentro de un día
- ✅ Ajustar horarios de actividades
- ✅ Responder preguntas sobre las actividades programadas
- ✅ Buscar información sobre lugares o actividades

**REGLAS ESPECIALES PARA MOVER ACTIVIDADES ENTRE DÍAS:**
Puedes mover una actividad de un día a otro SOLO si se cumplen TODAS estas condiciones:
1. ✅ Ambos días están en el MISMO destino/ciudad
2. ✅ La actividad NO es la primera del día (no puede ser "Llegada a...", "Check-in", etc.)
3. ✅ La actividad NO es la última del día (no puede ser "Viaje a...", "Check-out", "Salida hacia...", etc.)
4. ✅ La actividad NO implica transporte entre destinos

**ACTIVIDADES QUE NUNCA PUEDEN MOVERSE:**
- ❌ Actividades de llegada ("Llegada a [ciudad]", "Check-in hotel", "Llegada al aeropuerto")
- ❌ Actividades de salida ("Viaje a [ciudad]", "Check-out", "Salida hacia [ciudad]", "Traslado a aeropuerto")
- ❌ Primera actividad de un destino nuevo
- ❌ Última actividad antes de cambiar de destino
- ❌ Cualquier actividad relacionada con transporte entre ciudades

**ACCIÓN DE RECHAZO:**
Si el usuario solicita algo de la lista "PROHIBIDO", debes rechazarlo amablemente con un mensaje como:

"Entiendo tu solicitud, pero en esta etapa ya has confirmado la ruta principal (destinos y días). 
Para cambios en la estructura del viaje (destinos, duración, transportes), necesitas volver a la fase de planificación.
En este momento solo puedo ayudarte a ajustar las actividades diarias: cambiar restaurantes, agregar museos, 
modificar horarios, etc. ¿Hay alguna actividad que quieras ajustar?"

Si intenta mover una actividad de llegada/salida/transporte:
"No puedo mover esa actividad porque está relacionada con el transporte entre destinos. Las actividades de llegada 
y salida deben permanecer en su posición para mantener la coherencia del viaje. ¿Te gustaría modificar otras 
actividades dentro del día?"

Mantén siempre un tono amable pero firme al rechazar solicitudes fuera de tu alcance.
</STRICT_RULES>

"""

# ==== Memory Notes ====
"""

- Si el cliente te hace una aclaracion que consideres importante. Puedes usar la herramienta add_memory_notes para agregar las notas a la memoria del usuario o del itinerario.

Cuando el usuario te hace una aclaracion que consideres importante. Puedes usar la herramienta add_memory_notes para agregar las notas a la memoria del usuario o del itinerario.
La memoria del usuario persitira para los diferentes itinerarios.
La memoria del itinerario solo persitira para este itinerario en particular.
Las preferencias generales del usuario guardalas como memoria del usuario, las preferencias puntuales para este viaje guardalas como memoria del itinerario.
"""

def prompt(
    state: CustomState
):
    itinerary = state["itinerary"]
    system_msg = f"{PROMPT} El itinerario actual es: {itinerary}"
    return [{"role": "system", "content": system_msg}] + list(state["messages"])


# ==== Tools ====
# # ==== Memory Notes ====
# class MemoryNotesType(Enum):
#     USER_NOTES = "user_notes"
#     ITINERARY_NOTES = "itinerary_notes"

# def add_memory_notes(
#     notas: str = Field(..., description="Recordatorio de preferencia del usaurio, para este viaje o para su perfil"), 
#     type: MemoryNotesType = Field(..., description="Tipo de notas a agregar. USER_NOTES o ITINERARY_NOTES.")
# ):
#     """
#     Agrega notas a la memoria del usuario o del itinerario.
#     El tipo de notas puede ser USER_NOTES o ITINERARY_NOTES.
#     USER_NOTES son notas que permanecen en la memoria del usuario. Estas notas se usaran para futuras conversaciones y generaciones de itinertios personalizados.
#     ITINERARY_NOTES son notas que permanecen en la memoria del itinerario. Estas notas se usaran para este itiinerario en particular.
#     """
#     print(f"====\n \n Notes: {notas} \n Type: {type} \n ====")
#     # TODO: Add the notes to DB
#     return f"Notes added to the memory. Type: {type}"

def modify_activities(
    tool_call_id: Annotated[str, InjectedToolCallId],
    new_itinerary: ViajeState = Field(..., description="El itinerario COMPLETO actualizado, con todos los cambios en itinerario_diario aplicados"),
    new_itinerary_modifications_summary: str = Field(..., description="Resumen de las modificaciones realizadas en las actividades diarias"),
) :
    """
    Modifica las actividades diarias del itinerario.
    
    IMPORTANTE: Esta herramienta recibe el ViajeState COMPLETO con las modificaciones aplicadas.
    Solo se debe usar para cambiar actividades diarias (itinerario_diario).
    NO modificar destinos, días totales, ni transportes.
    
    Args:
        - new_itinerary: ViajeState completo con itinerario_diario actualizado
        - new_itinerary_modifications_summary: Resumen de los cambios realizados
    """

    user_feedback = interrupt(  
        f"Se van a aplicar las siguientes modificaciones a tus actividades: {new_itinerary_modifications_summary}. "
        "¿Estás de acuerdo? [Si (s)] (Mencionar cambios si no estás de acuerdo)"
    )

    user_feedback = user_feedback["messages"].lower()

    print(f"====\n \n User feedback (modify_activities): {user_feedback} \n ====")

    if user_feedback == "s" or user_feedback == "si":
        # Actualizar el itinerario completo en el estado
        # La persistencia en BD se maneja en services/itinerary.py
        return Command(update={
            "itinerary": new_itinerary,
            "messages": [
                ToolMessage(
                    "",  # String vacío para evitar mostrar mensaje técnico al usuario
                    tool_call_id=tool_call_id
                )
            ]
        }) 
    
    else:
        return Command(update={
            "messages": [
                ToolMessage(
                    f"De acuerdo, no he aplicado los cambios. El usuario respondió: {user_feedback}",
                    tool_call_id=tool_call_id
                )
            ]
        })

def web_search(
    query: str
) -> str:
    """
    Search the web for the query.
    """
    from openai import OpenAI
    client = OpenAI()

    response = client.responses.create(
        model=web_search_model,
        tools=[{"type": "web_search"}],
        input=query
    )

    return response.output[-1].content[0].text

# tools = [replace_string_in_itinerary, web_search]
tools = [web_search, modify_activities]


# ==== Create agents ====
activities_chat_agent = create_react_agent(
    model,
    tools=tools,
    prompt=prompt,
    checkpointer=checkpointer,
    state_schema=CustomState,
    # pre_model_hook=summarization_node, 
)
