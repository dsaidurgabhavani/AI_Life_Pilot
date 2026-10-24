import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
from fastapi import APIRouter
from database import get_connection
from models import (
    ChatMessageRequest,
    ChatMessageResponse,
    GoalBreakdownRequest,
    GoalBreakdownResponse,
    SubtaskItem
)
from ai_service import chat_with_assistant, breakdown_goal
from routers.tasks import enrich_task_dict

router = APIRouter(prefix="/api/assistant", tags=["Intelligent AI Assistant"])

@router.post("/chat", response_model=ChatMessageResponse)
def handle_chat(req: ChatMessageRequest):
    conn = get_connection()
    cursor = conn.cursor()

    # Gather user context to ground the assistant
    cursor.execute("SELECT * FROM tasks WHERE status != 'completed'")
    task_rows = cursor.fetchall()
    pending_tasks = [enrich_task_dict(dict(r)) for r in task_rows]
    overdue_count = sum(1 for t in pending_tasks if t["is_overdue"])

    # Focus time today
    today_start = datetime.now().strftime("%Y-%m-%d 00:00:00")
    cursor.execute("""
    SELECT COALESCE(SUM(duration_minutes), 0) FROM focus_sessions 
    WHERE completed_at >= ?
    """, (today_start,))
    focus_today = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM user_settings WHERE id = 1")
    settings_row = cursor.fetchone()
    settings = dict(settings_row) if settings_row else {}
    conn.close()

    context = {
        "tasks": pending_tasks,
        "overdue_count": overdue_count,
        "pending_count": len(pending_tasks),
        "focus_today_minutes": focus_today,
        "user_name": settings.get("user_name", "Alex")
    }

    result = chat_with_assistant(
        message=req.message,
        conversation_history=req.conversation_history or [],
        context=context,
        gemini_key=settings.get("gemini_api_key", "")
    )

    return ChatMessageResponse(**result)

@router.post("/breakdown", response_model=GoalBreakdownResponse)
def handle_goal_breakdown(req: GoalBreakdownRequest):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT gemini_api_key FROM user_settings WHERE id = 1")
    row = cursor.fetchone()
    gemini_key = row["gemini_api_key"] if row else ""
    conn.close()

    result = breakdown_goal(
        goal_title=req.goal_title,
        target_deadline=req.target_deadline,
        category=req.category or "Study",
        gemini_key=gemini_key
    )

    return GoalBreakdownResponse(**result)

@router.post("/import-subtasks")
def import_subtasks_to_tasks(payload: Dict[str, Any]):
    subtasks = payload.get("subtasks", [])
    if not subtasks:
        return {"imported_count": 0, "message": "No subtasks provided"}

    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now()
    cursor.execute("SELECT COALESCE(MAX(order_index), 0) FROM tasks")
    current_max_order = cursor.fetchone()[0]

    imported_ids = []
    for idx, item in enumerate(subtasks):
        t_id = f"task-{uuid.uuid4().hex[:8]}"
        day_offset = item.get("suggested_day_offset", 0)
        target_deadline = (now + timedelta(days=day_offset, hours=4)).strftime("%Y-%m-%dT18:00")

        cursor.execute("""
        INSERT INTO tasks (id, title, description, category, priority, status, estimated_duration, deadline, created_at, order_index)
        VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)
        """, (
            t_id,
            item["title"],
            item.get("description", ""),
            item.get("category", "Study"),
            item.get("priority", "urgent_important"),
            item.get("estimated_duration", 30),
            target_deadline,
            now.isoformat(),
            current_max_order + idx + 1
        ))
        imported_ids.append(t_id)

    conn.commit()
    conn.close()

    return {
        "imported_count": len(imported_ids),
        "imported_ids": imported_ids,
        "message": f"Successfully created {len(imported_ids)} actionable tasks!"
    }
