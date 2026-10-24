import sqlite3
import os
import json
import uuid
from datetime import datetime, timedelta

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
        theme TEXT DEFAULT 'system',
        notifications_enabled INTEGER DEFAULT 1,
        ai_provider TEXT DEFAULT 'auto',
        gemini_api_key TEXT DEFAULT ''
    )
    """)

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

    conn.commit()

    # Migration / Cleanup: Remove 'Alex Morgan' references from existing DB
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
            theme, notifications_enabled, ai_provider, gemini_api_key
        )
        VALUES (1, 'User', '09:00', '18:00', 15, 25, 5, 15, 'light', 1, 'auto', '')
        """)

    conn.commit()
    conn.close()

# Chat message persistence helpers
def get_chat_history(limit: int = 50):
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

def clear_all_data():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM habit_logs")
    cursor.execute("DELETE FROM habits")
    cursor.execute("DELETE FROM tasks")
    cursor.execute("DELETE FROM focus_sessions")
    cursor.execute("DELETE FROM chat_messages")
    conn.commit()
    conn.close()
