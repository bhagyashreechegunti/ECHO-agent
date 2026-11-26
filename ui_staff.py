"""
Staff Dashboard for ECHO Decision Safety Agent.
Features: My assigned teaching timetable, Lab capacity browser,
Change request submission (restricted to own slots), and request tracking.
"""
import streamlit as st
import pandas as pd
from engine.timetable import load_timetable
from engine.change_requests import add_request, list_requests
from auth import can, deny
from ui_common import render_top_header, timetable_grid

def render(user: dict):
    staff_id = user.get("staff_id", "T1")
    render_top_header(f"ECHO Faculty Portal — {staff_id}", role="Staff", user=user["username"])
    
    sections, labs, staff, slots = load_timetable()
    
    # Get staff details
    staff_info = staff[staff["staff_id"] == staff_id]
    staff_name = staff_info.iloc[0]["name"] if not staff_info.empty else staff_id
    staff_rank = staff_info.iloc[0]["rank"] if not staff_info.empty else "Assistant"
    
    st.markdown(f"""
    <div style="background: #FFFFFF; border-radius: 14px; padding: 16px 20px; border: 1px solid #E2E8F0; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
        <div>
            <span style="font-size: 20px; font-weight: 700; color: #1E293B;">{staff_name}</span>
            <span class="pill-badge pill-purple" style="margin-left: 10px;">Rank: {staff_rank} (Level {user.get('rank', 1)})</span>
        </div>
        <div style="font-size: 17px; color: #64748B;">
            Assigned Staff ID: <b>{staff_id}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    tabs = st.tabs([
        "📅 My Teaching Schedule",
        "🔬 Lab Availability Explorer",
        "✍️ Submit Timetable Request",
        "📋 My Submitted Requests"
    ])
    
    # ==========================================
    # TAB 1: MY SCHEDULE
    # ==========================================
    with tabs[0]:
        st.markdown('<div class="echo-card-header">Weekly Teaching Commitment</div>', unsafe_allow_html=True)
        my_slots = slots[slots["staff_id"] == staff_id]
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total Teaching Hours", f"{len(my_slots)} hrs/week")
        with c2:
            lab_hours = len(my_slots[my_slots["kind"] == "lab"])
            st.metric("Lab Practicals", f"{lab_hours} hrs/week")
        with c3:
            sections_taught = my_slots["section_id"].nunique()
            st.metric("Sections Taught", f"{sections_taught} Cohorts")
            
        grid = timetable_grid(slots, "staff_id", staff_id)
        st.dataframe(grid, use_container_width=True)
        st.caption("ℹ️ Cells display your scheduled classes, sections, and assigned rooms.")

    # ==========================================
    # TAB 2: LAB BROWSER
    # ==========================================
    with tabs[1]:
        st.markdown('<div class="echo-card-header">Campus Computer Laboratories Explorer</div>', unsafe_allow_html=True)
        st.caption("Inspect workstation capacities and existing bookings to plan room requests.")
        
        selected_lab = st.selectbox(
            "Select Laboratory to Inspect:",
            labs["lab_id"].tolist(),
            format_func=lambda x: f"{x} - {labs[labs['lab_id'] == x].iloc[0]['name']} (Capacity: {labs[labs['lab_id'] == x].iloc[0]['capacity']})",
            filter_mode=None
        )
        
        lab_grid = timetable_grid(slots, "lab_id", selected_lab)
        st.dataframe(lab_grid, use_container_width=True)

    # ==========================================
    # TAB 3: SUBMIT REQUEST
    # ==========================================
    with tabs[2]:
        st.markdown('<div class="echo-card-header">Request Timetable or Lab Relocation</div>', unsafe_allow_html=True)
        st.caption("Enforces ownership: you can only submit relocation requests for classes assigned to your staff ID.")
        
        if my_slots.empty:
            st.warning("No active teaching slots found for your staff profile.")
        else:
            slot_choices = my_slots["slot_id"].tolist()
            
            def slot_label(sid):
                row = my_slots[my_slots["slot_id"] == sid].iloc[0]
                room = f"Lab {row['lab_id']}" if row['lab_id'] else "Theory Hall"
                return f"{sid}: {row['subject']} ({row['section_id']}) • {row['day']} {row['hour']:02d}:00 [{room}]"
            
            with st.form("request_form"):
                chosen_slot = st.selectbox("Select Your Class to Move:", slot_choices, format_func=slot_label, filter_mode=None)
                
                c_day, c_hour, c_lab = st.columns(3)
                with c_day:
                    new_day = st.selectbox("Preferred Day:", ["Mon", "Tue", "Wed", "Thu", "Fri"], filter_mode=None)
                with c_hour:
                    new_hour = st.selectbox("Preferred Hour:", list(range(8, 17)), format_func=lambda h: f"{h:02d}:00", filter_mode=None)
                with c_lab:
                    new_lab = st.selectbox("Requested Laboratory:", labs["lab_id"].tolist(), format_func=lambda l: f"{l} (Cap: {labs[labs['lab_id'] == l].iloc[0]['capacity']})", filter_mode=None)
                    
                reason_note = st.text_input("Operational Reason / Equipment Justification:", placeholder="e.g. Relocating to Knuth Lab for specialized parallel computing nodes.")
                
                submitted = st.form_submit_button("🚀 Submit Request to Admin", type="primary")
                
                if submitted:
                    if not can(user["role"], "create_request"):
                        deny(user["role"], "create_request", user["username"])
                        st.error("Permission denied: You do not have permission to create timetable requests.")
                    else:
                        try:
                            payload = {
                                "slot_id": chosen_slot,
                                "new_day": new_day,
                                "new_hour": int(new_hour),
                                "new_lab_id": new_lab
                            }
                            new_req = add_request(
                                kind="class",
                                requester=staff_id.lower(),
                                role=user["role"],
                                rank=user.get("rank", 1),
                                payload=payload,
                                note=reason_note or f"Relocation of {chosen_slot} to {new_lab}"
                            )
                            st.success(f"Request {new_req['id']} submitted successfully! It is now queued for administrative safety evaluation.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Request submission failed: {str(e)}")

    # ==========================================
    # TAB 4: MY SUBMITTED REQUESTS
    # ==========================================
    with tabs[3]:
        st.markdown('<div class="echo-card-header">Status of Your Submitted Requests</div>', unsafe_allow_html=True)
        
        all_reqs = list_requests()
        my_reqs = [r for r in all_reqs if r.get("requester", "").lower() in [staff_id.lower(), user["username"].lower()]]
        
        if not my_reqs:
            st.info("You haven't submitted any requests yet.")
        else:
            table_data = []
            for r in reversed(my_reqs):
                payload = r.get("payload", {})
                table_data.append({
                    "Request ID": r.get("id"),
                    "Type": r.get("kind", "").upper(),
                    "Slot ID": payload.get("slot_id", "N/A"),
                    "Target Move": f"{payload.get('new_day', '')} {payload.get('new_hour', '')}:00 in Lab {payload.get('new_lab_id', '')}",
                    "Note": r.get("note", ""),
                    "Submitted At": r.get("created", ""),
                    "Status": r.get("status", "").upper()
                })
            st.dataframe(pd.DataFrame(table_data), use_container_width=True)
