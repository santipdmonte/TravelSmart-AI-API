from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from graphs.main_itinerary_graph import main_itinerary_graph
from graphs.itinerary_agent_graph import itinerary_agent
from langgraph.types import Command
from state import ViajeStateInput
from fastapi.responses import HTMLResponse
from utils.utils import extract_chatbot_message, detect_hil_mode


# Crear router para las rutas del clasificador de viajeros
itinerary_router = APIRouter(prefix="/itinerary", tags=["Itinerary"])

@itinerary_router.get("/agent_planner", response_class=HTMLResponse)
def home():
    with open("agent_planner.html", encoding="utf-8") as f:
        return f.read()

@itinerary_router.post("/generate_itinerary")
def generar_itinerario(input_state: ViajeStateInput):

    config = {
        "configurable": {
            "thread_id": "1"  
        }
    }

    result = main_itinerary_graph.invoke(input_state) #, config=config)

    return result

    # with open("itinerario_result.json", encoding="utf-8") as f:
    #     data = json.load(f)
    # return data


# Itinerary Agent

@itinerary_router.post("/initialize_graph")
def initialize_graph(thread_id: str):

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    initial_state = {
        "itinerary": "Viaje a la playa",
        "user_name": "Juan",
        "user_id": "user_123",
        # "messages": [{"role": "user", "content": "Quiero que mi itinerario ahora sea 'Viaje a la montaña'"}]
    }

    itinerary_agent.invoke(initial_state, config=config)

    # Get the raw state from the agent
    raw_state = itinerary_agent.get_state(config)
    
    # Check if agent is in HIL mode
    is_hil_mode, hil_message, state_values = detect_hil_mode(raw_state)
    
    if is_hil_mode:
        # HIL mode detected - extract state from values
        state_info = state_values if state_values else {}
        return {
            "mode": "hil",
            "hil_message": hil_message,
            "state": {
                "itinerary": state_info.get("itinerary", ""),
                "user_name": state_info.get("user_name", ""),
                "user_id": state_info.get("user_id", ""),
                "llm_input_messages": state_info.get("llm_input_messages", [])
            },
            "raw_state": raw_state  # Keep for debugging if needed
        }
    else:
        # Normal mode - extract the required information from the complex response structure
        # The raw_state is an array where the first element contains the state info
        state_info = raw_state[0] if len(raw_state) > 0 else {}
        
        # Extract the chatbot message content from the messages
        chatbot_message = extract_chatbot_message(state_info)
        
        # Return the structured response
        return {
            "mode": "normal",
            "state": {
                "itinerary": state_info.get("itinerary", ""),
                "user_name": state_info.get("user_name", ""),
                "user_id": state_info.get("user_id", ""),
                "llm_input_messages": state_info.get("llm_input_messages", [])
            },
            "chatbot_response": chatbot_message,
            "raw_state": raw_state  # Keep for debugging if needed
        }

@itinerary_router.post("/user_response")
def user_response(thread_id: str, user_response: str):

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    response = itinerary_agent.invoke({"messages": user_response}, config=config)

    # Get the raw state from the agent
    raw_state = itinerary_agent.get_state(config)

    print("--------------------------------")
    print(raw_state)
    print("--------------------------------")
    
    # Check if agent is in HIL mode
    is_hil_mode, hil_message, state_values = detect_hil_mode(raw_state)
    
    if is_hil_mode:
        # HIL mode detected - extract state from values
        state_info = state_values if state_values else {}
        return {
            "mode": "hil",
            "hil_message": hil_message,
            "state": {
                "itinerary": state_info.get("itinerary", ""),
                "user_name": state_info.get("user_name", ""),
                "user_id": state_info.get("user_id", ""),
                "llm_input_messages": state_info.get("llm_input_messages", [])
            },
            "raw_state": raw_state  # Keep for debugging if needed
        }
    else:
        # Normal mode - extract the required information from the complex response structure
        # The raw_state is an array where the first element contains the state info
        state_info = raw_state[0] if len(raw_state) > 0 else {}
        
        # Extract the chatbot message content from the messages
        chatbot_message = extract_chatbot_message(state_info)
        
        # Return the structured response
        return {
            "mode": "normal",
            "state": {
                "itinerary": state_info.get("itinerary", ""),
                "user_name": state_info.get("user_name", ""),
                "user_id": state_info.get("user_id", ""),
                "llm_input_messages": state_info.get("llm_input_messages", [])
            },
            "chatbot_response": chatbot_message,
            "raw_state": raw_state  # Keep for debugging if needed
        }

@itinerary_router.post("/HIL_response")
def user_HIL_response(thread_id: str, user_HIL_response: str):

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    response = itinerary_agent.invoke(Command(resume={"messages": user_HIL_response}), config=config)

    # Get the raw state from the agent
    raw_state = itinerary_agent.get_state(config)
    
    print("--------------------------------")
    print("HIL Response:")
    print(raw_state)
    print("--------------------------------")
    
    # Check if agent is in HIL mode again (could be chained HIL requests)
    is_hil_mode, hil_message, state_values = detect_hil_mode(raw_state)
    
    if is_hil_mode:
        # HIL mode detected - extract state from values
        state_info = state_values if state_values else {}
        return {
            "mode": "hil",
            "hil_message": hil_message,
            "state": {
                "itinerary": state_info.get("itinerary", ""),
                "user_name": state_info.get("user_name", ""),
                "user_id": state_info.get("user_id", ""),
                "llm_input_messages": state_info.get("llm_input_messages", [])
            },
            "raw_state": raw_state  # Keep for debugging if needed
        }
    else:
        # Normal mode - extract the required information from the complex response structure
        # The raw_state is an array where the first element contains the state info
        state_info = raw_state[0] if len(raw_state) > 0 else {}
        
        # Extract the chatbot message content from the messages
        chatbot_message = extract_chatbot_message(state_info)
        
        # Return the structured response
        return {
            "mode": "normal",
            "state": {
                "itinerary": state_info.get("itinerary", ""),
                "user_name": state_info.get("user_name", ""),
                "user_id": state_info.get("user_id", ""),
                "llm_input_messages": state_info.get("llm_input_messages", [])
            },
            "chatbot_response": chatbot_message,
            "raw_state": raw_state  # Keep for debugging if needed
        }

@itinerary_router.get("/get_state")
def get_state(thread_id: str):

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    return itinerary_agent.get_state(config)    