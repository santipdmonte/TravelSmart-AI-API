"""
Agent utilities for thread validation and state management
"""

from typing import Any, List, Dict, Union


def is_valid_thread_state(raw_state) -> bool:
    """
    Validate if a thread state is valid (has meaningful conversation data).
    
    Args:
        raw_state: The raw state returned from itinerary_agent.get_state()
        
    Returns:
        bool: True if thread state is valid (has messages), False otherwise
        
    Examples:
        Invalid state: [{}, [], {...}, null, null, null, []]
        Valid state: [{ messages: [...], ... }, ...]
    """
    # Check if raw_state has the expected structure
    if not raw_state or not isinstance(raw_state, list) or len(raw_state) == 0:
        return False
    
    # Get the first element which contains the main state data
    first_element = raw_state[0]
    
    # Valid state should have meaningful data in the first element
    if not isinstance(first_element, dict):
        return False
    
    # Check for 'messages' field as the key indicator of a valid conversation
    messages = first_element.get('messages')
    
    # Valid if messages exist and is a non-empty list
    return isinstance(messages, list) and len(messages) > 0


def is_empty_thread_state(raw_state: List[Any]) -> bool:
    """
    Check if the thread state is empty (no conversation started).
    
    Args:
        raw_state: The raw state returned from itinerary_agent.get_state()
        
    Returns:
        bool: True if thread state is empty
    """
    if not raw_state or not isinstance(raw_state, list) or len(raw_state) == 0:
        return True
    
    first_element = raw_state[0]
    
    # Empty state typically has an empty dict or no messages
    if not isinstance(first_element, dict):
        return True
    
    # Check if it has no messages or empty messages
    messages = first_element.get('messages', [])
    return not isinstance(messages, list) or len(messages) == 0


def extract_thread_messages(raw_state: List[Any]) -> List[Dict[str, Any]]:
    """
    Extract messages from thread state safely.
    
    Args:
        raw_state: The raw state returned from itinerary_agent.get_state()
        
    Returns:
        List of messages or empty list if not available
    """
    if not is_valid_thread_state(raw_state):
        return []
    
    first_element = raw_state[0]
    return first_element.get('messages', [])


def get_last_message(raw_state: List[Any]) -> Dict[str, Any]:
    """
    Get the last message from thread state safely.
    
    Args:
        raw_state: The raw state returned from itinerary_agent.get_state()
        
    Returns:
        Last message dict or empty dict if not available
    """
    messages = extract_thread_messages(raw_state)
    return messages[-1] if messages else {}
