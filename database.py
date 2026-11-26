"""
ECHO Database Layer.
Provides relational SQLite database storage, ACID transaction support,
table schemas, and synchronization with CSV/JSON datasets.
"""
import os
import sqlite3
import json
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "echo.db")

def get_connection():
    """Returns a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the relational database schema and syncs baseline data."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        role TEXT NOT NULL,
        rank INTEGER DEFAULT 1,
        staff_id TEXT,
        section_id TEXT
    );
    """)

    # 2. Sections Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sections (
        section_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        size INTEGER NOT NULL
    );
    """)

    # 3. Laboratories Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS labs (
        lab_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        capacity INTEGER NOT NULL
    );
    """)

    # 4. Academic Staff Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS staff (
        staff_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        rank_title TEXT NOT NULL,
        rank_level INTEGER NOT NULL
    );
    """)

    # 5. Master Timetable Slots Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS timetable_slots (
        slot_id TEXT PRIMARY KEY,
        section_id TEXT NOT NULL,
        subject TEXT NOT NULL,
        staff_id TEXT,
        day TEXT NOT NULL,
        hour INTEGER NOT NULL,
        kind TEXT NOT NULL,
        lab_id TEXT,
        FOREIGN KEY (section_id) REFERENCES sections(section_id),
        FOREIGN KEY (lab_id) REFERENCES labs(lab_id)
    );
    """)

    # 6. Change Requests Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS change_requests (
        id TEXT PRIMARY KEY,
        kind TEXT NOT NULL,
        requester TEXT NOT NULL,
        role TEXT NOT NULL,
        rank INTEGER DEFAULT 1,
        created TEXT NOT NULL,
        status TEXT NOT NULL,
        payload JSON,
        note TEXT
    );
    """)

    # 7. Immutable Audit Trail Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        event TEXT NOT NULL,
        user TEXT NOT NULL,
        details JSON
    );
    """)

    conn.commit()
    conn.close()
    
    # Sync from CSV/JSON into SQLite
    sync_from_files()

def sync_from_files():
    """Synchronizes file-based datasets (CSV/JSON) into relational SQLite tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # Sync Sections
    sections_csv = os.path.join(DATA_DIR, "sections.csv")
    if os.path.exists(sections_csv):
        df_sec = pd.read_csv(sections_csv)
        for _, row in df_sec.iterrows():
            cursor.execute("""
            INSERT OR REPLACE INTO sections (section_id, name, size)
            VALUES (?, ?, ?)
            """, (str(row["section_id"]), str(row["name"]), int(row["size"])))

    # Sync Labs
    labs_csv = os.path.join(DATA_DIR, "labs.csv")
    if os.path.exists(labs_csv):
        df_labs = pd.read_csv(labs_csv)
        for _, row in df_labs.iterrows():
            cursor.execute("""
            INSERT OR REPLACE INTO labs (lab_id, name, capacity)
            VALUES (?, ?, ?)
            """, (str(row["lab_id"]), str(row["name"]), int(row["capacity"])))

    # Sync Staff
    staff_csv = os.path.join(DATA_DIR, "staff.csv")
    if os.path.exists(staff_csv):
        df_staff = pd.read_csv(staff_csv)
        rank_map = {"Professor": 3, "Associate": 2, "Assistant": 1}
        for _, row in df_staff.iterrows():
            rt = str(row["rank"])
            rl = rank_map.get(rt, 1)
            cursor.execute("""
            INSERT OR REPLACE INTO staff (staff_id, name, rank_title, rank_level)
            VALUES (?, ?, ?, ?)
            """, (str(row["staff_id"]), str(row["name"]), rt, rl))

    # Sync Slots (Live or Baseline)
    live_csv = os.path.join(DATA_DIR, "slots_live.csv")
    base_csv = os.path.join(DATA_DIR, "slots.csv")
    slots_file = live_csv if os.path.exists(live_csv) else base_csv
    if os.path.exists(slots_file):
        df_slots = pd.read_csv(slots_file)
        for _, row in df_slots.iterrows():
            cursor.execute("""
            INSERT OR REPLACE INTO timetable_slots (slot_id, section_id, subject, staff_id, day, hour, kind, lab_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(row["slot_id"]),
                str(row["section_id"]),
                str(row["subject"]),
                str(row["staff_id"]) if pd.notna(row["staff_id"]) else "",
                str(row["day"]),
                int(row["hour"]),
                str(row["kind"]),
                str(row["lab_id"]) if pd.notna(row["lab_id"]) else ""
            ))

    # Sync Users
    users_csv = os.path.join(DATA_DIR, "users.csv")
    if os.path.exists(users_csv):
        try:
            df_u = pd.read_csv(users_csv)
            for _, row in df_u.iterrows():
                cursor.execute("""
                INSERT OR REPLACE INTO users (username, password_hash, salt, role, rank, staff_id, section_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(row["username"]),
                    str(row["password_hash"]),
                    str(row["salt"]),
                    str(row["role"]),
                    int(row["rank"]) if pd.notna(row["rank"]) else 1,
                    str(row["staff_id"]) if pd.notna(row["staff_id"]) else "",
                    str(row["section_id"]) if pd.notna(row["section_id"]) else ""
                ))
        except Exception:
            pass

    # Sync Audit Logs
    audit_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audit.log")
    if os.path.exists(audit_file):
        try:
            with open(audit_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entry = json.loads(line)
                        cursor.execute("""
                        INSERT INTO audit_logs (timestamp, event, user, details)
                        VALUES (?, ?, ?, ?)
                        """, (
                            entry.get("timestamp"),
                            entry.get("event"),
                            entry.get("user"),
                            json.dumps(entry.get("details", {}))
                        ))
        except Exception:
            pass

    # Sync Requests
    requests_json = os.path.join(DATA_DIR, "requests.json")
    if os.path.exists(requests_json):
        try:
            with open(requests_json, "r", encoding="utf-8") as f:
                requests = json.load(f)
            for r in requests:
                cursor.execute("""
                INSERT OR REPLACE INTO change_requests (id, kind, requester, role, rank, created, status, payload, note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    r.get("id"),
                    r.get("kind"),
                    r.get("requester"),
                    r.get("role"),
                    r.get("rank", 1),
                    r.get("created"),
                    r.get("status"),
                    json.dumps(r.get("payload", {})),
                    r.get("note", "")
                ))
        except Exception:
            pass

    conn.commit()
    conn.close()

def get_database_stats() -> dict:
    """Returns total record counts across all relational database tables."""
    conn = get_connection()
    cursor = conn.cursor()
    stats = {}
    tables = ["users", "sections", "labs", "staff", "timetable_slots", "change_requests", "audit_logs"]
    for t in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {t}")
            stats[t] = cursor.fetchone()[0]
        except Exception:
            stats[t] = 0
    conn.close()
    return stats

# Initialize schema on first import
init_db()
