"""
Unit and integration tests for ECHO Timetable Engine.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.timetable import load_timetable
from engine.timetable_checks import run_timetable_checks
from engine.timetable_scorer import timetable_risk
from engine.change_requests import simulate_request, find_conflicts, resolve_conflict, add_request, list_requests

def test_1_baseline_has_planted_counts():
    sections, labs, staff, slots = load_timetable()
    res = run_timetable_checks(slots, labs, sections)
    risk = timetable_risk(res)
    assert len(res["section_clash"]) == 0
    assert len(res["staff_clash"]) == 0
    assert len(res["lab_double_booking"]) == 0
    assert len(res["lab_too_small"]) == 2  # Planted slots S04 in L8 and S07 in L9
    assert risk["score"] == 10  # 2 * 5 = 10

def test_2_r1_gives_recommend_approve():
    reqs = list_requests()
    r1 = next(r for r in reqs if r["id"] == "R001")
    sim = simulate_request(r1)
    assert sim["verdict"] == "recommend approve"
    assert sim["recommended"] == 2

def test_3_r2_does_not_get_recommend_approve():
    reqs = list_requests()
    r2 = next(r for r in reqs if r["id"] == "R002")
    sim = simulate_request(r2)
    assert sim["verdict"] in ["recommend safer option", "recommend reject"]
    assert sim["recommended"] in [1, 3]

def test_4_r3_vs_r4_gives_documented_winner():
    reqs = list_requests()
    r3 = next(r for r in reqs if r["id"] == "R003")
    r4 = next(r for r in reqs if r["id"] == "R004")
    res = resolve_conflict(r3, r4)
    # T1 is Professor (rank 3), T4 is Assistant (rank 1) -> T1 wins
    assert res["winner"]["requester"] == "t1"
    assert res["loser"]["requester"] == "t4"
    assert "T1" in res["reason"] or "t1" in res["reason"]

def test_5_staff_request_for_foreign_slot_refused():
    try:
        # T4 attempting to request change for T1's slot SL004
        add_request("class", "t4", "staff", 1, {
            "slot_id": "SL001",
            "new_day": "Fri",
            "new_hour": 14,
            "new_lab_id": "L1"
        })
        assert False, "Should have raised PermissionError"
    except PermissionError:
        assert True
