"""
User account generator with PBKDF2-HMAC-SHA256 password hashing.
Generates data/users.csv with demo credentials.
"""
import os
import hashlib
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)

def hash_password(password, salt=None):
    salt = salt or os.urandom(16)
    h = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 200_000)
    return salt.hex(), h.hex()

def verify(password, salt_hex, hash_hex):
    h = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt_hex), 200_000)
    import hmac
    return hmac.compare_digest(h.hex(), hash_hex)

users = [
    # Admin
    {"username": "admin", "password": "admin123", "role": "admin", "rank": 3, "staff_id": "", "section_id": ""},
    # 8 Staff
    {"username": "t1", "password": "staff123", "role": "staff", "rank": 3, "staff_id": "T1", "section_id": ""},
    {"username": "t2", "password": "staff123", "role": "staff", "rank": 3, "staff_id": "T2", "section_id": ""},
    {"username": "t3", "password": "staff123", "role": "staff", "rank": 2, "staff_id": "T3", "section_id": ""},
    {"username": "t4", "password": "staff123", "role": "staff", "rank": 1, "staff_id": "T4", "section_id": ""},
    {"username": "t5", "password": "staff123", "role": "staff", "rank": 2, "staff_id": "T5", "section_id": ""},
    {"username": "t6", "password": "staff123", "role": "staff", "rank": 2, "staff_id": "T6", "section_id": ""},
    {"username": "t7", "password": "staff123", "role": "staff", "rank": 1, "staff_id": "T7", "section_id": ""},
    {"username": "t8", "password": "staff123", "role": "staff", "rank": 1, "staff_id": "T8", "section_id": ""},
    # 3 Students
    {"username": "student1", "password": "student123", "role": "student", "rank": 0, "staff_id": "", "section_id": "S01"},
    {"username": "student2", "password": "student123", "role": "student", "rank": 0, "staff_id": "", "section_id": "S03"},
    {"username": "student3", "password": "student123", "role": "student", "rank": 0, "staff_id": "", "section_id": "S07"},
]

rows = []
for u in users:
    salt_hex, hash_hex = hash_password(u["password"])
    rows.append({
        "username": u["username"],
        "salt": salt_hex,
        "password_hash": hash_hex,
        "role": u["role"],
        "rank": u["rank"],
        "staff_id": u["staff_id"],
        "section_id": u["section_id"]
    })

df_users = pd.DataFrame(rows)
df_users.to_csv(os.path.join(DATA_DIR, "users.csv"), index=False)
print("Created data/users.csv with salted PBKDF2 hashes!")
