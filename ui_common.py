"""
Common UI components, styling, themes, animations, and timetable grid visualizers for ECHO.
Palette: Pastel Blue (#4A90E2 / #5C6BC0), Lavender (#9B86EC / #EDE7F6), White (#FFFFFF), Slate (#2D3748).
"""
import streamlit as st
import pandas as pd

PASTEL_CSS = """
<style>
/* Modern styling with smooth animations */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #2D3748;
    font-size: 18px !important; /* +4px from default 14px */
}

/* Global Typography Boost (+4px) */
p, span, label, div, a, li {
    font-size: 18px;
}

.stMarkdown, .stMarkdown p {
    font-size: 18px !important;
}

.stCaption, small, .stCaption p {
    font-size: 16px !important; /* +4px from 12px */
}

input, select, textarea, .stTextInput input, .stTextArea textarea, .stSelectbox div {
    font-size: 18px !important;
}

button, .stButton button {
    font-size: 18px !important;
}

[data-testid="stDataFrame"] * {
    font-size: 16px !important; /* +4px from default ~12px */
}

/* Ensure all selectboxes have click-only pointer cursors and non-editable appearance */
div[data-testid="stSelectbox"] div[data-baseweb="select"] {
    cursor: pointer !important;
}
div[data-testid="stSelectbox"] input {
    cursor: pointer !important;
    caret-color: transparent !important;
    user-select: none !important;
}

h1 { font-size: 36px !important; }
h2 { font-size: 30px !important; }
h3 { font-size: 24px !important; }
h4 { font-size: 20px !important; }

/* Background gradient */
.stApp {
    background: linear-gradient(135deg, #F8FAFD 0%, #F1F4FA 50%, #EDE9F6 100%);
    background-attachment: fixed;
}

/* Custom Header Banner */
.echo-header {
    background: linear-gradient(120deg, #FFFFFF 0%, #F4F7FC 60%, #EFEBF8 100%);
    padding: 24px 30px;
    border-radius: 18px;
    border: 1px solid rgba(215, 224, 245, 0.8);
    box-shadow: 0 8px 24px rgba(92, 107, 192, 0.07);
    margin-bottom: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: all 0.3s ease;
}

.echo-title {
    font-size: 30px; /* was 26px (+4px) */
    font-weight: 700;
    color: #2D3748;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 12px;
}

.echo-badge {
    background: linear-gradient(135deg, #5C6BC0, #7986CB);
    color: white;
    font-size: 15px; /* was 11px (+4px) */
    font-weight: 600;
    padding: 5px 12px;
    border-radius: 20px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

/* Glassmorphism Cards */
.echo-card {
    background: #FFFFFF;
    border-radius: 16px;
    border: 1px solid rgba(226, 232, 240, 0.85);
    padding: 22px 24px;
    box-shadow: 0 6px 18px rgba(92, 107, 192, 0.05);
    margin-bottom: 20px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.echo-card:hover {
    box-shadow: 0 10px 24px rgba(92, 107, 192, 0.09);
}

.echo-card-header {
    font-size: 21px; /* was 17px (+4px) */
    font-weight: 600;
    color: #334155;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
    border-bottom: 1px solid #F1F5F9;
    padding-bottom: 10px;
}

/* Highlighted Verdict Banner */
.verdict-banner-approve {
    background: linear-gradient(120deg, #EBFBEE 0%, #E3F8E7 100%);
    border: 1.5px solid #82E0AA;
    color: #1E663B;
    padding: 18px 22px;
    border-radius: 14px;
    box-shadow: 0 4px 14px rgba(46, 204, 113, 0.12);
    margin: 18px 0;
    animation: fadeIn 0.4s ease-in;
}

.verdict-banner-safer {
    background: linear-gradient(120deg, #EFF4FE 0%, #E8EEFB 100%);
    border: 1.5px solid #85B5F7;
    color: #1A5276;
    padding: 18px 22px;
    border-radius: 14px;
    box-shadow: 0 4px 14px rgba(52, 152, 219, 0.12);
    margin: 18px 0;
    animation: fadeIn 0.4s ease-in;
}

.verdict-banner-reject {
    background: linear-gradient(120deg, #FDECEC 0%, #FCE8E8 100%);
    border: 1.5px solid #F1948A;
    color: #7B241C;
    padding: 18px 22px;
    border-radius: 14px;
    box-shadow: 0 4px 14px rgba(231, 76, 60, 0.12);
    margin: 18px 0;
    animation: fadeIn 0.4s ease-in;
}

/* Conflict Banner (Amber) */
.conflict-card {
    background: linear-gradient(135deg, #FEF9E7 0%, #FDF2E9 100%);
    border: 1.5px solid #F5CBA7;
    border-left: 6px solid #E67E22;
    padding: 20px 24px;
    border-radius: 14px;
    box-shadow: 0 6px 18px rgba(230, 126, 34, 0.08);
    margin-bottom: 24px;
    animation: pulseGlow 2.5s infinite alternate;
}

@keyframes pulseGlow {
    0% { box-shadow: 0 4px 12px rgba(230, 126, 34, 0.08); }
    100% { box-shadow: 0 8px 22px rgba(230, 126, 34, 0.18); }
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Metric Pill Badges */
.pill-badge {
    display: inline-block;
    padding: 5px 14px;
    font-size: 16px; /* was 12px (+4px) */
    font-weight: 600;
    border-radius: 14px;
    margin: 2px 4px;
}
.pill-purple { background: #EDE7F6; color: #5E35B1; }
.pill-blue { background: #E3F2FD; color: #1976D2; }
.pill-green { background: #E8F5E9; color: #2E7D32; }
.pill-amber { background: #FFF3E0; color: #E65100; }
.pill-red { background: #FFEBEE; color: #C62828; }

/* Custom Streamlit component refinements */
div[data-testid="stMetricValue"] {
    font-size: 32px !important;
    font-weight: 700;
    color: #2D3748;
}

div[data-testid="stMetricLabel"] {
    font-size: 18px !important; /* +4px */
}

button[kind="primary"] {
    background: linear-gradient(135deg, #5C6BC0, #7986CB) !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 18px !important;
    box-shadow: 0 4px 12px rgba(92, 107, 192, 0.25) !important;
    transition: all 0.2s ease !important;
}

button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 16px rgba(92, 107, 192, 0.35) !important;
}

button[kind="secondary"] {
    border-radius: 10px !important;
    border: 1px solid #CBD5E1 !important;
    font-size: 18px !important;
    transition: all 0.2s ease !important;
}

/* Tab design */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: rgba(238, 242, 246, 0.7);
    padding: 8px;
    border-radius: 14px;
    margin-bottom: 20px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 10px 22px;
    font-weight: 600;
    font-size: 18px; /* was 14px (+4px) */
    color: #64748B;
    border: none;
    background-color: transparent;
    transition: all 0.2s ease;
}

.stTabs [aria-selected="true"] {
    background-color: #FFFFFF !important;
    color: #5C6BC0 !important;
    box-shadow: 0 4px 12px rgba(92, 107, 192, 0.12) !important;
}

/* User sidebar badge */
.user-sidebar-card {
    background: linear-gradient(135deg, #FFFFFF, #F5F7FD);
    border: 1px solid rgba(200, 212, 245, 0.9);
    border-radius: 14px;
    padding: 18px;
    margin-bottom: 18px;
    box-shadow: 0 4px 12px rgba(92, 107, 192, 0.08);
}
</style>
"""

def inject_theme():
    """Injects pastel styling and animation CSS into the app."""
    st.markdown(PASTEL_CSS, unsafe_allow_html=True)

def render_top_header(title="ECHO Decision Safety Agent", role="Admin", user="admin", subtitle=None):
    """Renders top header card with role badge and system status."""
    role_color = {
        "admin": "linear-gradient(135deg, #7C68D0, #9B86EC)",
        "staff": "linear-gradient(135deg, #4A90E2, #6C8CD5)",
        "student": "linear-gradient(135deg, #27AE60, #2ECC71)"
    }.get(role.lower(), "linear-gradient(135deg, #5C6BC0, #7986CB)")
    
    # Hide subtitle for student portal as requested
    if subtitle is None:
        if role.lower() == "student":
            subtitle = ""
        else:
            subtitle = "Human-in-the-Loop Safe Decision Engine & Multi-Agent Timetable Optimization"
            
    sub_div = f'<div style="font-size: 17px; color: #64748B; margin-top: 4px;">{subtitle}</div>' if subtitle else ''
    
    st.markdown(f"""<div class="echo-header">
<div>
<div class="echo-title">
🛡️ {title}
</div>
{sub_div}
</div>
<div style="display: flex; align-items: center; gap: 10px;">
<span style="font-size: 17px; color: #64748B;">Signed in as <b>{user}</b></span>
<span class="echo-badge" style="background: {role_color};">
{role.upper()}
</span>
</div>
</div>""", unsafe_allow_html=True)

def timetable_grid(slots: pd.DataFrame, filter_col: str, filter_value: str) -> pd.DataFrame:
    """
    Renders weekly timetable grid:
    Hours (8 to 16) as rows and Monday to Friday as columns.
    Each cell shows subject, lab id, staff id joined as text.
    Returns the pivot DataFrame for display.
    """
    if slots.empty:
        return pd.DataFrame()
        
    filtered = slots[slots[filter_col].astype(str).str.upper() == str(filter_value).upper()].copy()
    
    days_order = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    hours_order = list(range(8, 17))
    hour_labels = [f"{h:02d}:00" for h in hours_order]
    
    # Initialize empty grid with matching string hour labels
    grid_data = {d: {f"{h:02d}:00": "" for h in hours_order} for d in days_order}
    
    for _, row in filtered.iterrows():
        d = str(row["day"])
        h = int(row["hour"])
        h_key = f"{h:02d}:00"
        if d in grid_data and h_key in grid_data[d]:
            subj = str(row.get("subject", "Class"))
            kind = str(row.get("kind", ""))
            lab = str(row.get("lab_id", "")).strip()
            staff = str(row.get("staff_id", "")).strip()
            sec = str(row.get("section_id", "")).strip()
            
            # Format cell content with clean, aligned indicators
            if kind == "lab" and lab and lab != "nan":
                if filter_col == "lab_id":
                    parts = ["[LAB]", subj, f"Sec {sec}", f"({staff})" if staff else ""]
                elif filter_col == "staff_id":
                    parts = [f"[LAB {lab}]", subj, f"Sec {sec}"]
                else:  # section_id (Student or Admin Section view)
                    parts = [f"[LAB {lab}]", subj, f"({staff})" if staff else ""]
            else:
                if filter_col == "staff_id" or filter_col == "lab_id":
                    parts = ["[LEC]", subj, f"Sec {sec}"]
                else:
                    parts = ["[LEC]", subj, f"({staff})" if staff else ""]
                    
            clean_parts = [p for p in parts if p]
            cell_text = " • ".join(clean_parts)
            
            # If multiple sessions clashing in this cell, mark alert
            if grid_data[d][h_key]:
                grid_data[d][h_key] += f" | ⚠️ CLASH: {cell_text}"
            else:
                grid_data[d][h_key] = cell_text
                
    df_grid = pd.DataFrame(grid_data, index=hour_labels)
    df_grid = df_grid.fillna("")
    return df_grid

def render_risk_gauge(score: int, title: str = "Risk Score"):
    """Renders visual risk score bar / meter with pastel coloring."""
    if score <= 20:
        bar_color = "linear-gradient(90deg, #A8E6CF, #56C596)"
        badge_text = "SAFE / LOW RISK"
        badge_bg = "#E8F8F5"
        text_color = "#117A65"
    elif score <= 50:
        bar_color = "linear-gradient(90deg, #F9E79F, #F39C12)"
        badge_text = "MODERATE RISK"
        badge_bg = "#FEF9E7"
        text_color = "#B7950B"
    else:
        bar_color = "linear-gradient(90deg, #F5B7B1, #E74C3C)"
        badge_text = "HIGH / CRITICAL RISK"
        badge_bg = "#FDEDEC"
        text_color = "#922B21"
        
    gauge_html = f"""<div style="background: #FFFFFF; border-radius: 14px; padding: 16px; border: 1px solid #E2E8F0; margin-bottom: 14px;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
<span style="font-size: 18px; font-weight: 600; color: #475569;">{title}</span>
<span style="background: {badge_bg}; color: {text_color}; font-size: 15px; font-weight: 700; padding: 4px 12px; border-radius: 20px;">{badge_text}</span>
</div>
<div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 8px;">
<span style="font-size: 36px; font-weight: 800; color: #1E293B;">{score}</span>
<span style="font-size: 18px; color: #94A3B8; font-weight: 500;">/ 100</span>
</div>
<div style="background: #EEF2F6; border-radius: 10px; height: 12px; overflow: hidden; width: 100%;">
<div style="width: {min(100, max(2, score))}%; background: {bar_color}; height: 100%; border-radius: 10px; transition: width 0.6s ease;"></div>
</div>
</div>"""
    st.markdown(gauge_html, unsafe_allow_html=True)

def render_options_comparison_chart(options: list, recommended_idx: int):
    """Renders visual 3-way risk comparison cards using native Streamlit containers."""
    cols = st.columns(3)
    for i, opt in enumerate(options):
        is_rec = (i + 1 == recommended_idx)
        with cols[i]:
            with st.container(border=True):
                if is_rec:
                    st.markdown('<span class="pill-badge pill-purple" style="margin-bottom: 8px;">⭐ RECOMMENDED</span>', unsafe_allow_html=True)
                st.markdown(f"**{opt['name']}**")
                st.caption(opt["description"])
                st.metric("Risk Score", f"{opt['risk']['score']} / 100")
                counts = opt["risk"]["counts"]
                db = counts.get("lab_double_booking", 0)
                stf = counts.get("staff_clash", 0)
                st.caption(f"Double-bookings: **{db}** • Staff: **{stf}**")
