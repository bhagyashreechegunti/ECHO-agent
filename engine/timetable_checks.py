"""
Timetable conflict and constraint checks for ECHO Decision Safety Agent.
Four checks: section clash, staff clash, lab double-booking, and lab too small.
Optimized for high-performance interactive simulation.
"""
from collections import defaultdict
import pandas as pd

def find_section_clashes(slots: pd.DataFrame) -> list:
    """Find sections scheduled for two classes at the same day and hour."""
    records = slots.to_dict('records') if isinstance(slots, pd.DataFrame) else slots
    sec_map = defaultdict(list)
    for r in records:
        sec = r.get("section_id")
        day = r.get("day")
        hour = int(r.get("hour"))
        sec_map[(sec, day, hour)].append(r)
        
    clashes = []
    for (sec, day, hour), group in sec_map.items():
        if len(group) > 1:
            clashes.append({
                "type": "section_clash",
                "section_id": sec,
                "day": day,
                "hour": hour,
                "slots": [x["slot_id"] for x in group],
                "subjects": [x["subject"] for x in group],
                "details": f"Section {sec} has {len(group)} classes at {day} {hour:02d}:00 ({', '.join([x['subject'] for x in group])})"
            })
    return clashes

def find_staff_clashes(slots: pd.DataFrame) -> list:
    """Find staff members assigned to two classes at the same day and hour."""
    records = slots.to_dict('records') if isinstance(slots, pd.DataFrame) else slots
    staff_map = defaultdict(list)
    for r in records:
        staff = str(r.get("staff_id", "")).strip()
        if staff and staff.lower() not in ("none", "nan", ""):
            day = r.get("day")
            hour = int(r.get("hour"))
            staff_map[(staff, day, hour)].append(r)
            
    clashes = []
    for (staff, day, hour), group in staff_map.items():
        if len(group) > 1:
            clashes.append({
                "type": "staff_clash",
                "staff_id": staff,
                "day": day,
                "hour": hour,
                "slots": [x["slot_id"] for x in group],
                "sections": [x["section_id"] for x in group],
                "details": f"Staff member {staff} double-assigned at {day} {hour:02d}:00 across sections {', '.join([x['section_id'] for x in group])}"
            })
    return clashes

def find_lab_double_bookings(slots: pd.DataFrame) -> list:
    """Find labs booked more than once in the same day and hour."""
    records = slots.to_dict('records') if isinstance(slots, pd.DataFrame) else slots
    lab_map = defaultdict(list)
    for r in records:
        if r.get("kind") == "lab":
            lab = str(r.get("lab_id", "")).strip()
            if lab and lab.lower() not in ("none", "nan", ""):
                day = r.get("day")
                hour = int(r.get("hour"))
                lab_map[(lab, day, hour)].append(r)
                
    clashes = []
    for (lab, day, hour), group in lab_map.items():
        if len(group) > 1:
            clashes.append({
                "type": "lab_double_booking",
                "lab_id": lab,
                "day": day,
                "hour": hour,
                "slots": [x["slot_id"] for x in group],
                "sections": [x["section_id"] for x in group],
                "details": f"Lab {lab} double-booked at {day} {hour:02d}:00 by sections {', '.join([x['section_id'] for x in group])}"
            })
    return clashes

def find_lab_too_small(slots: pd.DataFrame, labs: pd.DataFrame, sections: pd.DataFrame) -> list:
    """Find lab slots where section size exceeds lab capacity."""
    records = slots.to_dict('records') if isinstance(slots, pd.DataFrame) else slots
    sec_size = dict(zip(sections["section_id"], sections["size"]))
    lab_cap = dict(zip(labs["lab_id"], labs["capacity"]))
    
    too_small = []
    for r in records:
        if r.get("kind") == "lab":
            lab = str(r.get("lab_id", "")).strip()
            if lab and lab.lower() not in ("none", "nan", ""):
                sec = r.get("section_id")
                size = sec_size.get(sec, 0)
                cap = lab_cap.get(lab, 999)
                if size > cap:
                    over_pct = round(((size - cap) / cap) * 100, 1)
                    too_small.append({
                        "type": "lab_too_small",
                        "slot_id": r["slot_id"],
                        "section_id": sec,
                        "lab_id": lab,
                        "day": r["day"],
                        "hour": int(r["hour"]),
                        "size": size,
                        "capacity": cap,
                        "over_pct": over_pct,
                        "details": f"Lab {lab} (capacity {cap}) too small for Section {sec} ({size} students, +{over_pct}% overflow) at {r['day']} {int(r['hour']):02d}:00"
                    })
    return too_small

def run_timetable_checks(slots: pd.DataFrame, labs: pd.DataFrame, sections: pd.DataFrame) -> dict:
    """Runs all 4 checks and returns dictionary."""
    records = slots.to_dict('records') if isinstance(slots, pd.DataFrame) else slots
    sec_size = dict(zip(sections["section_id"], sections["size"]))
    lab_cap = dict(zip(labs["lab_id"], labs["capacity"]))

    sec_map = defaultdict(list)
    staff_map = defaultdict(list)
    lab_map = defaultdict(list)
    too_small = []

    for r in records:
        day = r.get("day")
        hour = int(r.get("hour"))
        sec = r.get("section_id")
        staff = str(r.get("staff_id", "")).strip()
        kind = r.get("kind")
        lab = str(r.get("lab_id", "")).strip()

        sec_map[(sec, day, hour)].append(r)

        if staff and staff.lower() not in ("none", "nan", ""):
            staff_map[(staff, day, hour)].append(r)

        if kind == "lab" and lab and lab.lower() not in ("none", "nan", ""):
            lab_map[(lab, day, hour)].append(r)
            size = sec_size.get(sec, 0)
            cap = lab_cap.get(lab, 999)
            if size > cap:
                over_pct = round(((size - cap) / cap) * 100, 1)
                too_small.append({
                    "type": "lab_too_small",
                    "slot_id": r["slot_id"],
                    "section_id": sec,
                    "lab_id": lab,
                    "day": day,
                    "hour": hour,
                    "size": size,
                    "capacity": cap,
                    "over_pct": over_pct,
                    "details": f"Lab {lab} (capacity {cap}) too small for Section {sec} ({size} students, +{over_pct}% overflow) at {day} {hour:02d}:00"
                })

    section_clashes = [
        {
            "type": "section_clash",
            "section_id": sec,
            "day": day,
            "hour": hour,
            "slots": [x["slot_id"] for x in group],
            "subjects": [x["subject"] for x in group],
            "details": f"Section {sec} has {len(group)} classes at {day} {hour:02d}:00 ({', '.join([x['subject'] for x in group])})"
        }
        for (sec, day, hour), group in sec_map.items() if len(group) > 1
    ]

    staff_clashes = [
        {
            "type": "staff_clash",
            "staff_id": staff,
            "day": day,
            "hour": hour,
            "slots": [x["slot_id"] for x in group],
            "sections": [x["section_id"] for x in group],
            "details": f"Staff member {staff} double-assigned at {day} {hour:02d}:00 across sections {', '.join([x['section_id'] for x in group])}"
        }
        for (staff, day, hour), group in staff_map.items() if len(group) > 1
    ]

    lab_double_bookings = [
        {
            "type": "lab_double_booking",
            "lab_id": lab,
            "day": day,
            "hour": hour,
            "slots": [x["slot_id"] for x in group],
            "sections": [x["section_id"] for x in group],
            "details": f"Lab {lab} double-booked at {day} {hour:02d}:00 by sections {', '.join([x['section_id'] for x in group])}"
        }
        for (lab, day, hour), group in lab_map.items() if len(group) > 1
    ]

    return {
        "section_clash": section_clashes,
        "staff_clash": staff_clashes,
        "lab_double_booking": lab_double_bookings,
        "lab_too_small": too_small
    }

