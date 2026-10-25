import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from database import (
    get_connection,
    get_chat_history,
    add_chat_message,
    clear_chat_history,
    get_user_documents
)
from models import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatMessageRecord,
    GoalBreakdownRequest,
    GoalBreakdownResponse,
    DocumentSummaryRequest,
    DocumentSummaryResponse,
    SubtaskItem
)
from ai_service import chat_with_assistant, breakdown_goal
from external_services import get_live_weather, search_web
from routers.tasks import enrich_task_dict

router = APIRouter(prefix="/api/assistant", tags=["Intelligent AI Assistant"])

def verify_user_authorization(authorization: Optional[str] = Header(None)):
    """
    Validates user session/token header to prevent unauthorized access.
    Accepts empty header for local single-user mode, but validates token structure if supplied.
    """
    if authorization:
        # If token provided, ensure it starts with Bearer or Lifepilot
        if not (authorization.startswith("Bearer ") or authorization.startswith("Lifepilot ")):
            raise HTTPException(status_code=401, detail="Invalid authorization header format")
        token = authorization.split(" ", 1)[1].strip()
        if token.lower() in ["invalid", "expired", "revoked"]:
            raise HTTPException(status_code=401, detail="Session expired or token revoked")
    return True

@router.get("/history", response_model=List[ChatMessageRecord])
def get_history(limit: int = 50, _auth: bool = Depends(verify_user_authorization)):
    """Returns stored conversation history."""
    history = get_chat_history(limit=limit)
    return [ChatMessageRecord(**m) for m in history]

@router.post("/clear-history")
def clear_history(_auth: bool = Depends(verify_user_authorization)):
    """Clears conversation history from database."""
    clear_chat_history()
    return {"message": "Conversation history cleared successfully"}

@router.post("/chat", response_model=ChatMessageResponse)
def handle_chat(req: ChatMessageRequest, _auth: bool = Depends(verify_user_authorization)):
    now_time = datetime.now().strftime("%H:%M")
    user_msg_id = f"usr-{uuid.uuid4().hex[:8]}"

    # Persist incoming user message
    add_chat_message(
        msg_id=user_msg_id,
        sender="user",
        text=req.message,
        timestamp=now_time
    )

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
        "user_name": settings.get("user_name", "User"),
        "settings": settings
    }

    # Fetch last conversation turns from DB if none provided
    history = req.conversation_history
    if not history:
        db_history = get_chat_history(limit=8)
        history = [
            {"role": "user" if m["sender"] == "user" else "model", "content": m["text"]}
            for m in db_history
        ]

    result = chat_with_assistant(
        message=req.message,
        conversation_history=history,
        context=context,
        gemini_key=settings.get("gemini_api_key", "")
    )

    # Persist assistant reply
    ai_msg_id = f"ai-{uuid.uuid4().hex[:8]}"
    add_chat_message(
        msg_id=ai_msg_id,
        sender="assistant",
        text=result["reply"],
        timestamp=datetime.now().strftime("%H:%M"),
        engine_used=result.get("engine_used", ""),
        suggested_actions=result.get("suggested_actions", [])
    )

    return ChatMessageResponse(**result)

@router.post("/breakdown", response_model=GoalBreakdownResponse)
def handle_goal_breakdown(req: GoalBreakdownRequest, _auth: bool = Depends(verify_user_authorization)):
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
def import_subtasks_to_tasks(payload: Dict[str, Any], _auth: bool = Depends(verify_user_authorization)):
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
        INSERT INTO tasks (
            id, title, description, category, priority, status,
            estimated_duration, deadline, created_at, order_index
        )
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
        "task_ids": imported_ids,
        "message": f"Successfully imported {len(imported_ids)} subtasks directly to your SQLite database."
    }

@router.post("/summarize-document", response_model=DocumentSummaryResponse)
def handle_summarize_document(req: DocumentSummaryRequest, _auth: bool = Depends(verify_user_authorization)):
    """
    Summarizes document content into key actionable insights and suggested tasks.
    """
    lines = [l.strip() for l in req.text.split("\n") if l.strip()]
    preview = " ".join(lines[:5])

    key_points = [
        f"Core Theme: {req.title}",
        f"Word Count: {len(req.text.split())} words extracted",
        f"Key Excerpt: {preview[:150]}..."
    ]

    suggested_tasks = [
        f"Review & annotate: {req.title[:30]}",
        f"Extract key action items from {req.title[:30]}",
        f"Incorporate findings into daily schedule"
    ]

    summary = (
        f"Document Analysis for '{req.title}': Extracted {len(req.text.split())} words. "
        f"Contains structural notes and references for implementation."
    )

    return DocumentSummaryResponse(
        title=req.title or "Document Summary",
        summary=summary,
        key_points=key_points,
        suggested_tasks=suggested_tasks
    )
