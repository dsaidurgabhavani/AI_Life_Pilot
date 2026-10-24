import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter
from database import get_connection
from models import FocusSessionCreate, FocusSessionResponse

router = APIRouter(prefix="/api/focus", tags=["Smart Study and Work Mode"])

@router.get("/sessions", response_model=List[FocusSessionResponse])
def get_focus_sessions(limit: int = 20):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM focus_sessions 
    ORDER BY completed_at DESC 
    LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()

    return [FocusSessionResponse(**dict(r)) for r in rows]

@router.post("/sessions", response_model=FocusSessionResponse)
def record_focus_session(session_in: FocusSessionCreate):
    conn = get_connection()
    cursor = conn.cursor()

    session_id = f"fs-{uuid.uuid4().hex[:8]}"
    now_iso = datetime.now().isoformat()

    cursor.execute("""
    INSERT INTO focus_sessions (id, task_id, task_title, mode, duration_minutes, completed_at, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        session_in.task_id,
        session_in.task_title,
        session_in.mode,
        session_in.duration_minutes,
        now_iso,
        session_in.notes or ""
    ))

    # If linked to a task, update status to in_progress if it was pending
    if session_in.task_id:
        cursor.execute("SELECT status FROM tasks WHERE id = ?", (session_in.task_id,))
        task_row = cursor.fetchone()
        if task_row and task_row["status"] == "pending":
            cursor.execute("UPDATE tasks SET status = 'in_progress' WHERE id = ?", (session_in.task_id,))

    conn.commit()

    cursor.execute("SELECT * FROM focus_sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()

    return FocusSessionResponse(**dict(row))

@router.get("/stats")
def get_focus_stats():
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now()
    today_start = now.strftime("%Y-%m-%d 00:00:00")
    week_start = (now - timedelta(days=7)).strftime("%Y-%m-%d 00:00:00")

    # Today focus
    cursor.execute("""
    SELECT COALESCE(SUM(duration_minutes), 0) FROM focus_sessions 
    WHERE completed_at >= ?
    """, (today_start,))
    today_minutes = cursor.fetchone()[0]

    # Week focus
    cursor.execute("""
    SELECT COALESCE(SUM(duration_minutes), 0) FROM focus_sessions 
    WHERE completed_at >= ?
    """, (week_start,))
    week_minutes = cursor.fetchone()[0]

    # Study vs Work breakdown
    cursor.execute("""
    SELECT mode, COALESCE(SUM(duration_minutes), 0) FROM focus_sessions
    GROUP BY mode
    """)
    mode_rows = cursor.fetchall()
    mode_dict = {r[0]: r[1] for r in mode_rows}

    # Total completed sessions count
    cursor.execute("SELECT COUNT(*) FROM focus_sessions")
    total_sessions_count = cursor.fetchone()[0]

    conn.close()

    return {
        "today_minutes": today_minutes,
        "week_minutes": week_minutes,
        "study_minutes": mode_dict.get("study", 0),
        "work_minutes": mode_dict.get("work", 0),
        "total_sessions": total_sessions_count
    }
