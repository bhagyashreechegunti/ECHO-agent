"""
Student Dashboard for ECHO Decision Safety Agent.
Features: Live section timetable (instantly reflects admin approvals),
Student voice / feedback box with prompt injection protection and AI proposal extraction.
"""
import streamlit as st
import pandas as pd
from engine.timetable import load_timetable
from engine.change_requests import add_request, list_requests
from security import check_input
from auth import can, deny, check_feedback_limit
from audit import log
from ai import propose_from_feedback
from ui_common import render_top_header, timetable_grid

def render(user: dict):
    sec_id = user.get("section_id", "S01")
    render_top_header(f"ECHO Student Portal — Section {sec_id}", role="Student", user=user["username"])
    
    sections, labs, staff, slots = load_timetable()
    
    sec_match = sections[sections["section_id"] == sec_id]
    sec_name = sec_match.iloc[0]["name"] if not sec_match.empty else f"Section {sec_id}"
    sec_size = sec_match.iloc[0]["size"] if not sec_match.empty else 50
    
    st.markdown(f"""
    <div style="background: #FFFFFF; border-radius: 14px; padding: 16px 20px; border: 1px solid #E2E8F0; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
        <div>
            <span style="font-size: 20px; font-weight: 700; color: #1E293B;">Cohort: {sec_name} ({sec_id})</span>
            <span class="pill-badge pill-green" style="margin-left: 10px;">Enrolled: {sec_size} Students</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    tabs = st.tabs([
        "📅 Weekly Timetable",
        "💬 Share Feedback",
        "📜 Feedback Status Tracker"
    ])
    
    # ==========================================
    # TAB 1: WEEKLY TIMETABLE
    # ==========================================
    with tabs[0]:
        st.markdown('<div class="echo-card-header">Weekly Class & Lab Schedule</div>', unsafe_allow_html=True)
        
        sec_slots = slots[slots["section_id"] == sec_id]
        
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Total Classes / Week", len(sec_slots))
        with m2:
            lab_classes = len(sec_slots[sec_slots["kind"] == "lab"])
            st.metric("Lab Sessions", lab_classes)
        with m3:
            st.metric("Faculty Assigned", sec_slots["staff_id"].nunique())
            
        grid = timetable_grid(slots, "section_id", sec_id)
        st.dataframe(grid, use_container_width=True)

    # ==========================================
    # TAB 2: STUDENT FEEDBACK BOX
    # ==========================================
    with tabs[1]:
        st.markdown('<div class="echo-card-header">Student Feedback & Room Bottleneck Reporting</div>', unsafe_allow_html=True)
        st.caption("Help optimize your campus experience. If a lab is overcrowded or machines lack capacity, report it here. ECHO's AI will parse your issue and submit a structured proposal to the Administration.")
        
        # Hourly rate limit indicator
        can_submit = check_feedback_limit(user["username"])
        if not can_submit:
            st.warning("⚠️ Hourly Submission Limit Reached: You have submitted 5 feedback reports in the last hour. Please try again later.")
            
        fb_text = st.text_area(
            "Describe the issue or lab concern:",
            placeholder="e.g. Lab 3 is too crowded for Section 3 during Tuesday morning AI Lab.",
            height=110,
            disabled=not can_submit
        )
        
        st.markdown("""
        <div style="font-size: 16px; color: #64748B; margin-bottom: 12px;">
            💬 <i>Your feedback is directly analyzed by ECHO's Decision Safety Agent to recommend room adjustments to the administration.</i>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📤 Submit Feedback to Administration", type="primary", disabled=not can_submit):
            if not can(user["role"], "send_feedback"):
                deny(user["role"], "send_feedback", user["username"])
                st.error("Permission Denied: Your account role is not allowed to submit student feedback.")
            else:
                # 1. Security Check
                sec_check = check_input(fb_text)
                if not sec_check["safe"]:
                    log("feedback_injection_attempt", user["username"], {"text": fb_text, "reason": sec_check["reason"]})
                    st.error(f"❌ Security Policy Refusal: {sec_check['reason']}")
                else:
                    # 2. AI proposal extraction with real-data validation
                    sec_slots_list = sec_slots[["slot_id", "day", "hour", "lab_id", "subject"]].to_dict(orient="records")
                    labs_list = labs[["lab_id", "name", "capacity"]].to_dict(orient="records")
                    context = {"section_slots": sec_slots_list, "labs": labs_list}
                    
                    ai_res = propose_from_feedback(fb_text, sec_id, context)
                    proposal = ai_res.get("change")
                    
                    # 3. Add to requests queue
                    payload = {
                        "text": fb_text,
                        "proposal": proposal,
                        "ai_reasoning": ai_res.get("reasoning", "")
                    }
                    
                    new_req = add_request(
                        kind="feedback",
                        requester=user["username"],
                        role=user["role"],
                        rank=0,
                        payload=payload,
                        note=f"Student feedback ({sec_id}): {fb_text[:60]}..."
                    )
                    
                    log("feedback_submitted", user["username"], {"request_id": new_req["id"], "has_proposal": bool(proposal)})
                    
                    if proposal:
                        st.success(f"✅ Feedback received! ECHO's AI successfully translated your issue into concrete relocation proposal ({proposal['slot_id']} → Lab {proposal['new_lab_id']}). Queued as Request {new_req['id']}.")
                    else:
                        st.info(f"Feedback logged as Request {new_req['id']}. The feedback was flagged as 'needs clarification' for admin review.")
                    st.rerun()

    # ==========================================
    # TAB 3: FEEDBACK STATUS TRACKER
    # ==========================================
    with tabs[2]:
        st.markdown('<div class="echo-card-header">Your Feedback Status Tracking</div>', unsafe_allow_html=True)
        
        all_reqs = list_requests()
        my_fb = [r for r in all_reqs if r.get("requester") == user["username"] and r.get("kind") == "feedback"]
        
        if not my_fb:
            st.info("You haven't submitted any feedback yet.")
        else:
            fb_rows = []
            for r in reversed(my_fb):
                p = r.get("payload", {})
                fb_rows.append({
                    "ID": r.get("id"),
                    "Feedback Summary": p.get("text", r.get("note")),
                    "AI Synthesized Proposal": f"Move {p['proposal']['slot_id']} to Lab {p['proposal']['new_lab_id']}" if p.get("proposal") else "Needs Clarification",
                    "Status": r.get("status", "").upper(),
                    "Submitted At": r.get("created")
                })
            st.dataframe(pd.DataFrame(fb_rows), use_container_width=True)
