from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from database import get_db
from graphs.main_itinerary_graph import main_itinerary_graph
from graphs.itinerary_chat_agent import itinerary_agent
from graphs.activities_chat_agent import activities_chat_agent
from langgraph.types import Command
from states.itinerary import ViajeStateInput, ViajeState
from fastapi.responses import HTMLResponse
from utils.utils import extract_chatbot_message, detect_hil_mode
import traceback
from fastapi import HTTPException
from langchain_core.runnables import RunnableConfig
from services.itinerary import ItineraryService
import uuid

# Crear router para las rutas del clasificador de viajeros
itinerary_router = APIRouter(prefix="/itinerary", tags=["Itinerary"])

@itinerary_router.get("/agent_planner", response_class=HTMLResponse)
def home():
    with open("agent_planner.html", encoding="utf-8") as f:
        return f.read()

@itinerary_router.post("/generate_itinerary")
def generate_itinerary(input_state: ViajeStateInput):
    print("--- Endpoint /generate_itinerary RECIBIÓ UNA LLAMADA ---")
    try:
        # Intentamos ejecutar la lógica original
        result = main_itinerary_graph.invoke(input_state)
        print(f"Resultado del grafo: {result}")
        return result

    except Exception as e:
        # ¡AQUÍ CAPTURAREMOS CUALQUIER ERROR!
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("¡¡¡ SE HA PRODUCIDO UN ERROR DENTRO DEL ENDPOINT !!!")
        
        # Imprimimos el error detallado (traceback) en la consola
        traceback.print_exc()
        
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        
        # Le devolvemos un error 500 a Postman con el mensaje del error
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# AGENT CHAT ENDPOINTS - Con enrutamiento dinámico de agentes
# ==============================================================================

@itinerary_router.post("/initialize_graph")
def initialize_graph(
    thread_id: str, 
    itinerary_state: ViajeState,
    db: Session = Depends(get_db)
):
    """
    Inicializa el grafo de conversación del agente con el estado del itinerario.
    
    ENRUTAMIENTO DINÁMICO:
    - Si el itinerary no está confirmado (draft): usa itinerary_agent
    - Si el itinerary está confirmado: usa activities_chat_agent
    
    Args:
        thread_id: ID del thread (generalmente el itinerary_id)
        itinerary_state: Estado completo del itinerario
        db: Sesión de base de datos
    
    Returns:
        Estado del agente (modo normal o HIL)
    """
    try:
        # Parsear el thread_id a UUID para obtener el itinerario
        itinerary_id = uuid.UUID(thread_id)
        itinerary_service = ItineraryService(db)
        itinerary = itinerary_service.get_itinerary_by_id(itinerary_id)
        
        if not itinerary:
            raise HTTPException(status_code=404, detail="Itinerary not found")
        
        # ENRUTAMIENTO: Seleccionar el agente correcto basado en el estado
        if itinerary.status == "confirmed":
            agent = activities_chat_agent
            agent_name = "activities_chat_agent"
        else:
            agent = itinerary_agent
            agent_name = "itinerary_agent"
        
        # Configuración del thread
        config: RunnableConfig = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        # Estado inicial con el itinerario completo
        initial_state = {
            "itinerary": itinerary_state,
            "user_name": "Usuario",  # Puede ser parametrizado
            "user_id": str(itinerary.user_id) if itinerary.user_id else str(itinerary.session_id),
        }

        # Invocar el agente seleccionado
        agent.invoke(initial_state, config=config)

        # Obtener el estado del agente
        raw_state = agent.get_state(config)
        
        # Verificar si está en modo HIL
        is_hil_mode, hil_message, state_values = detect_hil_mode(agent, config)
        
        if is_hil_mode:
            state_info = state_values if state_values else {}
            return {
                "mode": "hil",
                "agent": agent_name,
                "hil_message": hil_message,
                "state": {
                    "itinerary": state_info.get("itinerary", ""),
                    "user_name": state_info.get("user_name", ""),
                    "user_id": state_info.get("user_id", ""),
                    "llm_input_messages": state_info.get("llm_input_messages", [])
                },
                "raw_state": raw_state  # Restaurado para debugging
            }
        else:
            state_info = raw_state[0] if len(raw_state) > 0 else {}
            chatbot_message = extract_chatbot_message(state_info)
            
            return {
                "mode": "normal",
                "agent": agent_name,
                "state": {
                    "itinerary": state_info.get("itinerary", ""),
                    "user_name": state_info.get("user_name", ""),
                    "user_id": state_info.get("user_id", ""),
                    "llm_input_messages": state_info.get("llm_input_messages", [])
                },
                "chatbot_response": chatbot_message,
                "raw_state": raw_state  # Restaurado para debugging
            }
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid thread_id format (must be UUID)")
    except Exception as e:
        print("!!!!! ERROR en /initialize_graph !!!!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@itinerary_router.post("/user_response")
def user_response(
    thread_id: str, 
    user_response: str,
    db: Session = Depends(get_db)
):
    """
    Procesa la respuesta del usuario en el chat del agente.
    
    ENRUTAMIENTO DINÁMICO:
    - Obtiene el itinerario de la BD usando thread_id (que es itinerary_id)
    - Si status == "confirmed": usa activities_chat_agent (solo modifica actividades)
    - Si status != "confirmed": usa itinerary_agent (puede modificar todo)
    
    Args:
        thread_id: ID del thread (itinerary_id)
        user_response: Mensaje del usuario
        db: Sesión de base de datos
    
    Returns:
        Estado del agente con la respuesta del chatbot o mensaje HIL
    """
    try:
        # Parsear el thread_id a UUID
        itinerary_id = uuid.UUID(thread_id)
        itinerary_service = ItineraryService(db)
        itinerary = itinerary_service.get_itinerary_by_id(itinerary_id)
        
        if not itinerary:
            raise HTTPException(status_code=404, detail="Itinerary not found")
        
        # ENRUTAMIENTO: Seleccionar agente basado en el estado del itinerario
        if itinerary.status == "confirmed":
            agent = activities_chat_agent
            agent_name = "activities_chat_agent"
            print(f"🎯 Usando activities_chat_agent (itinerario confirmado)")
        else:
            agent = itinerary_agent
            agent_name = "itinerary_agent"
            print(f"🎯 Usando itinerary_agent (itinerario en borrador)")
        
        # Configuración del thread
        config: RunnableConfig = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        # Invocar el agente con el mensaje del usuario
        response = agent.invoke({"messages": user_response}, config=config)

        # Obtener el estado del agente
        raw_state = agent.get_state(config)

        print("--------------------------------")
        print(f"Agent: {agent_name}")
        print(f"Raw state: {raw_state}")
        print("--------------------------------")
        
        # Verificar si está en modo HIL
        is_hil_mode, hil_message, state_values = detect_hil_mode(agent, config)
        
        if is_hil_mode:
            state_info = state_values if state_values else {}
            return {
                "mode": "hil",
                "agent": agent_name,
                "hil_message": hil_message,
                "state": {
                    "itinerary": state_info.get("itinerary", ""),
                    "user_name": state_info.get("user_name", ""),
                    "user_id": state_info.get("user_id", ""),
                    "llm_input_messages": state_info.get("llm_input_messages", [])
                },
                "raw_state": raw_state  # Restaurado para debugging
            }
        else:
            state_info = raw_state[0] if len(raw_state) > 0 else {}
            chatbot_message = extract_chatbot_message(state_info)
            
            return {
                "mode": "normal",
                "agent": agent_name,
                "state": {
                    "itinerary": state_info.get("itinerary", ""),
                    "user_name": state_info.get("user_name", ""),
                    "user_id": state_info.get("user_id", ""),
                    "llm_input_messages": state_info.get("llm_input_messages", [])
                },
                "chatbot_response": chatbot_message,
                "raw_state": raw_state  # Restaurado para debugging
            }
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid thread_id format (must be UUID)")
    except Exception as e:
        print("!!!!! ERROR en /user_response !!!!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@itinerary_router.post("/HIL_response")
def user_HIL_response(
    thread_id: str, 
    user_HIL_response: str,
    db: Session = Depends(get_db)
):
    """
    Procesa la respuesta del usuario a una solicitud Human-in-the-Loop (HIL).
    
    ENRUTAMIENTO DINÁMICO:
    - Obtiene el itinerario de la BD usando thread_id (que es itinerary_id)
    - Si status == "confirmed": usa activities_chat_agent
    - Si status != "confirmed": usa itinerary_agent
    
    ACTUALIZACIÓN DE BD:
    - Si el usuario confirma los cambios (responde "si" o "s"), actualiza el itinerario en BD
    
    Args:
        thread_id: ID del thread (itinerary_id)
        user_HIL_response: Respuesta del usuario (generalmente "si" o feedback)
        db: Sesión de base de datos
    
    Returns:
        Estado del agente después de procesar la respuesta HIL
    """
    try:
        # Parsear el thread_id a UUID
        itinerary_id = uuid.UUID(thread_id)
        itinerary_service = ItineraryService(db)
        itinerary = itinerary_service.get_itinerary_by_id(itinerary_id)
        
        if not itinerary:
            raise HTTPException(status_code=404, detail="Itinerary not found")
        
        # ENRUTAMIENTO: Seleccionar agente basado en el estado del itinerario
        if itinerary.status == "confirmed":
            agent = activities_chat_agent
            agent_name = "activities_chat_agent"
            print(f"🎯 Usando activities_chat_agent para HIL (itinerario confirmado)")
        else:
            agent = itinerary_agent
            agent_name = "itinerary_agent"
            print(f"🎯 Usando itinerary_agent para HIL (itinerario en borrador)")
        
        # Configuración del thread
        config: RunnableConfig = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        # Invocar el agente con el comando de reanudación
        response = agent.invoke(Command(resume={"messages": user_HIL_response}), config=config)

        # Obtener el estado del agente
        raw_state = agent.get_state(config)
        
        print("--------------------------------")
        print(f"HIL Response - Agent: {agent_name}")
        print(f"Raw state: {raw_state}")
        print("--------------------------------")
        
        # Verificar si hay otro HIL encadenado
        is_hil_mode, hil_message, state_values = detect_hil_mode(agent, config)
        
        if is_hil_mode:
            state_info = state_values if state_values else {}
            return {
                "mode": "hil",
                "agent": agent_name,
                "hil_message": hil_message,
                "state": {
                    "itinerary": state_info.get("itinerary", ""),
                    "user_name": state_info.get("user_name", ""),
                    "user_id": state_info.get("user_id", ""),
                    "llm_input_messages": state_info.get("llm_input_messages", [])
                },
                "raw_state": raw_state  # Restaurado para debugging
            }
        else:
            state_info = raw_state[0] if len(raw_state) > 0 else {}
            chatbot_message = extract_chatbot_message(state_info)
            
            # IMPORTANTE: Si el usuario confirmó los cambios, actualizar el itinerario en BD
            # (Esto debería manejarse en el servicio, pero lo dejamos como nota)
            # TODO: Considerar mover esta lógica al servicio ItineraryService
            
            return {
                "mode": "normal",
                "agent": agent_name,
                "state": {
                    "itinerary": state_info.get("itinerary", ""),
                    "user_name": state_info.get("user_name", ""),
                    "user_id": state_info.get("user_id", ""),
                    "llm_input_messages": state_info.get("llm_input_messages", [])
                },
                "chatbot_response": chatbot_message,
                "raw_state": raw_state  # Restaurado para debugging
            }
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid thread_id format (must be UUID)")
    except Exception as e:
        print("!!!!! ERROR en /HIL_response !!!!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@itinerary_router.get("/get_state")
def get_state(
    thread_id: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene el estado actual del agente para un thread específico.
    
    ENRUTAMIENTO DINÁMICO:
    - Determina qué agente usar basándose en el estado del itinerario
    - Retorna el estado completo del agente seleccionado
    
    Args:
        thread_id: ID del thread (itinerary_id)
        db: Sesión de base de datos
    
    Returns:
        Estado completo del agente
    """
    try:
        # Parsear el thread_id a UUID
        itinerary_id = uuid.UUID(thread_id)
        itinerary_service = ItineraryService(db)
        itinerary = itinerary_service.get_itinerary_by_id(itinerary_id)
        
        if not itinerary:
            raise HTTPException(status_code=404, detail="Itinerary not found")
        
        # ENRUTAMIENTO: Seleccionar agente basado en el estado del itinerario
        if itinerary.status == "confirmed":
            agent = activities_chat_agent
            agent_name = "activities_chat_agent"
        else:
            agent = itinerary_agent
            agent_name = "itinerary_agent"
        
        config: RunnableConfig = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        raw_state = agent.get_state(config)
        
        return {
            "agent": agent_name,
            "state": raw_state
        }
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid thread_id format (must be UUID)")
    except Exception as e:
        print("!!!!! ERROR en /get_state !!!!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))    