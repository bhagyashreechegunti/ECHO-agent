"""
ECHO – Decision Safety Agent
Main Application Entrypoint & Role Router (Person B Implementation).
"""
import streamlit as st
import os

# Page config
st.set_page_config(
    page_title="ECHO – Decision Safety Agent",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

from ui_common import inject_theme
from auth import login, is_locked_out
from engine.timetable import reset_demo
import database
import importlib
import ui_admin
import ui_staff
import ui_student
import ui_common

importlib.reload(ui_admin)
importlib.reload(ui_staff)
importlib.reload(ui_student)
importlib.reload(ui_common)

# Inject pastel theme and animations
inject_theme()

# Session State Initialization
if "user" not in st.session_state:
    st.session_state["user"] = None

user = st.session_state.get("user")

# ==============================================================================
# 1. LOGIN SCREEN (When logged out)
# ==============================================================================
if not user:
    st.markdown("""
    <div style="text-align: center; margin-top: 20px; margin-bottom: 25px;">
        <div style="font-size: 42px; font-weight: 800; color: #1E293B; letter-spacing: -0.5px;">
            🛡️ ECHO <span style="color: #5C6BC0; font-weight: 300;">| Decision Safety Agent</span>
        </div>
        <div style="font-size: 19px; color: #64748B; margin-top: 6px;">
            Autonomous Timetable & Campus Decision Optimization with Human-in-the-Loop Safeguards
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_l, col_m, col_r = st.columns([1, 1.8, 1])
    
    with col_m:
        st.markdown('<div class="echo-card">', unsafe_allow_html=True)
        st.markdown("### 🔐 Secure System Sign In")
        st.caption("Enter your credentials or choose a pre-configured demo account below.")
        
        with st.form("login_form"):
            username = st.text_input("Username:", placeholder="e.g. admin, t2, student2").strip().lower()
            password = st.text_input("Password:", type="password", placeholder="Enter password")
            submit = st.form_submit_button("Sign In to ECHO", type="primary", use_container_width=True)
            
            if submit:
                if is_locked_out(username):
                    st.error("Account Temporarily Locked: 5 failed attempts detected in the last 5 minutes.")
                else:
                    auth_user = login(username, password)
                    if auth_user:
                        st.session_state["user"] = auth_user
                        st.success("Authentication successful! Redirecting...")
                        st.rerun()
                    else:
                        st.error("Wrong username or password")
                        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Quick Demo Login Selector for seamless evaluation
        st.markdown("""
        <div style="background: #FFFFFF; border-radius: 14px; padding: 18px; border: 1px dashed #CBD5E1; margin-top: 15px;">
            <div style="font-size: 17px; font-weight: 700; color: #475569; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px;">
                ⚡ One-Click Demo Personas (Evaluator Fast-Track)
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        d1, d2, d3 = st.columns(3)
        with d1:
            if st.button("👑 Admin\n(admin / admin123)", use_container_width=True):
                u = login("admin", "admin123")
                if u:
                    st.session_state["user"] = u
                    st.rerun()
        with d2:
            if st.button("👨‍🏫 Faculty (T2)\n(t2 / staff123)", use_container_width=True):
                u = login("t2", "staff123")
                if u:
                    st.session_state["user"] = u
                    st.rerun()
        with d3:
            if st.button("🎓 Student (S03)\n(student2 / student123)", use_container_width=True):
                u = login("student2", "student123")
                if u:
                    st.session_state["user"] = u
                    st.rerun()

        st.caption("ℹ️ Passwords in `data/users.csv` are cryptographically hashed using PBKDF2-HMAC-SHA256 with individual salts.")
        
    st.stop()


# ==============================================================================
# 2. LOGGED-IN SIDEBAR & NAVIGATION
# ==============================================================================
if user:
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 10px 0 16px 0;">
            <span style="font-size: 28px; font-weight: 800; color: #5C6BC0;">🛡️ ECHO</span>
            <div style="font-size: 15px; color: #94A3B8; text-transform: uppercase; letter-spacing: 1px;">Decision Safety Agent</div>
        </div>
        """, unsafe_allow_html=True)
        
        role = user.get("role", "admin").capitalize()
        role_color = {"Admin": "#7C68D0", "Staff": "#4A90E2", "Student": "#27AE60"}.get(role, "#5C6BC0")
        
        extra_info = ""
        if user.get("staff_id"):
            extra_info = f"Assigned Staff ID: <b>{user['staff_id']}</b>"
        elif user.get("section_id"):
            extra_info = f"Assigned Section: <b>{user['section_id']}</b>"
        elif role == "Admin":
            extra_info = "Access Level: <b>Full Administrative</b>"
            
        sidebar_html = f"""<div class="user-sidebar-card">
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
<div style="background: {role_color}; color: white; width: 42px; height: 42px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 20px;">
{user['username'][0].upper()}
</div>
<div>
<div style="font-weight: 700; color: #1E293B; font-size: 19px;">{user['username']}</div>
<div style="font-size: 16px; color: #64748B;">Role: <b style="color: {role_color};">{role}</b></div>
</div>
</div>
<div style="font-size: 15px; color: #64748B; border-top: 1px solid #EEF2F6; padding-top: 8px; margin-top: 6px;">
{extra_info}
</div>
</div>"""
        st.markdown(sidebar_html, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Reset Demo State Button
        st.markdown("#### 🔄 Demo Controls")
        if st.button("Reset Demo State (Restore R1-R4)", use_container_width=True, help="Restores slots.csv to slots_live.csv and re-seeds demo change requests R1 to R4."):
            reset_demo()
            st.session_state["active_sim_req"] = None
            st.success("Demo state successfully reset to original seed data!")
            st.rerun()

        st.markdown("---")
        
        # Fast Role Switcher for convenience during presentation
        st.markdown("#### 🔄 Switch Role (Demo)")
        c_sw1, c_sw2, c_sw3 = st.columns(3)
        with c_sw1:
            if st.button("Admin", key="sw_admin"):
                st.session_state["user"] = login("admin", "admin123")
                st.rerun()
        with c_sw2:
            if st.button("Staff (T2)", key="sw_t2"):
                st.session_state["user"] = login("t2", "staff123")
                st.rerun()
        with c_sw3:
            if st.button("Student", key="sw_student"):
                st.session_state["user"] = login("student2", "student123")
                st.rerun()
                
        st.markdown("---")
        
        # Logout
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state["user"] = None
            st.session_state["active_sim_req"] = None
            st.rerun()


    # ==============================================================================
    # 3. ROLE ROUTER
    # ==============================================================================
    user_role = user.get("role", "").lower()

    if user_role == "admin":
        ui_admin.render(user)
    elif user_role == "staff":
        ui_staff.render(user)
    elif user_role == "student":
        ui_student.render(user)
    else:
        st.error(f"Unrecognized role '{user_role}'. Please log in again.")
