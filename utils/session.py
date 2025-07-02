"""
Session management utilities
"""

from fastapi import Request
from typing import Optional
import uuid


def get_session_id_from_request(request: Request) -> uuid.UUID:
    """Get or create session ID from request headers/cookies"""
    # Try to get session ID from custom header first
    session_id_str = request.headers.get("X-Session-ID")
    
    if session_id_str:
        try:
            return uuid.UUID(session_id_str)
        except ValueError:
            # Invalid UUID format, generate new one
            pass
    
    # Try to get from cookies as fallback
    session_id_str = request.cookies.get("session_id")
    if session_id_str:
        try:
            return uuid.UUID(session_id_str)
        except ValueError:
            pass
    
    # If no valid session ID found anywhere, generate a new one
    return uuid.uuid4()