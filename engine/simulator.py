"""
Exam simulator for ECHO Decision Safety Agent (13 / 66 / 13 demo benchmark).
"""

def simulate_exam(decision_text: str = "Move all Block B exams to Block C"):
    """
    Classic ECHO Exam Simulation benchmark:
    Option 1: Current Exam Schedule (Risk 13)
    Option 2: As Requested (Risk 66)
    Option 3: Safer Alternative (Risk 13)
    """
    opt1 = {
        "name": "Option 1: Current Exam Timetable",
        "description": "Baseline multi-block allocation across Blocks A, B, and C",
        "moved": 0,
        "risk": {
            "score": 13,
            "counts": {"room_overflow": 1, "invigilator_clash": 0, "session_overlap": 1},
            "breakdown": {"room_overflow": 8, "invigilator_clash": 0, "session_overlap": 5}
        },
        "findings": [
            {
                "severity": "medium",
                "rule": "Capacity Headroom Warning",
                "message": "Block A Hall 2 operating at 96% planned seating limit.",
                "points": 8,
                "source": "computed"
            },
            {
                "severity": "low",
                "rule": "Session Separation Margin",
                "message": "Afternoon session starts 35 minutes following morning sweep.",
                "points": 5,
                "source": "computed"
            }
        ]
    }
    
    opt2 = {
        "name": "Option 2: Requested Shift (Block B -> Block C)",
        "description": "Consolidate 12 exam sessions from Block B entirely into Block C",
        "moved": 12,
        "risk": {
            "score": 66,
            "counts": {"room_overflow": 4, "invigilator_clash": 3, "session_overlap": 2},
            "breakdown": {"room_overflow": 32, "invigilator_clash": 24, "session_overlap": 10}
        },
        "findings": [
            {
                "severity": "critical",
                "rule": "Severe Room Overflow",
                "message": "Block C capacity (450 seats) exceeded by 180 registered candidates.",
                "points": 18,
                "source": "computed"
            },
            {
                "severity": "critical",
                "rule": "Invigilator Double-Booking",
                "message": "6 invigilators assigned to two rooms concurrently during slot 09:00-12:00.",
                "points": 24,
                "source": "computed"
            },
            {
                "severity": "high",
                "rule": "Corridor Transit Bottleneck",
                "message": "Simultaneous dismissal exceeds fire exit evacuation flow rate by 42%.",
                "points": 14,
                "source": "computed"
            },
            {
                "severity": "medium",
                "rule": "Special Accommodations Lost",
                "message": "Wheelchair-accessible desks unavailable in assigned C-wing basement annex.",
                "points": 10,
                "source": "computed"
            }
        ]
    }
    
    opt3 = {
        "name": "Option 3: Safer Alternative (Balanced Reallocation)",
        "description": "Shift heavy exam papers to North Auditorium and staggered Block C slots",
        "moved": 8,
        "risk": {
            "score": 13,
            "counts": {"room_overflow": 0, "invigilator_clash": 0, "session_overlap": 1},
            "breakdown": {"room_overflow": 0, "invigilator_clash": 0, "session_overlap": 13}
        },
        "findings": [
            {
                "severity": "low",
                "rule": "Staggered Corridor Transit",
                "message": "15-minute offset introduced between Auditorium and Block C starts.",
                "points": 13,
                "source": "computed"
            },
            {
                "severity": "low",
                "rule": "Accessibility Maintained",
                "message": "Ground floor access reserved for all candidates with mobility needs.",
                "points": 0,
                "source": "computed"
            }
        ]
    }
    
    verdict = "recommend safer option"
    verdict_reason = "Consolidating all Block B exams into Block C triggers critical capacity deficits and staff double-bookings (Score: 66/100). The safer alternative resolves all critical constraints while fulfilling operational needs (Score: 13/100)."
    
    return {
        "options": [opt1, opt2, opt3],
        "recommended": 3,
        "verdict": verdict,
        "verdict_reason": verdict_reason
    }
