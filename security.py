"""
Security filters and validation for ECHO Decision Safety Agent.
"""
import re
from audit import log

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions?",
    r"system\s*:\s*",
    r"disregard\s+all",
    r"you\s+are\s+now\s+dan",
    r"drop\s+table",
    r"delete\s+from",
    r"<script",
    r"javascript:",
    r"give\s+me\s+admin",
    r"admin\s+mode",
    r"override\s+permission",
]

def check_input(text: str) -> dict:
    """
    Checks free-text input for length, structure, and prompt injection patterns.
    Returns: {"safe": bool, "reason": str}
    """
    if not text or len(text.strip()) < 3:
        return {"safe": False, "reason": "Input too short (minimum 3 characters required)."}
    
    if len(text) > 500:
        return {"safe": False, "reason": "Input exceeds maximum allowed limit of 500 characters."}
    
    lower_text = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lower_text):
            return {"safe": False, "reason": f"Security policy violation: detected forbidden pattern '{pattern}'."}
            
    return {"safe": True, "reason": "Passed security check."}

def can_run(role: str, action: str) -> bool:
    """Legacy check for exam simulation."""
    if action == "run_simulation":
        return role == "admin"
    return False
