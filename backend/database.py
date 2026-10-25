import sqlite3
import os
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "lifepilot.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Tasks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        category TEXT NOT NULL DEFAULT 'Work',
        priority TEXT NOT NULL DEFAULT 'important_not_urgent',
        status TEXT NOT NULL DEFAULT 'pending',
        estimated_duration INTEGER NOT NULL DEFAULT 30,
        deadline TEXT NOT NULL,
        scheduled_start TEXT,
        scheduled_end TEXT,
        created_at TEXT NOT NULL,
        completed_at TEXT,
        order_index INTEGER DEFAULT 0
    )
    """)

    # Habits table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS habits (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        category TEXT NOT NULL DEFAULT 'Personal',
        frequency TEXT NOT NULL DEFAULT 'daily',
        target_days_per_week INTEGER DEFAULT 7,
        icon TEXT DEFAULT 'sparkles',
        color TEXT DEFAULT '#3b82f6',
        created_at TEXT NOT NULL
    )
    """)

    # Habit Logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS habit_logs (
        id TEXT PRIMARY KEY,
        habit_id TEXT NOT NULL,
        log_date TEXT NOT NULL,
        completed INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE,
        UNIQUE(habit_id, log_date)
    )
    """)

    # Focus Sessions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS focus_sessions (
        id TEXT PRIMARY KEY,
        task_id TEXT,
        task_title TEXT NOT NULL,
        mode TEXT NOT NULL DEFAULT 'work',
        duration_minutes INTEGER NOT NULL,
        completed_at TEXT NOT NULL,
        notes TEXT DEFAULT ''
    )
    """)

    # User Settings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_settings (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        user_name TEXT DEFAULT 'User',
        work_start_time TEXT DEFAULT '09:00',
        work_end_time TEXT DEFAULT '18:00',
        buffer_minutes INTEGER DEFAULT 15,
        pomodoro_work_duration INTEGER DEFAULT 25,
        pomodoro_break_duration INTEGER DEFAULT 5,
        pomodoro_long_break_duration INTEGER DEFAULT 15,
        theme TEXT DEFAULT 'light',
        notifications_enabled INTEGER DEFAULT 1,
        ai_provider TEXT DEFAULT 'auto',
        gemini_api_key TEXT DEFAULT '',
        timezone TEXT DEFAULT 'auto'
    )
    """)

    # Add timezone column if missing in existing database
    cursor.execute("PRAGMA table_info(user_settings)")
    settings_cols = [r["name"] for r in cursor.fetchall()]
    if "timezone" not in settings_cols:
        try:
            cursor.execute("ALTER TABLE user_settings ADD COLUMN timezone TEXT DEFAULT 'auto'")
        except Exception:
            pass

    # Chat Messages table (Conversation Persistence)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_messages (
        id TEXT PRIMARY KEY,
        sender TEXT NOT NULL,
        text TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        engine_used TEXT DEFAULT '',
        suggested_actions TEXT DEFAULT '[]',
        created_at TEXT NOT NULL
    )
    """)

    # Reminders table (Real-time scheduling mechanism)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        id TEXT PRIMARY KEY,
        task_id TEXT,
        title TEXT NOT NULL,
        remind_at TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        channel TEXT NOT NULL DEFAULT 'in_app',
        created_at TEXT NOT NULL,
        sent_at TEXT,
        FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL
    )
    """)

    # User Documents table (Document upload & summarization storage)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_documents (
        id TEXT PRIMARY KEY,
        filename TEXT NOT NULL,
        content TEXT NOT NULL,
        summary TEXT DEFAULT '',
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()

    # Migration / Cleanup: Remove 'Alex Morgan' references completely from existing DB
    cursor.execute("""
    UPDATE user_settings 
    SET user_name = 'User' 
    WHERE user_name = 'Alex Morgan' OR user_name LIKE '%Alex%'
    """)

    # Ensure default user settings row exists
    cursor.execute("SELECT COUNT(*) FROM user_settings WHERE id = 1")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO user_settings (
            id, user_name, work_start_time, work_end_time, buffer_minutes,
            pomodoro_work_duration, pomodoro_break_duration, pomodoro_long_break_duration,
            theme, notifications_enabled, ai_provider, gemini_api_key, timezone
        )
        VALUES (1, 'User', '09:00', '18:00', 15, 25, 5, 15, 'light', 1, 'auto', '', 'auto')
        """)

    conn.commit()
    conn.close()

# ================= Chat Message Persistence =================

def get_chat_history(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, sender, text, timestamp, engine_used, suggested_actions, created_at
    FROM chat_messages
    ORDER BY created_at ASC
    LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()

    history = []
    for r in rows:
        actions = []
        try:
            if r["suggested_actions"]:
                actions = json.loads(r["suggested_actions"])
        except Exception:
            actions = []
        history.append({
            "id": r["id"],
            "sender": r["sender"],
            "text": r["text"],
            "timestamp": r["timestamp"],
            "engine_used": r["engine_used"],
            "suggested_actions": actions,
            "created_at": r["created_at"]
        })
    return history

def add_chat_message(
    msg_id: str,
    sender: str,
    text: str,
    timestamp: str,
    engine_used: str = "",
    suggested_actions: list = None
):
    conn = get_connection()
    cursor = conn.cursor()
    actions_json = json.dumps(suggested_actions or [])
    now_iso = datetime.now().isoformat()
    cursor.execute("""
    INSERT INTO chat_messages (id, sender, text, timestamp, engine_used, suggested_actions, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (msg_id, sender, text, timestamp, engine_used, actions_json, now_iso))
    conn.commit()
    conn.close()

def clear_chat_history():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_messages")
    conn.commit()
    conn.close()

# ================= Reminders Persistence =================

def create_reminder_record(
    title: str,
    remind_at: str,
    task_id: Optional[str] = None,
    channel: str = "in_app"
) -> Dict[str, Any]:
    rem_id = f"rem-{uuid.uuid4().hex[:8]}"
    now_iso = datetime.now().isoformat()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO reminders (id, task_id, title, remind_at, status, channel, created_at, sent_at)
    VALUES (?, ?, ?, ?, 'pending', ?, ?, NULL)
    """, (rem_id, task_id, title.strip(), remind_at, channel, now_iso))
    conn.commit()

    cursor.execute("SELECT * FROM reminders WHERE id = ?", (rem_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row)

def get_reminders_list(status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if status and status.lower() != "all":
        cursor.execute("""
        SELECT * FROM reminders 
        WHERE status = ? 
        ORDER BY remind_at ASC 
        LIMIT ?
        """, (status, limit))
    else:
        cursor.execute("""
        SELECT * FROM reminders 
        ORDER BY remind_at ASC 
        LIMIT ?
        """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_due_reminders(now_iso: Optional[str] = None) -> List[Dict[str, Any]]:
    current_time = now_iso or datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM reminders 
    WHERE status = 'pending' AND remind_at <= ?
    ORDER BY remind_at ASC
    """, (current_time,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_reminder_status(reminder_id: str, status: str, sent_at: Optional[str] = None) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE reminders 
    SET status = ?, sent_at = COALESCE(?, sent_at) 
    WHERE id = ?
    """, (status, sent_at, reminder_id))
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated

def delete_reminder_record(reminder_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# ================= Documents Persistence =================

def save_user_document(filename: str, content: str, summary: str = "") -> Dict[str, Any]:
    doc_id = f"doc-{uuid.uuid4().hex[:8]}"
    now_iso = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO user_documents (id, filename, content, summary, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (doc_id, filename, content, summary, now_iso))
    conn.commit()
    cursor.execute("SELECT * FROM user_documents WHERE id = ?", (doc_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row)

def get_user_documents(limit: int = 10) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename, summary, created_at, LENGTH(content) as content_length FROM user_documents ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ================= Global Reset / Clear =================

def clear_all_data():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM habit_logs")
    cursor.execute("DELETE FROM habits")
    cursor.execute("DELETE FROM tasks")
    cursor.execute("DELETE FROM focus_sessions")
    cursor.execute("DELETE FROM chat_messages")
    cursor.execute("DELETE FROM reminders")
    cursor.execute("DELETE FROM user_documents")
    conn.commit()
    conn.close()
