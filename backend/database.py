import sqlite3
import os
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
        user_name TEXT DEFAULT 'Alex Morgan',
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

    conn.commit()
    conn.close()

    # If database is freshly initialized or empty, seed demo data
    check_and_seed_defaults()

def check_and_seed_defaults():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM user_settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO user_settings (id, user_name, work_start_time, work_end_time, buffer_minutes, pomodoro_work_duration, pomodoro_break_duration, pomodoro_long_break_duration, theme, notifications_enabled, ai_provider, gemini_api_key)
        VALUES (1, 'Alex Morgan', '09:00', '18:00', 15, 25, 5, 15, 'light', 1, 'auto', '')
        """)
        conn.commit()

    cursor.execute("SELECT COUNT(*) FROM tasks")
    if cursor.fetchone()[0] == 0:
        seed_demo_data(conn)
    conn.close()

def seed_demo_data(conn=None):
    close_when_done = False
    if conn is None:
        conn = get_connection()
        close_when_done = True

    cursor = conn.cursor()

    # Clear existing
    cursor.execute("DELETE FROM habit_logs")
    cursor.execute("DELETE FROM habits")
    cursor.execute("DELETE FROM tasks")
    cursor.execute("DELETE FROM focus_sessions")

    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    # Sample tasks
    demo_tasks = [
        # Overdue task to highlight deadline manager
        {
            "id": "t-1",
            "title": "Submit Research Project Abstract",
            "description": "Finalize literature review abstract and submit to course portal with supervisor sign-off.",
            "category": "Study",
            "priority": "urgent_important",
            "status": "pending",
            "estimated_duration": 45,
            "deadline": (now - timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M"),
            "scheduled_start": "09:00",
            "scheduled_end": "09:45",
            "created_at": (now - timedelta(days=2)).isoformat(),
            "completed_at": None,
            "order_index": 1
        },
        # Due Today Urgent & Important
        {
            "id": "t-2",
            "title": "Prepare Client Demo & Presentation Slides",
            "description": "Outline key architecture pillars, AI features, and prepare interactive demo workflow.",
            "category": "Work",
            "priority": "urgent_important",
            "status": "in_progress",
            "estimated_duration": 60,
            "deadline": (now + timedelta(hours=4)).strftime("%Y-%m-%dT%H:%M"),
            "scheduled_start": "10:00",
            "scheduled_end": "11:00",
            "created_at": (now - timedelta(days=1)).isoformat(),
            "completed_at": None,
            "order_index": 2
        },
        # Due Today Important Not Urgent
        {
            "id": "t-3",
            "title": "Review Distributed Systems Chapter 4",
            "description": "Study Paxos and Raft consensus algorithms and write summary notes for upcoming exam.",
            "category": "Study",
            "priority": "important_not_urgent",
            "status": "pending",
            "estimated_duration": 50,
            "deadline": (now + timedelta(hours=8)).strftime("%Y-%m-%dT%H:%M"),
            "scheduled_start": "11:15",
            "scheduled_end": "12:05",
            "created_at": (now - timedelta(days=1)).isoformat(),
            "completed_at": None,
            "order_index": 3
        },
        # Completed Today
        {
            "id": "t-4",
            "title": "Morning Team Standup & Sprint Sync",
            "description": "Share progress on AI LifePilot sprint and blocker resolutions.",
            "category": "Work",
            "priority": "urgent_not_important",
            "status": "completed",
            "estimated_duration": 30,
            "deadline": (now - timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M"),
            "scheduled_start": "08:30",
            "scheduled_end": "09:00",
            "created_at": (now - timedelta(days=1)).isoformat(),
            "completed_at": (now - timedelta(hours=4)).isoformat(),
            "order_index": 0
        },
        # Personal / Health Task
        {
            "id": "t-5",
            "title": "Post-Work 5K Jog & Stretching",
            "description": "Cardio session to recharge focus and maintain physical wellness.",
            "category": "Health",
            "priority": "important_not_urgent",
            "status": "pending",
            "estimated_duration": 40,
            "deadline": (now + timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M"),
            "scheduled_start": "17:30",
            "scheduled_end": "18:10",
            "created_at": (now - timedelta(days=1)).isoformat(),
            "completed_at": None,
            "order_index": 4
        },
        # Tomorrow Due Task
        {
            "id": "t-6",
            "title": "Draft Technical Architecture Documentation",
            "description": "Document database schemas, REST APIs, and Gemini AI fallback mechanisms.",
            "category": "Work",
            "priority": "important_not_urgent",
            "status": "pending",
            "estimated_duration": 90,
            "deadline": (now + timedelta(days=1, hours=2)).strftime("%Y-%m-%dT%H:%M"),
            "scheduled_start": None,
            "scheduled_end": None,
            "created_at": now.isoformat(),
            "completed_at": None,
            "order_index": 5
        },
        # Personal Task
        {
            "id": "t-7",
            "title": "Review Monthly Budget & Subscriptions",
            "description": "Check cloud hosting costs, gym membership, and grocery allocations.",
            "category": "Finance",
            "priority": "neither",
            "status": "pending",
            "estimated_duration": 25,
            "deadline": (now + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M"),
            "scheduled_start": None,
            "scheduled_end": None,
            "created_at": now.isoformat(),
            "completed_at": None,
            "order_index": 6
        }
    ]

    for t in demo_tasks:
        cursor.execute("""
        INSERT INTO tasks (id, title, description, category, priority, status, estimated_duration, deadline, scheduled_start, scheduled_end, created_at, completed_at, order_index)
        VALUES (:id, :title, :description, :category, :priority, :status, :estimated_duration, :deadline, :scheduled_start, :scheduled_end, :created_at, :completed_at, :order_index)
        """, t)

    # Sample Habits
    demo_habits = [
        {
            "id": "h-1",
            "title": "Read 20 Pages Non-Fiction",
            "description": "Deep reading in productivity, psychology, or software engineering.",
            "category": "Personal",
            "frequency": "daily",
            "target_days_per_week": 7,
            "icon": "book-open",
            "color": "#3b82f6"
        },
        {
            "id": "h-2",
            "title": "Morning Exercise & Stretching",
            "description": "At least 20 minutes of cardio or bodyweight workout.",
            "category": "Health",
            "frequency": "daily",
            "target_days_per_week": 6,
            "icon": "activity",
            "color": "#10b981"
        },
        {
            "id": "h-3",
            "title": "LeetCode / Algorithm Practice",
            "description": "Solve 1 medium problem or review data structures.",
            "category": "Study",
            "frequency": "daily",
            "target_days_per_week": 5,
            "icon": "code",
            "color": "#8b5cf6"
        },
        {
            "id": "h-4",
            "title": "Evening Daily Review & Planning",
            "description": "Review completed tasks, log accomplishments, and preview tomorrow.",
            "category": "Work",
            "frequency": "daily",
            "target_days_per_week": 7,
            "icon": "check-circle",
            "color": "#f59e0b"
        }
    ]

    for h in demo_habits:
        cursor.execute("""
        INSERT INTO habits (id, title, description, category, frequency, target_days_per_week, icon, color, created_at)
        VALUES (:id, :title, :description, :category, :frequency, :target_days_per_week, :icon, :color, :created_at)
        """, {**h, "created_at": (now - timedelta(days=14)).isoformat()})

    # Sample Habit Logs for the past 7 days to give active streaks!
    # Days: 6 days ago up to today
    log_matrix = {
        "h-1": [True, True, True, True, True, True, True],   # 7 day streak!
        "h-2": [True, False, True, True, True, True, True],  # 5 day streak
        "h-3": [False, True, True, True, True, False, True], # 1 day streak (today done)
        "h-4": [True, True, True, True, True, True, False]   # 6 day streak (today pending)
    }

    for habit_id, completions in log_matrix.items():
        for i, completed in enumerate(completions):
            if completed:
                log_day = (now - timedelta(days=(6 - i))).strftime("%Y-%m-%d")
                cursor.execute("""
                INSERT OR REPLACE INTO habit_logs (id, habit_id, log_date, completed)
                VALUES (?, ?, ?, 1)
                """, (f"hl-{habit_id}-{log_day}", habit_id, log_day))

    # Sample Focus Sessions
    demo_sessions = [
        {
            "id": f"fs-{uuid.uuid4().hex[:8]}",
            "task_id": "t-4",
            "task_title": "Morning Team Standup & Sprint Sync",
            "mode": "work",
            "duration_minutes": 25,
            "completed_at": (now - timedelta(hours=4)).isoformat(),
            "notes": "Discussed blockers and prioritized demo presentation."
        },
        {
            "id": f"fs-{uuid.uuid4().hex[:8]}",
            "task_id": "t-2",
            "task_title": "Prepare Client Demo & Presentation Slides",
            "mode": "work",
            "duration_minutes": 45,
            "completed_at": (now - timedelta(hours=2)).isoformat(),
            "notes": "Finished slide deck drafts and rehearsed demo storyline."
        },
        {
            "id": f"fs-{uuid.uuid4().hex[:8]}",
            "task_id": "t-3",
            "task_title": "Review Distributed Systems Chapter 4",
            "mode": "study",
            "duration_minutes": 50,
            "completed_at": (now - timedelta(days=1, hours=3)).isoformat(),
            "notes": "Focused reading on consensus protocols and quorum slicing."
        }
    ]

    for s in demo_sessions:
        cursor.execute("""
        INSERT INTO focus_sessions (id, task_id, task_title, mode, duration_minutes, completed_at, notes)
        VALUES (:id, :task_id, :task_title, :mode, :duration_minutes, :completed_at, :notes)
        """, s)

    conn.commit()
    if close_when_done:
        conn.close()

def clear_all_data():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM habit_logs")
    cursor.execute("DELETE FROM habits")
    cursor.execute("DELETE FROM tasks")
    cursor.execute("DELETE FROM focus_sessions")
    conn.commit()
    conn.close()
