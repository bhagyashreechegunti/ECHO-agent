"""
Timetable loader and live updater for ECHO Decision Safety Agent.
"""
import os
import shutil
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
SECTIONS_CSV = os.path.join(DATA_DIR, "sections.csv")
LABS_CSV = os.path.join(DATA_DIR, "labs.csv")
STAFF_CSV = os.path.join(DATA_DIR, "staff.csv")
SLOTS_CSV = os.path.join(DATA_DIR, "slots.csv")
SLOTS_LIVE_CSV = os.path.join(DATA_DIR, "slots_live.csv")
REQUESTS_JSON = os.path.join(DATA_DIR, "requests.json")

def load_timetable():
    """
    Returns (sections, labs, staff, slots) as four tables.
    Reads slots_live.csv, creating it from slots.csv if missing.
    """
    if not os.path.exists(SLOTS_LIVE_CSV):
        if os.path.exists(SLOTS_CSV):
            shutil.copyfile(SLOTS_CSV, SLOTS_LIVE_CSV)
            
    sections = pd.read_csv(SECTIONS_CSV)
    labs = pd.read_csv(LABS_CSV)
    staff = pd.read_csv(STAFF_CSV)
    slots = pd.read_csv(SLOTS_LIVE_CSV)
    
    # Fill empty lab_ids with empty string
    slots["lab_id"] = slots["lab_id"].fillna("").astype(str)
    
    # Validation checks on load
    if (labs["capacity"] < 1).any() or (labs["capacity"] > 1000).any():
        raise ValueError("Invalid lab capacity found outside 1-1000 range.")
    valid_days = {"Mon", "Tue", "Wed", "Thu", "Fri"}
    if not set(slots["day"]).issubset(valid_days):
        raise ValueError("Slot contains invalid day.")
    if (slots["hour"] < 8).any() or (slots["hour"] > 16).any():
        raise ValueError("Slot contains invalid hour outside 8-16.")
        
    return sections, labs, staff, slots

def apply_change(slots: pd.DataFrame, change: dict) -> pd.DataFrame:
    """
    A changed COPY of slots. The original DataFrame is never edited in place.
    change: {"slot_id": "...", "new_day": "...", "new_hour": int, "new_lab_id": "..."}
    """
    slots_copy = slots.copy()
    slot_id = change.get("slot_id")
    mask = slots_copy["slot_id"] == slot_id
    if not mask.any():
        raise KeyError(f"Slot ID '{slot_id}' not found in timetable.")
        
    if "new_day" in change:
        slots_copy.loc[mask, "day"] = change["new_day"]
    if "new_hour" in change:
        slots_copy.loc[mask, "hour"] = int(change["new_hour"])
    if "new_lab_id" in change:
        slots_copy.loc[mask, "lab_id"] = change["new_lab_id"]
        # If moving to a lab, ensure kind is lab
        if change["new_lab_id"]:
            slots_copy.loc[mask, "kind"] = "lab"
            
    return slots_copy

def commit_change(change: dict):
    """
    Applies the change to live table and writes to slots_live.csv.
    """
    _, _, _, slots = load_timetable()
    updated = apply_change(slots, change)
    updated.to_csv(SLOTS_LIVE_CSV, index=False)
    return updated

def reset_demo():
    """
    Restores slots.csv over slots_live.csv and re-creates seeded demo requests R1 to R4.
    """
    from scripts.generate_timetable import DATA_DIR as GEN_DIR
    import scripts.generate_timetable as gen
    # Re-run generate_timetable logic or restore
    if os.path.exists(SLOTS_CSV):
        shutil.copyfile(SLOTS_CSV, SLOTS_LIVE_CSV)
    # Re-run generator to ensure fresh seeded requests
    os.system("python scripts/generate_timetable.py")
    return True
