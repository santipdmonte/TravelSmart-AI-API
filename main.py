from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from state import ViajeState, ViajeStateInput, ViajeStateModify
# from accommodation_graph.state import AlojamientoStateInput
# from accommodation_graph.accommodation_graph import accommodation_graph
from trip_planner_graph.main_itinerary_graph import main_itinerary_graph
from trip_planner_graph.modify_itinerary_graph import modify_itinerary_graph
import uvicorn
import json

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def home():
    with open("itinerario.html", encoding="utf-8") as f:
        return f.read()

@app.post("/itinerario")
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

# print(result)

@app.post("/modificar_itinerario")
def modificar_itinerario(prompt: str):

    config = {
        "configurable": {
            "thread_id": "1"  
        }
    }


    try:
        with open("itinerario_turquia_12.json", encoding="utf-8") as f:
            data = json.load(f)

        state = ViajeStateModify(
            itinerario_actual=ViajeState(**data),
            prompt=prompt
        )
        
    except Exception as e:
        print(f"Error loading itinerary result: {e}")
        return {"error": str(e)}

    result = modify_itinerary_graph.invoke(input = state) #, config=config)

    return result


# Agent Flow

from trip_planner_graph.agent_planner_graph import agent
from langgraph.types import Command

def extract_chatbot_message(state_info):
    """Helper function to extract chatbot message from state info"""
    chatbot_message = ""
    if 'messages' in state_info and len(state_info['messages']) > 0:
        # Get the last AI message content
        for message in reversed(state_info['messages']):
            try:
                # Handle message objects (like AIMessage)
                if hasattr(message, 'type') and message.type == 'ai':
                    chatbot_message = getattr(message, 'content', '')
                    break
                # Handle dictionary format
                elif isinstance(message, dict) and message.get('type') == 'ai':
                    chatbot_message = message.get('content', '')
                    break
            except Exception as e:
                print(f"Error extracting message: {e}")
                continue
    return chatbot_message

def detect_hil_mode(raw_state):
    """Detect if the agent is waiting for Human in the Loop response"""
    hil_message = ""
    is_hil_mode = False
    
    try:
        # Check if this is a StateSnapshot format
        if hasattr(raw_state, 'tasks') and raw_state.tasks:
            for task in raw_state.tasks:
                if hasattr(task, 'interrupts') and task.interrupts:
                    for interrupt in task.interrupts:
                        if hasattr(interrupt, 'value') and interrupt.value:
                            hil_message = interrupt.value
                            is_hil_mode = True
                            break
                    if is_hil_mode:
                        break
        
        # Alternative: Check in the raw_state if it's a different format
        elif hasattr(raw_state, 'values'):
            state_values = raw_state.values
            # Extract state info for other purposes
            return is_hil_mode, hil_message, state_values
            
    except Exception as e:
        print(f"Error detecting HIL mode: {e}")
    
    return is_hil_mode, hil_message, None

@app.get("/agent_planner", response_class=HTMLResponse)
def home():
    with open("agent_planner.html", encoding="utf-8") as f:
        return f.read()

@app.post("/initialize_graph")
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

    agent.invoke(initial_state, config=config)

    # Get the raw state from the agent
    raw_state = agent.get_state(config)
    
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

@app.post("/user_response")
def user_response(thread_id: str, user_response: str):

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    response = agent.invoke({"messages": user_response}, config=config)

    # Get the raw state from the agent
    raw_state = agent.get_state(config)

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

@app.post("/user_HIL_response")
def user_HIL_response(thread_id: str, user_HIL_response: str):

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    response = agent.invoke(Command(resume={"messages": user_HIL_response}), config=config)

    # Get the raw state from the agent
    raw_state = agent.get_state(config)
    
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

@app.get("/get_state")
def get_state(thread_id: str):

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    return graph.get_state(config)





# @app.post("/accommodation")
# def generar_accommodation(): #input_state: AlojamientoStateInput):

#     with open("destino_result.json", encoding="utf-8") as f:
#         data = json.load(f)

#     input_state = AlojamientoStateInput (
#         destino=data,
#         fecha_inicio="2025-05-01",
#         cantidad_adultos=2,
#         cantidad_ninos=0
#     )

#     result = accommodation_graph.invoke(input_state)
#     return result


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
