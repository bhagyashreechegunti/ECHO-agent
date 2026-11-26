"""
Risk scoring and explainable findings for timetables.
Weights: section_clash 3, staff_clash 4, lab_double_booking 8, lab_too_small 5. Score capped at 100.
"""

TT_WEIGHTS = {
    "section_clash": 3,
    "staff_clash": 4,
    "lab_double_booking": 8,
    "lab_too_small": 5
}

def timetable_risk(results: dict) -> dict:
    """Calculates risk score (0-100), counts, and breakdown."""
    counts = {
        "section_clash": len(results.get("section_clash", [])),
        "staff_clash": len(results.get("staff_clash", [])),
        "lab_double_booking": len(results.get("lab_double_booking", [])),
        "lab_too_small": len(results.get("lab_too_small", []))
    }
    
    breakdown = {
        k: counts[k] * TT_WEIGHTS[k] for k in TT_WEIGHTS
    }
    
    raw_score = sum(breakdown.values())
    score = min(100, raw_score)
    
    return {
        "score": score,
        "counts": counts,
        "breakdown": breakdown
    }

def timetable_findings(results: dict) -> list:
    """Generates structured findings with severities tagged 'source: computed'."""
    findings = []
    
    # Lab double booking is critical (weight 8)
    for c in results.get("lab_double_booking", []):
        findings.append({
            "severity": "critical",
            "rule": "Lab Double-Booking",
            "message": c["details"],
            "points": TT_WEIGHTS["lab_double_booking"],
            "source": "computed"
        })
        
    # Staff clash is high (weight 4)
    for c in results.get("staff_clash", []):
        findings.append({
            "severity": "high",
            "rule": "Staff Double-Assignment",
            "message": c["details"],
            "points": TT_WEIGHTS["staff_clash"],
            "source": "computed"
        })
        
    # Lab too small is medium/high (weight 5)
    for c in results.get("lab_too_small", []):
        findings.append({
            "severity": "medium",
            "rule": "Lab Capacity Deficit",
            "message": c["details"],
            "points": TT_WEIGHTS["lab_too_small"],
            "source": "computed"
        })
        
    # Section clash is medium (weight 3)
    for c in results.get("section_clash", []):
        findings.append({
            "severity": "medium",
            "rule": "Section Schedule Conflict",
            "message": c["details"],
            "points": TT_WEIGHTS["section_clash"],
            "source": "computed"
        })
        
    if not findings:
        findings.append({
            "severity": "low",
            "rule": "Baseline Health",
            "message": "No timetable schedule conflicts detected.",
            "points": 0,
            "source": "computed"
        })
        
    return findings
