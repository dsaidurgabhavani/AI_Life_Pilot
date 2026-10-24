import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from database import get_connection
from models import TaskCreate, TaskUpdate, TaskResponse

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

def format_time_remaining(deadline_dt: datetime, now: datetime) -> str:
    diff = deadline_dt - now
    total_seconds = int(diff.total_seconds())

    if total_seconds < 0:
        past_seconds = abs(total_seconds)
        if past_seconds < 3600:
            return f"Overdue by {past_seconds // 60}m"
        elif past_seconds < 86400:
            return f"Overdue by {past_seconds // 3600}h"
        else:
            return f"Overdue by {past_seconds // 86400}d"
    
    if total_seconds < 3600:
        return f"{total_seconds // 60}m remaining"
    elif total_seconds < 86400:
        hours = total_seconds // 3600
        mins = (total_seconds % 3600) // 60
        return f"{hours}h {mins}m remaining"
    else:
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        return f"{days}d {hours}h remaining"

def enrich_task_dict(row: dict) -> dict:
    t = dict(row)
    now = datetime.now()
    deadline_str = t.get("deadline", "")
    is_overdue = False
    time_remaining_formatted = "No deadline"
    urgency_level = "normal"

    if deadline_str:
        try:
            clean_str = deadline_str[:16]
            dl = datetime.fromisoformat(clean_str)
            time_remaining_formatted = format_time_remaining(dl, now)
            diff_hours = (dl - now).total_seconds() / 3600.0

            if t.get("status") != "completed":
                if diff_hours < 0:
                    is_overdue = True
                    urgency_level = "overdue"
                elif diff_hours <= 4:
                    urgency_level = "urgent"
                elif diff_hours <= 24:
                    urgency_level = "today"
                else:
                    urgency_level = "upcoming"
            else:
                urgency_level = "completed"
        except Exception:
            pass

    t["is_overdue"] = is_overdue
    t["time_remaining_formatted"] = time_remaining_formatted
    t["urgency_level"] = urgency_level
    return t

@router.get("", response_model=List[TaskResponse])
def get_tasks(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("deadline") # deadline, priority, duration, created_at
):
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM tasks WHERE 1=1"
    params = []

    if search:
        query += " AND (title LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    if category and category.lower() != "all":
        query += " AND category = ?"
        params.append(category)
    if priority and priority.lower() != "all":
        query += " AND priority = ?"
        params.append(priority)
    if status and status.lower() != "all":
        query += " AND status = ?"
        params.append(status)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    tasks = [enrich_task_dict(dict(row)) for row in rows]

    # Sorting
    if sort_by == "priority":
        priority_order = {"urgent_important": 0, "urgent_not_important": 1, "important_not_urgent": 2, "neither": 3}
        tasks.sort(key=lambda x: priority_order.get(x["priority"], 4))
    elif sort_by == "duration":
        tasks.sort(key=lambda x: x["estimated_duration"])
    elif sort_by == "created_at":
        tasks.sort(key=lambda x: x["created_at"], reverse=True)
    else: # default deadline
        tasks.sort(key=lambda x: (x["status"] == "completed", x["deadline"]))

    return tasks

@router.post("", response_model=TaskResponse)
def create_task(task_in: TaskCreate):
    conn = get_connection()
    cursor = conn.cursor()

    task_id = f"task-{uuid.uuid4().hex[:8]}"
    now_iso = datetime.now().isoformat()

    cursor.execute("SELECT COALESCE(MAX(order_index), 0) + 1 FROM tasks")
    next_order = cursor.fetchone()[0]

    cursor.execute("""
    INSERT INTO tasks (id, title, description, category, priority, status, estimated_duration, deadline, scheduled_start, scheduled_end, created_at, completed_at, order_index)
    VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?, NULL, ?)
    """, (
        task_id,
        task_in.title,
        task_in.description or "",
        task_in.category,
        task_in.priority,
        task_in.estimated_duration,
        task_in.deadline,
        task_in.scheduled_start,
        task_in.scheduled_end,
        now_iso,
        next_order
    ))

    conn.commit()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()

    return enrich_task_dict(dict(row))

@router.get("/recommendation/next", response_model=Optional[TaskResponse])
def get_next_recommended_task():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE status != 'completed'")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return None

    tasks = [enrich_task_dict(dict(row)) for row in rows]
    # Priority sorting: Overdue first, then urgent_important, then due soonest
    def rank_score(t):
        score = 0
        if t["is_overdue"]:
            score += 1000
        if t["priority"] == "urgent_important":
            score += 500
        elif t["priority"] == "important_not_urgent":
            score += 300
        elif t["priority"] == "urgent_not_important":
            score += 200
        
        if t["urgency_level"] == "urgent":
            score += 250
        elif t["urgency_level"] == "today":
            score += 100
        return score

    tasks.sort(key=rank_score, reverse=True)
    return tasks[0]

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    return enrich_task_dict(dict(row))

@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, updates: TaskUpdate):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = updates.model_dump(exclude_unset=True)
    if not update_data:
        conn.close()
        return enrich_task_dict(dict(existing))

    fields = []
    values = []
    for k, v in update_data.items():
        fields.append(f"{k} = ?")
        values.append(v)

    # If status is being updated to completed, record completed_at
    if "status" in update_data:
        if update_data["status"] == "completed":
            fields.append("completed_at = ?")
            values.append(datetime.now().isoformat())
        else:
            fields.append("completed_at = ?")
            values.append(None)

    values.append(task_id)
    sql = f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?"
    cursor.execute(sql, values)
    conn.commit()

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    updated_row = cursor.fetchone()
    conn.close()

    return enrich_task_dict(dict(updated_row))

@router.post("/{task_id}/toggle", response_model=TaskResponse)
def toggle_task(task_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")

    new_status = "completed" if row["status"] != "completed" else "pending"
    completed_at = datetime.now().isoformat() if new_status == "completed" else None

    cursor.execute("""
    UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?
    """, (new_status, completed_at, task_id))
    conn.commit()

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    updated_row = cursor.fetchone()
    conn.close()

    return enrich_task_dict(dict(updated_row))

@router.delete("/{task_id}")
def delete_task(task_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return {"message": "Task deleted successfully", "id": task_id}
