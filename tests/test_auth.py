"""
Tests for authentication, role-based access control, and red team checks.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import login, can
from redteam.runner import run_all
from redteam.access import run_access_checks

def test_login_success():
    user = login("admin", "admin123")
    assert user is not None
    assert user["role"] == "admin"

def test_login_failure():
    user = login("admin", "wrongpassword99")
    assert user is None

def test_role_permissions():
    assert can("admin", "approve") is True
    assert can("staff", "approve") is False
    assert can("student", "approve") is False
    
    assert can("staff", "create_request") is True
    assert can("student", "create_request") is False
    
    assert can("student", "send_feedback") is True
    assert can("staff", "send_feedback") is False

def test_all_16_redteam_scenarios_pass():
    runner_results = run_all()
    access_results = run_access_checks()
    all_results = runner_results + access_results
    assert len(all_results) == 16
    for r in all_results:
        assert r["result"] == "PASS", f"Scenario failed: {r['scenario']}"
