# ECHO Agent – Decision Safety Agent

**ECHO Agent** is an enterprise-grade Decision Safety Agent and Timetable Optimization Engine designed with Human-in-the-Loop (HITL) governance. The agent autonomously simulates alternatives, computes deterministic risk penalties, predicts operational knock-on disruptions, and arbitrates multi-staff resource contentions—while preserving complete final decision authority in administrative hands (*"The agent only recommends. You decide"*).

---

## 🏛️ The Five Core Pillars of ECHO Agent

ECHO Agent is architected across five comprehensive engineering pillars:

### 1. 🎨 Frontend
- **Streamlit Interactive Portals**: Tailored interfaces for **Administrator**, **Faculty (Staff)**, and **Student** personas.
- **Visual Design System**: Soft pastel theme (Pastel Blue `#5C6BC0`, Lavender `#EDE7F6`, Off-White `#F8FAFD`, Slate `#2D3748`) with glassmorphic cards and smooth CSS animations.
- **Accessible Typography**: Enhanced readable typography (+4px project-wide boost) with clear visual hierarchy.
- **Native Non-Editable Dropdowns**: Click-to-select dropdown menus across all dashboards with typing disabled (`filter_mode=None`) and pointer-cursor enforcement.
- **Three-Way Decision Simulation**: Side-by-side comparative visualization of **Option 1 (Baseline)**, **Option 2 (Requested)**, and **Option 3 (Safer Alternative)** with color-coded risk gauges.
- **Interactive Master Timetable Grids**: Live weekly schedules across 10 academic cohorts (S01–S10) and 9 campus laboratories (L1–L9).

### 2. ⚙️ Backend
- **Deterministic Constraint Engine ([engine/timetable_checks.py](file:///c:/Users/bhagyashree/OneDrive/Desktop/ECHO-frontend-demo/engine/timetable_checks.py))**: High-speed hash-map verification of Section Clashes (wt 3), Faculty Clashes (wt 4), Lab Double-Bookings (wt 8), and Room Capacity Deficits (wt 5).
- **High-Performance Simulation ($O(1)$ Indexed Pruning)**: Fast candidate search in [engine/change_requests.py](file:///c:/Users/bhagyashree/OneDrive/Desktop/ECHO-frontend-demo/engine/change_requests.py) that evaluates alternatives in **~30 milliseconds** (a 200× speedup over un-indexed algorithms).
- **Two-Staff Conflict Arbitrator**: Automated multi-agent dispute resolution applying flexibility check (alternative availability), academic seniority ranking (Professor > Associate > Assistant), and submission timestamps.
- **AI Operational Predictor ([ai.py](file:///c:/Users/bhagyashree/OneDrive/Desktop/ECHO-frontend-demo/ai.py))**: Derives natural-language knock-on operational risks strictly from counted constraint facts without ungrounded hallucinations.

### 3. 🗄️ Database
- **Dual-Layer Persistent Storage**:
  - **Relational SQL Database ([database.py](file:///c:/Users/bhagyashree/OneDrive/Desktop/ECHO-frontend-demo/database.py))**: SQLite database (`data/echo.db`) enforcing relational schemas, primary/foreign keys, and ACID transactions across `users`, `sections`, `labs`, `staff`, `timetable_slots`, `change_requests`, and `audit_logs`.
  - **Structured Flat-File Store**: Synchronized CSV and JSON datasets (`data/slots.csv`, `data/slots_live.csv`, `data/sections.csv`, `data/labs.csv`, `data/staff.csv`, `data/users.csv`, `data/requests.json`, `data/ai_cache.json`).
- **Dynamic Live Synchronization**: Real-time synchronization ensuring approvals instantly update live schedules without data drift.

### 4. 🛡️ Security
- **Cryptographic Password Security ([create_users.py](file:///c:/Users/bhagyashree/OneDrive/Desktop/ECHO-frontend-demo/scripts/create_users.py))**: Salted PBKDF2-HMAC-SHA256 password hashing (100,000 iterations) with unique per-user 16-byte cryptographic salts.
- **Role-Based Access Control (RBAC)**: Centralized authorization matrix (`auth.py`) enforcing strict permission boundaries for `admin`, `staff`, and `student` roles.
- **Account Lockout Defense**: Automated rate-limiting and brute-force mitigation locking out accounts after 5 consecutive failed authentication attempts.
- **Prompt Injection Defense ([security.py](file:///c:/Users/bhagyashree/OneDrive/Desktop/ECHO-frontend-demo/security.py))**: Automated heuristic and pattern-matching sanitization shielding feedback ingestion against prompt injection, jailbreaking, and SQL/shell injection.
- **Immutable Cryptographic Audit Trail ([audit.py](file:///c:/Users/bhagyashree/OneDrive/Desktop/ECHO-frontend-demo/audit.py))**: Append-only log recording all security events, logins, simulations, decisions, and lockouts with operational issues listed first and UTC timestamps.

### 5. 📊 Management
- **Administrative Governance Center**: Full Human-in-the-Loop decision sign-off; autonomous AI recommendations require explicit administrative approval before mutating live tables.
- **Resource & Capacity Monitoring**: Live metrics tracking laboratory capacity, utilization rates, and scheduled bookings.
- **Request Lifecycle Management**: Full state tracking (`pending`, `approved`, `rejected`) across faculty relocation proposals and student room bottleneck reports.
- **Disaster Recovery & State Reset**: One-click demo state recovery (`reset_demo`) restoring pristine baseline timetable schedules and seeded scenario requests.

---

## 🚀 Quick Start

### 1. Requirements
Ensure Python 3.10+ is installed:
```bash
pip install streamlit pandas
```

### 2. Run the Application
```bash
streamlit run app.py --server.port 8502
```


## 📂 Project Structure

```text
ECHO-agent/
├── .streamlit/
│   ├── config.toml           # Pastel theme configuration
│   └── credentials.toml      # Streamlit local credentials bypass
├── app.py                    # Main application router & persona manager
├── database.py               # Relational SQLite database schema & sync engine
├── auth.py                   # PBKDF2 authentication, RBAC, and lockout detection
├── security.py               # Prompt injection defense & input sanitization
├── audit.py                  # Immutable audit trail logger
├── ai.py                     # AI knock-on predictor & feedback translator
├── ui_common.py              # CSS styles, typography (+4px), timetable grids, charts
├── ui_admin.py               # Administrator control center & simulation tabs
├── ui_staff.py               # Faculty dashboard & relocation submission
├── ui_student.py             # Student dashboard & feedback tracker
├── engine/
│   ├── timetable.py          # Timetable state manager & change applier
│   ├── timetable_checks.py   # Hash-map constraint solver (clashes & capacity)
│   ├── timetable_scorer.py   # Deterministic risk scoring & findings
│   └── change_requests.py    # Request queues, 3-way simulation & conflict resolver
├── redteam/
│   ├── runner.py             # 8 AI safety defense scenarios
│   └── access.py             # 8 RBAC & security boundary tests
├── scripts/
│   ├── generate_timetable.py # Baseline synthetic timetable generator
│   └── create_users.py       # Cryptographic user password generator
├── tests/
│   ├── test_timetable.py     # Timetable constraint validation unit tests
│   └── test_auth.py          # Security, RBAC, and Red Team tests
├── data/                     # Relational DB, CSVs, and JSON stores
│   ├── echo.db               # SQLite relational database
│   ├── sections.csv          # Academic cohorts and strengths
│   ├── labs.csv              # Laboratories and capacities
│   ├── staff.csv             # Academic staff and ranks
│   ├── slots.csv             # Baseline master timetable
│   ├── slots_live.csv        # Live timetable state
│   ├── users.csv             # Salted password hashes & roles
│   └── requests.json         # Queued change requests
└── README.md                 # Project documentation
```
