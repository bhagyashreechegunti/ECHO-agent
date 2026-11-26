"""
Audit logger for ECHO Decision Safety Agent.
Logs all events with timestamp, user, role, and details.
"""
import os
import json
from datetime import datetime, timezone

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audit.log")

# In-memory mirror for fast reactive UI rendering
_memory_audit = []

def log(event: str, user: str = "system", details: dict = None):
    """Log an audit event."""
    if details is None:
        details = {}
    
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "event": event,
        "user": user,
        "details": details
    }
    _memory_audit.append(entry)
    
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass
    return entry

def read_log():
    """Read all audit log entries."""
    entries = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entries.append(json.loads(line))
        except Exception:
            pass
    if not entries and _memory_audit:
        return list(_memory_audit)
    return entries
