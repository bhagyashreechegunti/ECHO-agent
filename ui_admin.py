"""
Admin Dashboard for ECHO Decision Safety Agent.
Features: Timetable explorer, Requests & Conflict resolver, 3-way decision simulation,
and real-time Audit log.
"""
import streamlit as st
import pandas as pd
from engine.timetable import load_timetable, commit_change, reset_demo
from engine.change_requests import (
    list_requests, simulate_request, set_status,
    find_conflicts, resolve_conflict
)
from auth import can, deny
from audit import log, read_log
from ai import explain
from ui_common import (
    render_top_header, timetable_grid,
    render_risk_gauge, render_options_comparison_chart
)

def render(user: dict):
    render_top_header("ECHO Administrator Control Center", role="Admin", user=user["username"])
    
    tab_names = [
        "📅 Timetables",
        "📥 Requests & Conflicts",
        "⚖️ Decision Simulation",
        "📜 Audit Log"
    ]
    
    # Allow programmatic tab switching (e.g., clicking 'Run Simulation' switches directly to Decision Simulation)
    target_tab = st.session_state.pop("switch_to_admin_tab", None)
    if target_tab and target_tab in tab_names:
        st.session_state["admin_active_tab"] = target_tab
    elif "admin_active_tab" not in st.session_state:
        st.session_state["admin_active_tab"] = tab_names[0]
        
    tabs = st.tabs(tab_names, key="admin_active_tab", on_change="rerun")
    
    sections, labs, staff, slots = load_timetable()
    
    # ==========================================
    # TAB 1: TIMETABLES EXPLORER
    # ==========================================
    with tabs[0]:
        st.markdown('<div class="echo-card-header">Weekly Master Timetables</div>', unsafe_allow_html=True)
        
        view_type = st.radio("Select View Type:", ["Sections (S01 - S10)", "Labs (L1 - L9)"], horizontal=True)
        
        if "Sections" in view_type:
            sec_options = sections["section_id"].tolist()
            sec_names = dict(zip(sections["section_id"], sections["name"]))
            sec_sizes = dict(zip(sections["section_id"], sections["size"]))
            
            selected_sec = st.selectbox(
                "Choose Section:",
                sec_options,
                format_func=lambda x: f"{x} - {sec_names[x]} ({sec_sizes[x]} Students)",
                key="admin_sec_sel",
                filter_mode=None
            )
            
            col1, col2, col3 = st.columns(3)
            sec_slots = slots[slots["section_id"] == selected_sec]
            with col1:
                st.metric("Section Strength", f"{sec_sizes[selected_sec]} Students")
            with col2:
                st.metric("Weekly Periods", len(sec_slots))
            with col3:
                lab_cnt = len(sec_slots[sec_slots["kind"] == "lab"])
                st.metric("Lab Sessions", f"{lab_cnt} Sessions")
                
            grid_df = timetable_grid(slots, "section_id", selected_sec)
            st.dataframe(grid_df, use_container_width=True)
            
        else:
            lab_options = labs["lab_id"].tolist()
            lab_names = dict(zip(labs["lab_id"], labs["name"]))
            lab_caps = dict(zip(labs["lab_id"], labs["capacity"]))
            
            selected_lab = st.selectbox(
                "Choose Lab:",
                lab_options,
                format_func=lambda x: f"{x} - {lab_names[x]} (Capacity: {lab_caps[x]})",
                key="admin_lab_sel",
                filter_mode=None
            )
            
            lab_slots = slots[(slots["kind"] == "lab") & (slots["lab_id"] == selected_lab)]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Lab Capacity", f"{lab_caps[selected_lab]} Workstations")
            with col2:
                st.metric("Weekly Bookings", len(lab_slots))
            with col3:
                utilization = round((len(lab_slots) / 45) * 100, 1)
                st.metric("Utilization Rate", f"{utilization}%")
                
            grid_df = timetable_grid(slots, "lab_id", selected_lab)
            st.dataframe(grid_df, use_container_width=True)

    # ==========================================
    # TAB 2: REQUESTS & CONFLICTS
    # ==========================================
    with tabs[1]:
        st.markdown('<div class="echo-card-header">Change Requests & Automated Conflict Resolution</div>', unsafe_allow_html=True)
        
        # 1. Conflict Check (Step B11)
        conflicts = find_conflicts()
        if conflicts:
            for req_a, req_b in conflicts:
                sol = resolve_conflict(req_a, req_b)
                p_a = req_a.get("payload", {})
                target_lab = p_a.get("new_lab_id")
                target_day = p_a.get("new_day")
                target_hour = p_a.get("new_hour")
                
                conflict_html = f"""<div class="conflict-card">
<div style="font-size: 20px; font-weight: 700; color: #B9770E; margin-bottom: 8px;">
⚠️ TWO-STAFF RESOURCE CONFLICT DETECTED
</div>
<div style="font-size: 18px; color: #784212; margin-bottom: 12px;">
Two pending faculty requests are competing for <b>Lab {target_lab}</b> on <b>{target_day} at {target_hour}:00</b>:
<ul style="margin-top: 6px; margin-bottom: 6px;">
<li><b>{req_a['id']}</b>: {req_a['requester'].upper()} (Rank: {req_a.get('rank', 1)}) — {req_a.get('note', '')}</li>
<li><b>{req_b['id']}</b>: {req_b['requester'].upper()} (Rank: {req_b.get('rank', 1)}) — {req_b.get('note', '')}</li>
</ul>
</div>
<div style="background: rgba(255,255,255,0.7); border-radius: 10px; padding: 12px; margin-bottom: 14px; border: 1px solid #F5CBA7;">
<b>Rule Engine Rationale:</b> {sol['reason']}
<br>
<b>Proposed Adjustment for Loser ({sol['loser']['requester'].upper()}):</b> Relocate to Lab <b>{sol['loser_alternative']['new_lab_id']}</b> on {sol['loser_alternative']['new_day']} {sol['loser_alternative']['new_hour']}:00.
</div>
</div>"""
                st.markdown(conflict_html, unsafe_allow_html=True)
                
                c_col1, c_col2, _ = st.columns([1.5, 1.5, 3])
                with c_col1:
                    if st.button(f"⚡ Accept Rule Result ({sol['winner']['requester'].upper()} wins)", key=f"accept_conf_{req_a['id']}_{req_b['id']}", type="primary"):
                        if not can(user["role"], "approve"):
                            deny(user["role"], "approve", user["username"])
                            st.error("Permission denied: You do not have approve privileges.")
                        else:
                            # Approve winner
                            commit_change(sol["winner"]["payload"])
                            set_status(sol["winner"]["id"], "approved", by=user["username"])
                            # Commit loser's alternative
                            commit_change(sol["loser_alternative"])
                            set_status(sol["loser"]["id"], "approved", by=user["username"])
                            log("conflict_resolved", user["username"], {
                                "winner": sol["winner"]["id"],
                                "loser": sol["loser"]["id"],
                                "reason": sol["reason"]
                            })
                            st.success("Conflict successfully resolved! Timetable updated for both faculty.")
                            st.rerun()
                with c_col2:
                    if st.button("✋ Decide Myself (Keep Pending)", key=f"manual_conf_{req_a['id']}_{req_b['id']}"):
                        st.info("Both requests left in pending status for manual case-by-case review.")

        # 2. Requests Table
        reqs = list_requests()
        if not reqs:
            st.info("No change requests in queue.")
        else:
            st.markdown("#### Pending & Processed Requests Queue")
            
            for r in reqs:
                status_color = {
                    "pending": "#FFF3E0; color: #E65100; border: 1px solid #FFE0B2;",
                    "approved": "#E8F5E9; color: #2E7D32; border: 1px solid #C8E6C9;",
                    "rejected": "#FFEBEE; color: #C62828; border: 1px solid #FFCDD2;"
                }.get(r["status"], "#F1F5F9; color: #475569;")
                
                with st.expander(f"📌 {r['id']} | [{r['kind'].upper()}] from {r['requester'].upper()} ({r.get('role', 'staff')}) — Status: {r['status'].upper()}", expanded=(r["status"] == "pending")):
                    r_col1, r_col2 = st.columns([3, 1])
                    with r_col1:
                        st.write(f"**Submitted At:** {r.get('created', 'N/A')}")
                        st.write(f"**Description / Note:** {r.get('note', 'None')}")
                        st.write(f"**Payload Details:** `{r.get('payload', {})}`")
                        
                        is_feedback = (r.get("kind") == "feedback")
                        has_proposal = bool(r.get("payload", {}).get("proposal")) if is_feedback else True
                        
                        if is_feedback and not has_proposal:
                            st.warning("⚠️ Student feedback requires clarification. AI could not reliably synthesize a concrete slot change.")
                    
                    with r_col2:
                        st.markdown(f"""<div style="background: {status_color}; padding: 6px 12px; border-radius: 8px; font-weight: 700; text-align: center; margin-bottom: 10px;">
{r['status'].upper()}
</div>""", unsafe_allow_html=True)
                        
                        can_sim = has_proposal and (r["status"] == "pending")
                        if st.button("🔍 Run Simulation", key=f"sim_btn_{r['id']}", disabled=not can_sim, type="primary"):
                            st.session_state["active_sim_req"] = r
                            st.session_state["decision_sim_selected_id"] = r["id"]
                            st.session_state["switch_to_admin_tab"] = "⚖️ Decision Simulation"
                            st.rerun()

    # ==========================================
    # TAB 3: DECISION SIMULATION
    # ==========================================
    with tabs[2]:
        st.markdown('<div class="echo-card-header">Three-Way Simulation & Decision Safety Review</div>', unsafe_allow_html=True)
        
        all_reqs = list_requests()
        valid_reqs = [r for r in all_reqs if r.get("kind") != "feedback" or r.get("payload", {}).get("proposal")]
        
        if not valid_reqs:
            st.info("No requests available to simulate. Please submit a request from the Staff dashboard or restore demo state.")
        else:
            req_map_by_id = {r["id"]: r for r in valid_reqs}
            active_sim = st.session_state.get("active_sim_req")
            default_id = active_sim["id"] if (active_sim and active_sim["id"] in req_map_by_id) else valid_reqs[0]["id"]
            
            c_sel1, c_sel2 = st.columns([3, 1])
            with c_sel1:
                selected_rid = st.selectbox(
                    "Choose Request to Simulate & Review:",
                    options=list(req_map_by_id.keys()),
                    index=list(req_map_by_id.keys()).index(default_id) if default_id in req_map_by_id else 0,
                    format_func=lambda rid: f"{rid} — [{req_map_by_id[rid].get('requester', '').upper()}] {req_map_by_id[rid].get('note', '')[:75]}",
                    key="decision_sim_selected_id",
                    filter_mode=None
                )
                sim_req = req_map_by_id[selected_rid]
                st.session_state["active_sim_req"] = sim_req
            with c_sel2:
                req_status = sim_req.get("status", "pending").upper()
                s_color = "#2E7D32" if req_status == "APPROVED" else ("#C62828" if req_status == "REJECTED" else "#E65100")
                st.markdown(f"""<div style="margin-top: 28px; background: rgba(0,0,0,0.04); padding: 8px 12px; border-radius: 8px; text-align: center; font-weight: 700; color: {s_color};">
Status: {req_status}
</div>""", unsafe_allow_html=True)
            
            # Check permissions
            if not can(user["role"], "run_simulation"):
                deny(user["role"], "run_simulation", user["username"])
                st.error("Access Denied: Your account role does not have permission to execute simulation engine.")
                return

            sim_res = simulate_request(sim_req)
            options = sim_res["options"]
            recommended_idx = sim_res["recommended"]
            verdict = sim_res["verdict"]
            verdict_reason = sim_res["verdict_reason"]
            
            # 1. Visual 3-Way Options Comparison Cards (Native Streamlit Containers)
            render_options_comparison_chart(options, recommended_idx)
            
            # 2. Prominent Verdict Banner
            banner_class = "verdict-banner-approve" if verdict == "recommend approve" else ("verdict-banner-safer" if verdict == "recommend safer option" else "verdict-banner-reject")
            verdict_icon = "✅" if verdict == "recommend approve" else ("🛡️" if verdict == "recommend safer option" else "❌")
            
            verdict_html = f"""<div class="{banner_class}">
<div style="font-size: 22px; font-weight: 800; display: flex; align-items: center; gap: 8px;">
{verdict_icon} Agent Recommendation: {verdict.upper()}
</div>
<div style="font-size: 18px; margin-top: 6px; line-height: 1.5;">
{verdict_reason}
</div>
</div>"""
            st.markdown(verdict_html, unsafe_allow_html=True)
            
            # 3. Two-Column Detailed Findings (Computed vs Predicted)
            chosen_opt = options[recommended_idx - 1]
            opt2 = options[1]
            
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                st.markdown("#### 🔢 Computed Rule Findings")
                render_risk_gauge(opt2["risk"]["score"], f"Option 2 Requested Risk: {opt2['risk']['score']}/100")
                
                for f in opt2["findings"]:
                    sev_color = {"critical": "#FFCDD2", "high": "#FFE0B2", "medium": "#FFF9C4", "low": "#E8F5E9"}.get(f["severity"], "#F1F5F9")
                    finding_html = f"""<div style="background: #FFFFFF; border-left: 4px solid #5C6BC0; padding: 12px 14px; border-radius: 8px; margin-bottom: 8px; border: 1px solid #E2E8F0;">
<div style="display: flex; justify-content: space-between;">
<b>{f['rule']}</b>
<span class="pill-badge" style="background: {sev_color};">{f['severity'].upper()} (+{f['points']} pts)</span>
</div>
<div style="font-size: 17px; color: #475569; margin-top: 4px;">{f['message']}</div>
</div>"""
                    st.markdown(finding_html, unsafe_allow_html=True)
                    
            with f_col2:
                st.markdown("#### 🧠 Predicted Knock-On Effects")
                
                knock_ons = explain(sim_req.get("payload"), opt2["findings"])
                for k in knock_ons:
                    knock_html = f"""<div style="background: #F8FAFD; border: 1px dashed #CBD5E1; padding: 12px 14px; border-radius: 8px; margin-bottom: 8px;">
<span style="color: #5C6BC0; font-weight: 700;">•</span> <span style="font-size: 17px; color: #334155;">{k}</span>
</div>"""
                    st.markdown(knock_html, unsafe_allow_html=True)
            
            # 4. Human Decision Action Center
            st.markdown("---")
            st.markdown('<div class="echo-card-header">Human-in-the-Loop Decision Authority</div>', unsafe_allow_html=True)
            
            d_col1, d_col2, d_col3 = st.columns([1.5, 1.5, 3])
            
            with d_col1:
                # Approve button
                target_to_apply = options[recommended_idx - 1].get("change") or sim_req.get("payload")
                btn_label = "✅ Approve Recommended" if recommended_idx != 1 else "✅ Approve Requested"
                if st.button(btn_label, type="primary", use_container_width=True):
                    if not can(user["role"], "approve"):
                        deny(user["role"], "approve", user["username"])
                        st.error("Permission denied: You do not have approve privileges.")
                    else:
                        if target_to_apply:
                            commit_change(target_to_apply)
                        set_status(sim_req["id"], "approved", by=user["username"])
                        st.success(f"Request {sim_req['id']} successfully approved and applied to live timetable!")
                        st.rerun()
                        
            with d_col2:
                # Reject button
                if st.button("❌ Reject Request", use_container_width=True):
                    if not can(user["role"], "reject"):
                        deny(user["role"], "reject", user["username"])
                        st.error("Permission denied: You do not have reject privileges.")
                    else:
                        set_status(sim_req["id"], "rejected", by=user["username"])
                        st.warning(f"Request {sim_req['id']} marked as rejected.")
                        st.rerun()

    # ==========================================
    # TAB 4: AUDIT LOG
    # ==========================================
    with tabs[3]:
        st.markdown('<div class="echo-card-header">Immutable Cryptographic Audit Trail</div>', unsafe_allow_html=True)
        
        logs = read_log()
        if not logs:
            st.info("No audit entries recorded yet.")
        else:
            # Build request map for issue lookup
            reqs = list_requests()
            req_map = {r["id"]: r for r in reqs if isinstance(r, dict) and "id" in r}
            for e in logs:
                det = e.get("details", {})
                if isinstance(det, dict) and det.get("request_id"):
                    rid = det.get("request_id")
                    if rid not in req_map and det.get("note"):
                        req_map[rid] = {"id": rid, "note": det.get("note")}

            log_filter = st.selectbox("Filter by Event:", ["All Events"] + list(set(e.get("event") for e in logs)), filter_mode=None)
            filtered_logs = logs if log_filter == "All Events" else [e for e in logs if e.get("event") == log_filter]
            
            # Format dataframe: 'Issue' as the first column and 'Timestamp (UTC)' as the last column
            log_table = []
            for e in reversed(filtered_logs):
                issue_desc = _resolve_audit_issue(e, req_map)
                log_table.append({
                    "Issue": issue_desc,
                    "Event": e.get("event"),
                    "User": e.get("user"),
                    "Details": str(e.get("details", {})),
                    "Timestamp (UTC)": e.get("timestamp")
                })
            st.dataframe(pd.DataFrame(log_table), use_container_width=True)


def _resolve_audit_issue(entry: dict, req_map: dict) -> str:
    """Extracts or resolves the faculty/student issue addressed by this audit record."""
    details = entry.get("details", {})
    if not isinstance(details, dict):
        details = {}
        
    req_id = details.get("request_id") or details.get("winner")
    
    # 1. Look up in active / historical request map
    if req_id and req_id in req_map:
        req = req_map[req_id]
        note = req.get("note") or req.get("payload", {}).get("text")
        if note:
            return str(note)
        p = req.get("payload", {})
        if p.get("slot_id") and p.get("new_lab_id"):
            return f"Relocation of {p.get('slot_id')} to Lab {p.get('new_lab_id')} ({p.get('new_day')} {p.get('new_hour')}:00)"

    # 2. Check if note is directly inside entry details
    if details.get("note"):
        return str(details.get("note"))

    # 3. Known fallback seeds
    known_seed = {
        "R001": "Section 3 AI Systems Lab move to Knuth Lab (L6) for high-performance GPUs",
        "R002": "Move Section 2 DB Lab to Lovelace Lab (L2) - schedule conflict",
        "R003": "Prof. Vance requesting Von Neumann Lab (L4) for Operating Systems Lab",
        "R004": "Dr. Davies requesting Von Neumann Lab (L4) for Web Cloud Lab",
        "R005": "Lab overcrowding: Section S03 AI Lab has insufficient workstations",
        "R006": "Machine deficit: Section S06 Cybersecurity Lab needs GPU workstations",
    }
    if req_id in known_seed:
        return known_seed[req_id]
        
    # 4. Contextual descriptions based on event
    event = entry.get("event", "")
    user = entry.get("user", "")
    
    if event == "conflict_resolved":
        w = details.get("winner", "Req A")
        l = details.get("loser", "Req B")
        return f"Lab room contention: Two faculty requested the same room/time ({w} vs {l})"
        
    if event in ("feedback_submitted", "request_created"):
        return details.get("note") or f"Feedback submitted regarding lab capacity ({req_id or 'New Request'})"
        
    if event in ("approved", "rejected"):
        status_word = "Approval" if event == "approved" else "Rejection"
        if req_id:
            return f"{status_word} of lab change request {req_id}"
        return f"Administrative action ({event})"
        
    if event == "simulate_class":
        if req_id:
            return f"Safety simulation check for request {req_id}"
        return "Timetable simulation execution"
        
    if event == "login_locked":
        return f"Security lockout: Rate limited after 5+ failed attempts ({details.get('username', user)})"
        
    if event == "login_failed":
        return f"Failed login: Invalid credentials provided for '{details.get('username', user)}'"
        
    if event == "login_ok":
        role = details.get("role", "user")
        return f"Authorized portal session established ({role.capitalize()}: {user})"
        
    if event == "access_denied":
        return f"RBAC access denied: Unauthorized attempt on '{details.get('action', 'resource')}'"
        
    return f"System operational event: {event}"

