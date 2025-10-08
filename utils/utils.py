import json
from pydantic.json import pydantic_encoder

from states.itinerary import ViajeState
from states.daily_activities import DailyItineraryOutput

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

def detect_hil_mode(agent,config):
    """Detect if the agent is waiting for Human in the Loop response"""
    hil_message = ""
    is_hil_mode = False

    raw_state = agent.get_state(config)
    
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

def state_to_json(state):
    """Convert the state to a JSON string"""
    return json.dumps(state, default=pydantic_encoder)

def state_to_dict(state):
    """Convert the state to a dictionary"""
    return json.loads(state_to_json(state))

def update_activities_day(itinerary_dict: dict, new_activities_day: DailyItineraryOutput, titulo_dia: str) -> dict | bool:
    """
    Update the activities in the itinerary based on the day title.
    More robust version with better error handling.
    
    Args:
        itinerary_dict: Dictionary containing the full itinerary structure from JSON
        new_activities_day: New daily itinerary with updated activities
        titulo_dia: Title of the day to update (must match exactly)
    
    Returns:
        Updated itinerary dictionary if successful, False if day not found
    """
    try:
        itinerario_diario = itinerary_dict['details_itinerary']['itinerario_diario']
        
        for i, day in enumerate(itinerario_diario):
            if day.get('titulo') == titulo_dia:
                itinerario_diario[i] = new_activities_day.model_dump()
                
                return itinerary_dict
        
        return False
        
    except (KeyError, TypeError) as e:
        # Handle missing keys or wrong structure
        print(f"Error updating activities: {e}")
        return False