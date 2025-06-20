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