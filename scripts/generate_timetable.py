"""
Timetable data generator for ECHO Decision Safety Agent.
Generates sections.csv, labs.csv, staff.csv, slots.csv, and initializes slots_live.csv and requests.json.
"""
import os
import json
import random
import pandas as pd

random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# 1. Sections (S01 to S10)
sections_data = [
    {"section_id": "S01", "name": "Computer Science A", "size": 52},
    {"section_id": "S02", "name": "Computer Science B", "size": 56},
    {"section_id": "S03", "name": "Artificial Intelligence", "size": 54},
    {"section_id": "S04", "name": "Data Science", "size": 58},
    {"section_id": "S05", "name": "Software Engineering", "size": 50},
    {"section_id": "S06", "name": "Cybersecurity", "size": 48},
    {"section_id": "S07", "name": "Information Systems", "size": 57},
    {"section_id": "S08", "name": "Cloud Computing", "size": 53},
    {"section_id": "S09", "name": "Robotics & IoT", "size": 55},
    {"section_id": "S10", "name": "Computer Networks", "size": 49},
]
df_sections = pd.DataFrame(sections_data)
df_sections.to_csv(os.path.join(DATA_DIR, "sections.csv"), index=False)

# 2. Labs (L1 to L9) - Capacities 45 to 60.
# L8 (cap 50) and L9 (cap 48) planted too small for S04 (58) and S07 (57)
labs_data = [
    {"lab_id": "L1", "name": "Turing Lab (Systems)", "capacity": 60},
    {"lab_id": "L2", "name": "Lovelace Lab (AI/ML)", "capacity": 60},
    {"lab_id": "L3", "name": "Hopper Lab (Networks)", "capacity": 58},
    {"lab_id": "L4", "name": "Von Neumann Lab (Robotics)", "capacity": 60},
    {"lab_id": "L5", "name": "Shannon Lab (Information)", "capacity": 58},
    {"lab_id": "L6", "name": "Knuth Lab (Open Practice)", "capacity": 60},  # Roomy buffer lab
    {"lab_id": "L7", "name": "Ritchie Lab (Operating Systems)", "capacity": 58},
    {"lab_id": "L8", "name": "Berners-Lee Lab (Web Systems)", "capacity": 50},  # Planted small
    {"lab_id": "L9", "name": "Cerf Lab (Cybersecurity)", "capacity": 48},      # Planted small
]
df_labs = pd.DataFrame(labs_data)
df_labs.to_csv(os.path.join(DATA_DIR, "labs.csv"), index=False)

# 3. Staff (T1 to T8)
# Ranks: Professor (3), Associate (2), Assistant (1)
staff_data = [
    {"staff_id": "T1", "name": "Prof. Eleanor Vance", "rank": "Professor"},       # rank 3
    {"staff_id": "T2", "name": "Prof. Marcus Reed", "rank": "Professor"},         # rank 3
    {"staff_id": "T3", "name": "Dr. Sophia Chen", "rank": "Associate"},          # rank 2
    {"staff_id": "T4", "name": "Dr. Liam Davies", "rank": "Assistant"},           # rank 1
    {"staff_id": "T5", "name": "Dr. Amara Patel", "rank": "Associate"},          # rank 2
    {"staff_id": "T6", "name": "Dr. David Kim", "rank": "Associate"},            # rank 2
    {"staff_id": "T7", "name": "Dr. Elena Rostova", "rank": "Assistant"},        # rank 1
    {"staff_id": "T8", "name": "Dr. Tariq Al-Mansoor", "rank": "Assistant"},     # rank 1
]
df_staff = pd.DataFrame(staff_data)
df_staff.to_csv(os.path.join(DATA_DIR, "staff.csv"), index=False)

# 4. Slots (Monday to Friday, hours 8 to 16)
days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
hours = list(range(8, 17)) # 8:00 to 16:00

slots = []
slot_counter = 1

def make_slot(section_id, day, hour, kind, lab_id, staff_id, subject):
    global slot_counter
    sid = f"SL{slot_counter:03d}"
    slot_counter += 1
    return {
        "slot_id": sid,
        "section_id": section_id,
        "day": day,
        "hour": hour,
        "kind": kind,
        "lab_id": lab_id if kind == "lab" else "",
        "staff_id": staff_id,
        "subject": subject
    }

subjects = {
    "T1": ["Computer Architecture", "Advanced OS", "OS Lab"],
    "T2": ["Artificial Intelligence", "Neural Networks", "AI Systems Lab"],
    "T3": ["Database Systems", "Big Data Analytics", "DB Lab"],
    "T4": ["Web Technologies", "Cloud Infrastructure", "Web Lab"],
    "T5": ["Algorithms & Complexity", "Data Structures", "Algo Lab"],
    "T6": ["Computer Networks", "Distributed Systems", "Networks Lab"],
    "T7": ["Software Testing", "Security Engineering", "Security Lab"],
    "T8": ["Human Computer Interaction", "Mobile App Dev", "Mobile Lab"]
}

occupied_sec_day_hour = set()
occupied_staff_day_hour = set()
occupied_lab_day_hour = set()

# Seeded Demo Slots:
# R1 demo slot: Section S03, Tuesday 10:00 Lab in L3 with T2 (Prof Marcus Reed)
r1_slot = make_slot("S03", "Tue", 10, "lab", "L3", "T2", "AI Systems Lab")
slots.append(r1_slot)
occupied_sec_day_hour.add(("S03", "Tue", 10))
occupied_staff_day_hour.add(("T2", "Tue", 10))
occupied_lab_day_hour.add(("L3", "Tue", 10))

# Planted problem 1: S04 (size 58) in L8 (cap 50) on Mon 09:00 with T4
planted_1 = make_slot("S04", "Mon", 9, "lab", "L8", "T4", "Web Lab")
slots.append(planted_1)
occupied_sec_day_hour.add(("S04", "Mon", 9))
occupied_staff_day_hour.add(("T4", "Mon", 9))
occupied_lab_day_hour.add(("L8", "Mon", 9))

# Planted problem 2: S07 (size 57) in L9 (cap 48) on Wed 11:00 with T7
planted_2 = make_slot("S07", "Wed", 11, "lab", "L9", "T7", "Security Lab")
slots.append(planted_2)
occupied_sec_day_hour.add(("S07", "Wed", 11))
occupied_staff_day_hour.add(("T7", "Wed", 11))
occupied_lab_day_hour.add(("L9", "Wed", 11))

# Dedicated slots for R2, R3, R4 demo
# R2: S02 has lab on Wed 14:00 with T3 in L1
r2_slot = make_slot("S02", "Wed", 14, "lab", "L1", "T3", "DB Lab")
slots.append(r2_slot)
occupied_sec_day_hour.add(("S02", "Wed", 14))
occupied_staff_day_hour.add(("T3", "Wed", 14))
occupied_lab_day_hour.add(("L1", "Wed", 14))

# Keep L2 busy on Wed 15:00 with S05 and T6
l2_busy = make_slot("S05", "Wed", 15, "lab", "L2", "T6", "Networks Lab")
slots.append(l2_busy)
occupied_sec_day_hour.add(("S05", "Wed", 15))
occupied_staff_day_hour.add(("T6", "Wed", 15))
occupied_lab_day_hour.add(("L2", "Wed", 15))

# R3 current slot for T1: S01 Thu 09:00 in L5, wanting to move to Thu 12:00 in L4
r3_slot = make_slot("S01", "Thu", 9, "lab", "L5", "T1", "OS Lab")
slots.append(r3_slot)
occupied_sec_day_hour.add(("S01", "Thu", 9))
occupied_staff_day_hour.add(("T1", "Thu", 9))
occupied_lab_day_hour.add(("L5", "Thu", 9))

# R4 current slot for T4: S06 Thu 15:00 in L7, wanting to move to Thu 12:00 in L4
r4_slot = make_slot("S06", "Thu", 15, "lab", "L7", "T4", "Web Lab")
slots.append(r4_slot)
occupied_sec_day_hour.add(("S06", "Thu", 15))
occupied_staff_day_hour.add(("T4", "Thu", 15))
occupied_lab_day_hour.add(("L7", "Thu", 15))

# Assign lab sessions across ALL labs (L1 to L9) for each section
# L8 cap is 50 -> fits S05 (50), S06 (48), S10 (49)
# L9 cap is 48 -> fits S06 (48)
# L1-L7 caps are 58-60 -> fit all sections
sec_caps = dict(zip(df_sections["section_id"], df_sections["size"]))

# Structured, clash-free lab session assignments so EVERY lab has active sections
planned_labs = [
    # Mon
    ("S01", "Mon", 11, "L1", "T1", "OS Lab"),
    ("S02", "Mon", 13, "L2", "T2", "AI Systems Lab"),
    ("S03", "Mon", 14, "L3", "T6", "Networks Lab"),
    ("S05", "Mon", 15, "L8", "T4", "Web Lab"),          # S05 size 50 <= L8 cap 50 (fits!)
    ("S06", "Mon", 16, "L9", "T7", "Security Lab"),     # S06 size 48 <= L9 cap 48 (fits!)
    ("S08", "Mon", 10, "L6", "T8", "Mobile Lab"),       # Knuth Lab active
    ("S09", "Mon", 12, "L4", "T5", "Algo Lab"),
    ("S10", "Mon", 15, "L7", "T3", "DB Lab"),

    # Tue
    ("S01", "Tue", 8,  "L7", "T3", "DB Lab"),
    ("S02", "Tue", 9,  "L5", "T5", "Algo Lab"),
    # S03 Tue 10 is R1 (L3)
    ("S04", "Tue", 11, "L1", "T1", "OS Lab"),
    ("S05", "Tue", 13, "L4", "T6", "Networks Lab"),
    ("S06", "Tue", 14, "L6", "T4", "Web Lab"),          # Knuth Lab active
    ("S07", "Tue", 15, "L2", "T2", "AI Systems Lab"),
    ("S08", "Tue", 16, "L3", "T7", "Security Lab"),
    ("S09", "Tue", 9,  "L6", "T8", "Mobile Lab"),       # Knuth Lab active
    ("S10", "Tue", 14, "L8", "T4", "Web Lab"),          # S10 size 49 <= L8 cap 50 (fits!)

    # Wed
    ("S01", "Wed", 10, "L3", "T6", "Networks Lab"),
    ("S03", "Wed", 13, "L4", "T5", "Algo Lab"),
    # S02 Wed 14 is R2 (L1)
    # S05 Wed 15 is L2
    ("S04", "Wed", 16, "L5", "T1", "OS Lab"),
    ("S06", "Wed", 8,  "L9", "T7", "Security Lab"),     # S06 size 48 <= L9 cap 48 (fits!)
    ("S08", "Wed", 12, "L7", "T3", "DB Lab"),
    ("S09", "Wed", 14, "L6", "T2", "AI Systems Lab"),   # Knuth Lab active
    ("S10", "Wed", 10, "L1", "T8", "Mobile Lab"),

    # Thu
    # S01 Thu 9 is R3 (L5)
    ("S02", "Thu", 11, "L3", "T6", "Networks Lab"),
    ("S03", "Thu", 13, "L2", "T2", "AI Systems Lab"),
    ("S04", "Thu", 14, "L1", "T1", "OS Lab"),
    ("S05", "Thu", 16, "L5", "T5", "Algo Lab"),
    # S06 Thu 15 is R4 (L7)
    ("S07", "Thu", 8,  "L4", "T8", "Mobile Lab"),
    ("S08", "Thu", 14, "L6", "T4", "Web Lab"),          # Knuth Lab active
    ("S09", "Thu", 16, "L7", "T7", "Security Lab"),
    ("S10", "Thu", 9,  "L8", "T3", "DB Lab"),           # S10 size 49 <= L8 cap 50 (fits!)

    # Fri
    ("S01", "Fri", 14, "L2", "T2", "AI Systems Lab"),
    ("S02", "Fri", 10, "L4", "T6", "Networks Lab"),
    ("S03", "Fri", 15, "L7", "T3", "DB Lab"),
    ("S04", "Fri", 8,  "L6", "T8", "Mobile Lab"),       # Knuth Lab active
    ("S05", "Fri", 9,  "L1", "T1", "OS Lab"),
    ("S06", "Fri", 11, "L3", "T5", "Algo Lab"),
    ("S07", "Fri", 13, "L5", "T4", "Web Lab"),
    ("S08", "Fri", 15, "L2", "T2", "AI Systems Lab"),
    ("S09", "Fri", 10, "L1", "T1", "OS Lab"),
    ("S10", "Fri", 12, "L6", "T7", "Security Lab"),     # Knuth Lab active
]

for sec, day, hour, lab, stf, subj in planned_labs:
    if (sec, day, hour) in occupied_sec_day_hour or (stf, day, hour) in occupied_staff_day_hour or (lab, day, hour) in occupied_lab_day_hour:
        continue
    slot = make_slot(sec, day, hour, "lab", lab, stf, subj)
    slots.append(slot)
    occupied_sec_day_hour.add((sec, day, hour))
    occupied_staff_day_hour.add((stf, day, hour))
    occupied_lab_day_hour.add((lab, day, hour))

# Fill in theory classes for all sections across empty periods
staff_ids = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"]

for sec in df_sections["section_id"]:
    for day in days:
        for hour in [8, 9, 10, 11, 13, 14, 15, 16]:
            if (sec, day, hour) in occupied_sec_day_hour:
                continue
            # Keep reasonable density per section
            if random.random() > 0.60:
                continue

            # Pick free staff
            random.shuffle(staff_ids)
            chosen_staff = None
            for stf in staff_ids:
                if (stf, day, hour) not in occupied_staff_day_hour:
                    chosen_staff = stf
                    break
            if not chosen_staff:
                continue

            subj = subjects[chosen_staff][0 if hour < 12 else 1]
            slot = make_slot(sec, day, hour, "theory", "", chosen_staff, subj)
            slots.append(slot)
            occupied_sec_day_hour.add((sec, day, hour))
            occupied_staff_day_hour.add((chosen_staff, day, hour))

df_slots = pd.DataFrame(slots)
df_slots.to_csv(os.path.join(DATA_DIR, "slots.csv"), index=False)
df_slots.to_csv(os.path.join(DATA_DIR, "slots_live.csv"), index=False)

# Seeded requests (R1, R2, R3, R4)
requests_data = [
    {
        "id": "R001",
        "kind": "class",
        "requester": "t2",
        "role": "staff",
        "rank": 3,
        "created": "2026-12-01 09:15:00",
        "status": "pending",
        "payload": {
            "slot_id": r1_slot["slot_id"],
            "new_day": "Tue",
            "new_hour": 10,
            "new_lab_id": "L6"
        },
        "note": "Section 3 AI Systems Lab move to Knuth Lab (L6) for high-performance GPUs"
    },
    {
        "id": "R002",
        "kind": "class",
        "requester": "t3",
        "role": "staff",
        "rank": 2,
        "created": "2026-12-01 10:00:00",
        "status": "pending",
        "payload": {
            "slot_id": r2_slot["slot_id"],
            "new_day": "Wed",
            "new_hour": 15,
            "new_lab_id": "L2"
        },
        "note": "Move Section 2 DB Lab to Lovelace Lab (L2) - causes clash"
    },
    {
        "id": "R003",
        "kind": "class",
        "requester": "t1",
        "role": "staff",
        "rank": 3,
        "created": "2026-12-01 10:30:00",
        "status": "pending",
        "payload": {
            "slot_id": r3_slot["slot_id"],
            "new_day": "Thu",
            "new_hour": 12,
            "new_lab_id": "L4"
        },
        "note": "Prof. Vance requesting Von Neumann Lab (L4) for Operating Systems Lab"
    },
    {
        "id": "R004",
        "kind": "class",
        "requester": "t4",
        "role": "staff",
        "rank": 1,
        "created": "2026-12-01 11:00:00",
        "status": "pending",
        "payload": {
            "slot_id": r4_slot["slot_id"],
            "new_day": "Thu",
            "new_hour": 12,
            "new_lab_id": "L4"
        },
        "note": "Dr. Davies requesting Von Neumann Lab (L4) for Web Cloud Lab"
    }
]

with open(os.path.join(DATA_DIR, "requests.json"), "w") as f:
    json.dump(requests_data, f, indent=2)

print("Generated enriched timetable data with active lab assignments across all labs!")
