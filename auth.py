"""
Authentication and role-based access control for ECHO.
"""
import os
import hashlib
import hmac
import pandas as pd
from datetime import datetime, timezone, timedelta
from audit import log, read_log

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
USERS_CSV = os.path.join(DATA_DIR, "users.csv")

# Section 2.4 Permission Matrix
PERMISSIONS = {
    "admin": {
        "see_section_all": True,
        "see_section_own": True,
        "see_staff_own": True,
        "see_lab_timetable": True,
        "create_request": False,
        "send_feedback": False,
        "see_request_list": True,
        "see_own_requests": True,
        "run_simulation": True,
        "approve": True,
        "reject": True,
        "audit_log": True,
        "red_team": True,
    },
    "staff": {
        "see_section_all": False,
        "see_section_own": False,
        "see_staff_own": True,
        "see_lab_timetable": True,
        "create_request": True,
        "send_feedback": False,
        "see_request_list": False,
        "see_own_requests": True,
        "run_simulation": False,
        "approve": False,
        "reject": False,
        "audit_log": False,
        "red_team": False,
    },
    "student": {
        "see_section_all": False,
        "see_section_own": True,
        "see_staff_own": False,
        "see_lab_timetable": False,
        "create_request": False,
        "send_feedback": True,
        "see_request_list": False,
        "see_own_requests": False,
        "run_simulation": False,
        "approve": False,
        "reject": False,
        "audit_log": False,
        "red_team": False,
    }
}

def verify_hash(password: str, salt_hex: str, hash_hex: str) -> bool:
    try:
        h = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt_hex), 200_000)
        return hmac.compare_digest(h.hex(), hash_hex)
    except Exception:
        return False

def is_locked_out(username: str) -> bool:
    """Check if user had 5 or more failed logins within last 5 minutes."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
    entries = read_log()
    failed_count = 0
    for entry in entries:
        if entry.get("event") == "login_failed" and entry.get("details", {}).get("username") == username:
            try:
                t = datetime.fromisoformat(entry.get("timestamp"))
                if t >= cutoff:
                    failed_count += 1
            except Exception:
                pass
    return failed_count >= 5

def login(username: str, password: str) -> dict | None:
    """
    Authenticate user. Returns user dict or None.
    Locks out account if 5 or more failed attempts in last 5 minutes.
    """
    if not username or not password:
        return None
    
    clean_user = username.strip().lower()
    
    if is_locked_out(clean_user):
        log("login_locked", clean_user, {"username": clean_user, "reason": "Rate limited: 5+ failed attempts."})
        return None
    
    if not os.path.exists(USERS_CSV):
        return None
        
    try:
        df = pd.read_csv(USERS_CSV)
        match = df[df["username"].str.lower() == clean_user]
        if match.empty:
            log("login_failed", clean_user, {"username": clean_user, "reason": "Invalid credentials"})
            return None
            
        row = match.iloc[0]
        if verify_hash(password, str(row["salt"]), str(row["password_hash"])):
            user_dict = {
                "username": str(row["username"]),
                "role": str(row["role"]),
                "rank": int(row["rank"]) if pd.notna(row["rank"]) else 0,
                "staff_id": str(row["staff_id"]) if pd.notna(row["staff_id"]) else "",
                "section_id": str(row["section_id"]) if pd.notna(row["section_id"]) else ""
            }
            log("login_ok", user_dict["username"], {"role": user_dict["role"]})
            return user_dict
        else:
            log("login_failed", clean_user, {"username": clean_user, "reason": "Invalid credentials"})
            return None
    except Exception as e:
        log("login_failed", clean_user, {"username": clean_user, "error": str(e)})
        return None

def can(role: str, action: str) -> bool:
    """Check if a role is permitted to perform action."""
    role_perms = PERMISSIONS.get(role.lower(), {})
    return role_perms.get(action, False)

def deny(role: str, action: str, user: str = "unknown"):
    """Helper when an action is denied."""
    log("denied_action", user, {"role": role, "action": action})
    return False

def check_feedback_limit(username: str) -> bool:
    """At most 5 feedback messages per student per hour."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    entries = read_log()
    count = 0
    for e in entries:
        if e.get("event") == "feedback_submitted" and e.get("user") == username:
            try:
                t = datetime.fromisoformat(e.get("timestamp"))
                if t >= cutoff:
                    count += 1
            except Exception:
                pass
    return count < 5
