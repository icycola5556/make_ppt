import re
from fastapi import HTTPException

def validate_session_id(session_id: str) -> str:
    """
    Validate session_id to prevent path traversal attacks.
    Allowed characters: alphanumeric, hyphen, underscore.
    Length limit: 64 characters.
    """
    if not session_id:
        raise ValueError("Session ID cannot be empty")
    
    if len(session_id) > 64:
        raise ValueError("Session ID too long")
        
    # Only allow safe characters
    if not re.match(r'^[a-zA-Z0-9_-]+$', session_id):
        raise ValueError("Invalid session ID format")
        
    # Explicitly check for path traversal patterns just in case
    if '..' in session_id or '/' in session_id or '\\' in session_id:
        raise ValueError("Invalid characters in session ID")
        
    return session_id
