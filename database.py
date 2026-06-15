import sqlite3
import hashlib
import json
import os
from datetime import datetime

import os
DB_PATH = os.path.join("/tmp", "interview_coach.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT UNIQUE NOT NULL,
            email      TEXT UNIQUE,
            password   TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            date       TEXT NOT NULL,
            role       TEXT,
            mode       TEXT DEFAULT 'practice',
            avg_scores TEXT NOT NULL,
            results    TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()

def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, email, password):
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    try:
        conn = get_conn()
        conn.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username.strip(), email.strip() or None, hash_pw(password))
        )
        conn.commit()
        conn.close()
        return True, "Account created! Please log in."
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            return False, "Username already taken."
        if "email" in str(e):
            return False, "Email already registered."
        return False, "Registration failed."

def login_user(username, password):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username.strip(), hash_pw(password))
    ).fetchone()
    conn.close()
    if row:
        return {"id": row["id"], "username": row["username"], "email": row["email"]}
    return None

def save_session(user_id, role, mode, avg_scores, results):
    conn = get_conn()
    conn.execute(
        "INSERT INTO sessions (user_id, date, role, mode, avg_scores, results) VALUES (?,?,?,?,?,?)",
        (
            user_id,
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            role or "General",
            mode or "practice",
            json.dumps(avg_scores),
            json.dumps(results)
        )
    )
    conn.commit()
    conn.close()

def get_sessions(user_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM sessions WHERE user_id = ? ORDER BY date ASC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [
        {
            "id":         row["id"],
            "date":       row["date"],
            "role":       row["role"],
            "mode":       row["mode"],
            "avg_scores": json.loads(row["avg_scores"]),
            "results":    json.loads(row["results"])
        }
        for row in rows
    ]

def get_weakest_dim(user_id):
    sessions = get_sessions(user_id)
    if not sessions:
        return "structure"
    dims = ["clarity", "specificity", "relevance", "structure", "impact"]
    totals = {d: 0 for d in dims}
    for s in sessions:
        for d in dims:
            totals[d] += s["avg_scores"].get(d, 0)
    count = len(sessions)
    avgs = {d: totals[d] / count for d in dims}
    return min(avgs, key=avgs.get)

def delete_account(user_id):
    conn = get_conn()
    conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()