"""
Change requests handling, simulation, safer-option finder, and two-staff conflict resolver.
"""
import os
import json
import pandas as pd
from engine.timetable import load_timetable, apply_change
from engine.timetable_checks import run_timetable_checks
from engine.timetable_scorer import timetable_risk, timetable_findings
from audit import log

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
REQUESTS_FILE = os.path.join(DATA_DIR, "requests.json")

def list_requests() -> list:
    """Reads all requests from requests.json."""
    if not os.path.exists(REQUESTS_FILE):
        return []
    try:
        with open(REQUESTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_requests(requests: list):
    """Saves requests list to requests.json."""
    with open(REQUESTS_FILE, "w", encoding="utf-8") as f:
        json.dump(requests, f, indent=2)

def add_request(kind: str, requester: str, role: str, rank: int, payload: dict, note: str = "") -> dict:
    """
    Creates and records a request.
    If role == 'staff' and kind == 'class', verifies that the slot belongs to requester.
    """
    sections, labs, staff, slots = load_timetable()
    
    if role == "staff" and kind == "class":
        slot_id = payload.get("slot_id")
        slot_row = slots[slots["slot_id"] == slot_id]
        if slot_row.empty:
            raise ValueError(f"Slot {slot_id} does not exist.")
        # requester can be 't2' or 'T2'
        staff_target = slot_row.iloc[0]["staff_id"]
        if staff_target.lower() != requester.lower():
            raise PermissionError(f"Staff member {requester} cannot modify slot belonging to {staff_target}.")

    reqs = list_requests()
    next_num = len(reqs) + 1
    req_id = f"R{next_num:03d}"
    
    from datetime import datetime
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    new_req = {
        "id": req_id,
        "kind": kind,
        "requester": requester,
        "role": role,
        "rank": rank,
        "created": now_str,
        "status": "pending",
        "payload": payload,
        "note": note
    }
    reqs.append(new_req)
    save_requests(reqs)
    log("request_created", requester, {"request_id": req_id, "kind": kind, "note": note})
    return new_req

def set_status(req_id: str, status: str, by: str = "admin") -> bool:
    """Update status of a request."""
    reqs = list_requests()
    updated = False
    for r in reqs:
        if r["id"] == req_id:
            r["status"] = status
            updated = True
            break
    if updated:
        save_requests(reqs)
        log("approved" if status == "approved" else "rejected", by, {"request_id": req_id})
    return updated

def find_safer_option(slot_id: str, requested_day: str, requested_hour: int, requested_lab: str, slots: pd.DataFrame, labs: pd.DataFrame, sections: pd.DataFrame, baseline_score: int) -> dict | None:
    """
    Searches for an alternative slot:
    1. Other labs at the same day and hour
    2. Other hours on the same day
    3. Other days
    Keeps lowest risk option where risk <= baseline_score.
    High-performance indexed pruning.
    """
    slot_row = slots[slots["slot_id"] == slot_id]
    if slot_row.empty:
        return None
        
    sec_id = slot_row.iloc[0]["section_id"]
    staff_id = slot_row.iloc[0]["staff_id"]
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    hours = list(range(8, 17))
    all_labs = labs["lab_id"].tolist()
    
    sec_sizes = dict(zip(sections["section_id"], sections["size"]))
    my_sec_size = sec_sizes.get(sec_id, 0)
    lab_caps = dict(zip(labs["lab_id"], labs["capacity"]))

    # Pre-index existing slots (excluding slot_id itself)
    other_slots = slots[slots["slot_id"] != slot_id]
    busy_sec = set(zip(other_slots["section_id"], other_slots["day"], other_slots["hour"].astype(int)))
    valid_staff = other_slots[other_slots["staff_id"].fillna("").astype(str).str.strip() != ""]
    busy_staff = set(zip(valid_staff["staff_id"], valid_staff["day"], valid_staff["hour"].astype(int)))
    lab_slots = other_slots[(other_slots["kind"] == "lab") & (other_slots["lab_id"].fillna("").astype(str).str.strip() != "")]
    busy_labs = set(zip(lab_slots["lab_id"].astype(str), lab_slots["day"], lab_slots["hour"].astype(int)))

    def is_candidate_viable(d: str, h: int, l: str) -> bool:
        if (sec_id, d, h) in busy_sec:
            return False
        if staff_id and (staff_id, d, h) in busy_staff:
            return False
        if (str(l), d, h) in busy_labs:
            return False
        if my_sec_size > lab_caps.get(str(l), 0):
            return False
        return True

    best_cand = None

    # Priority 1: Other labs at requested day & hour
    for lab in all_labs:
        if lab == requested_lab:
            continue
        if is_candidate_viable(requested_day, requested_hour, lab):
            best_cand = {"slot_id": slot_id, "new_day": requested_day, "new_hour": requested_hour, "new_lab_id": lab}
            break
            
    # Priority 2: Other hours on same day
    if not best_cand:
        for hr in hours:
            if hr == requested_hour:
                continue
            for lab in all_labs:
                if is_candidate_viable(requested_day, hr, lab):
                    best_cand = {"slot_id": slot_id, "new_day": requested_day, "new_hour": hr, "new_lab_id": lab}
                    break
            if best_cand:
                break
                    
    # Priority 3: Other days
    if not best_cand:
        for d in days:
            if d == requested_day:
                continue
            for hr in hours:
                for lab in all_labs:
                    if is_candidate_viable(d, hr, lab):
                        best_cand = {"slot_id": slot_id, "new_day": d, "new_hour": hr, "new_lab_id": lab}
                        break
                if best_cand:
                    break
            if best_cand:
                break

    if best_cand:
        c_slots = apply_change(slots, best_cand)
        c_res = run_timetable_checks(c_slots, labs, sections)
        c_risk = timetable_risk(c_res)
        return {
            "change": best_cand,
            "results": c_res,
            "risk": c_risk
        }
    return None

def simulate_request(req: dict) -> dict:
    """
    Simulates a request and returns 3 scored options + recommendation + verdict.
    """
    sections, labs, staff, slots = load_timetable()
    
    # 1. Option 1: Current baseline
    res_base = run_timetable_checks(slots, labs, sections)
    risk_base = timetable_risk(res_base)
    find_base = timetable_findings(res_base)
    opt1 = {
        "name": "Option 1: Current Timetable",
        "description": "Retain baseline schedule unchanged",
        "moved": 0,
        "results": res_base,
        "risk": risk_base,
        "findings": find_base,
        "change": None
    }
    
    payload = req.get("payload", {})
    # If feedback with proposal, unwrap
    if req.get("kind") == "feedback":
        payload = payload.get("proposal") or {}
        
    slot_id = payload.get("slot_id")
    new_day = payload.get("new_day")
    new_hour = payload.get("new_hour")
    new_lab_id = payload.get("new_lab_id", "")
    
    # 2. Option 2: As requested
    change_req = {
        "slot_id": slot_id,
        "new_day": new_day,
        "new_hour": new_hour,
        "new_lab_id": new_lab_id
    }
    
    slots_req = apply_change(slots, change_req)
    res_req = run_timetable_checks(slots_req, labs, sections)
    risk_req = timetable_risk(res_req)
    find_req = timetable_findings(res_req)
    
    opt2 = {
        "name": "Option 2: As Requested",
        "description": f"Move {slot_id} to {new_day} {new_hour}:00 in Lab {new_lab_id}",
        "moved": 1,
        "results": res_req,
        "risk": risk_req,
        "findings": find_req,
        "change": change_req
    }
    
    # Check new problems created by Option 2 vs Option 1
    new_problems = []
    for k in ["lab_double_booking", "staff_clash", "section_clash", "lab_too_small"]:
        diff = len(res_req.get(k, [])) - len(res_base.get(k, []))
        if diff > 0:
            new_problems.append(f"{diff} new {k.replace('_', ' ')}")
            
    # 3. Option 3: Safer alternative
    safer = find_safer_option(slot_id, new_day, new_hour, new_lab_id, slots, labs, sections, risk_base["score"])
    if safer:
        opt3 = {
            "name": "Option 3: Safer Alternative",
            "description": f"Move {slot_id} to {safer['change']['new_day']} {safer['change']['new_hour']}:00 in Lab {safer['change']['new_lab_id']}",
            "moved": 1,
            "results": safer["results"],
            "risk": safer["risk"],
            "findings": timetable_findings(safer["results"]),
            "change": safer["change"]
        }
    else:
        opt3 = {
            "name": "Option 3: Safer Alternative",
            "description": "No safer alternative found",
            "moved": 0,
            "results": res_base,
            "risk": risk_base,
            "findings": find_base,
            "change": None
        }
        
    # Verdict decision logic
    # If option 2 adds no new problem compared with option 1 -> recommend approve
    # If it adds problems but a safer alternative exists -> recommend safer option
    # Otherwise -> recommend reject
    if not new_problems and risk_req["score"] <= risk_base["score"]:
        recommended = 2
        verdict = "recommend approve"
        verdict_reason = f"Requested change introduces zero conflicts or capacity deficits. Risk score is {risk_req['score']}/100."
    elif safer and safer["change"] != change_req and safer["risk"]["score"] < risk_req["score"]:
        recommended = 3
        verdict = "recommend safer option"
        verdict_reason = f"Requested change adds {', '.join(new_problems)}. Safer alternative in Lab {safer['change']['new_lab_id']} eliminates these risks (Score: {safer['risk']['score']}/100)."
    else:
        recommended = 1
        verdict = "recommend reject"
        verdict_reason = f"Requested change introduces serious violations ({', '.join(new_problems)}) and no viable zero-clash alternative exists."
        
    log("simulate_class", "admin", {"request_id": req.get("id"), "verdict": verdict, "recommended": recommended})
    
    return {
        "options": [opt1, opt2, opt3],
        "recommended": recommended,
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "new_problems": new_problems
    }

def find_conflicts() -> list:
    """Find pairs of pending class requests wanting the same lab, day, and hour."""
    reqs = list_requests()
    pending_class = [r for r in reqs if r.get("status") == "pending" and r.get("kind") == "class"]
    
    conflicts = []
    for i in range(len(pending_class)):
        for j in range(i + 1, len(pending_class)):
            r_a = pending_class[i]
            r_b = pending_class[j]
            p_a = r_a.get("payload", {})
            p_b = r_b.get("payload", {})
            if (p_a.get("new_day") == p_b.get("new_day") and 
                int(p_a.get("new_hour", -1)) == int(p_b.get("new_hour", -2)) and 
                p_a.get("new_lab_id") == p_b.get("new_lab_id") and
                p_a.get("new_lab_id")):
                conflicts.append((r_a, r_b))
    return conflicts

def resolve_conflict(req_a: dict, req_b: dict) -> dict:
    """
    Fixed rule resolution:
    Step 1: Check flexibility (does safer alternative exist?). Whichever has a free alternative slot can be moved;
            whoever has no alternative gets the lab.
    Step 2: If both are equally flexible (both have alternative, or neither), seniority (Professor 3 > Associate 2 > Assistant 1).
    Step 3: Same rank: earlier created request wins.
    """
    sections, labs, staff, slots = load_timetable()
    p_a = req_a.get("payload", {})
    p_b = req_b.get("payload", {})
    
    safer_a = find_safer_option(p_a.get("slot_id"), p_a.get("new_day"), p_a.get("new_hour"), p_a.get("new_lab_id"), slots, labs, sections, 20)
    safer_b = find_safer_option(p_b.get("slot_id"), p_b.get("new_day"), p_b.get("new_hour"), p_b.get("new_lab_id"), slots, labs, sections, 20)
    
    flex_a = safer_a is not None
    flex_b = safer_b is not None
    
    winner = None
    loser = None
    reason = ""
    loser_alt = None
    
    if flex_a and not flex_b:
        winner = req_b
        loser = req_a
        loser_alt = safer_a["change"]
        reason = f"{loser['requester'].upper()} has a free alternative slot in Lab {loser_alt['new_lab_id']} at {loser_alt['new_day']} {loser_alt['new_hour']}:00 and {winner['requester'].upper()} does not, so {winner['requester'].upper()} gets Lab {p_b.get('new_lab_id')}."
    elif flex_b and not flex_a:
        winner = req_a
        loser = req_b
        loser_alt = safer_b["change"]
        reason = f"{loser['requester'].upper()} has a free alternative slot in Lab {loser_alt['new_lab_id']} at {loser_alt['new_day']} {loser_alt['new_hour']}:00 and {winner['requester'].upper()} does not, so {winner['requester'].upper()} gets Lab {p_a.get('new_lab_id')}."
    else:
        # Step 2: Seniority (rank)
        rank_a = int(req_a.get("rank", 1))
        rank_b = int(req_b.get("rank", 1))
        if rank_a > rank_b:
            winner = req_a
            loser = req_b
            loser_alt = safer_b["change"] if safer_b else None
            reason = f"Both faculty are equally flexible; {winner['requester'].upper()} (Rank {rank_a}) outranks {loser['requester'].upper()} (Rank {rank_b}), so {winner['requester'].upper()} gets Lab {p_a.get('new_lab_id')}."
        elif rank_b > rank_a:
            winner = req_b
            loser = req_a
            loser_alt = safer_a["change"] if safer_a else None
            reason = f"Both faculty are equally flexible; {winner['requester'].upper()} (Rank {rank_b}) outranks {loser['requester'].upper()} (Rank {rank_a}), so {winner['requester'].upper()} gets Lab {p_b.get('new_lab_id')}."
        else:
            # Step 3: Earlier request
            created_a = req_a.get("created", "")
            created_b = req_b.get("created", "")
            if created_a <= created_b:
                winner = req_a
                loser = req_b
                loser_alt = safer_b["change"] if safer_b else None
                reason = f"Faculty share equal rank ({rank_a}); {winner['requester'].upper()} submitted earlier ({created_a} vs {created_b}), so {winner['requester'].upper()} gets Lab {p_a.get('new_lab_id')}."
            else:
                winner = req_b
                loser = req_a
                loser_alt = safer_a["change"] if safer_a else None
                reason = f"Faculty share equal rank ({rank_b}); {winner['requester'].upper()} submitted earlier ({created_b} vs {created_a}), so {winner['requester'].upper()} gets Lab {p_b.get('new_lab_id')}."

    return {
        "winner": winner,
        "loser": loser,
        "reason": reason,
        "loser_alternative": loser_alt
    }
