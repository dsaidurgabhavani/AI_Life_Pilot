from datetime import datetime
from typing import Optional
from fastapi import APIRouter
from database import get_connection
from models import DailyScheduleResponse, ScheduleReorderRequest
from ai_service import generate_daily_schedule
from routers.tasks import enrich_task_dict

router = APIRouter(prefix="/api/planner", tags=["AI Daily Planner"])

@router.get("/today", response_model=DailyScheduleResponse)
def get_today_schedule(date: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()

    target_date = date or datetime.now().strftime("%Y-%m-%d")

    cursor.execute("SELECT * FROM tasks")
    task_rows = cursor.fetchall()
    tasks = [enrich_task_dict(dict(r)) for r in task_rows]

    cursor.execute("SELECT * FROM user_settings WHERE id = 1")
    settings_row = cursor.fetchone()
    settings = dict(settings_row) if settings_row else {}
    conn.close()

    schedule = generate_daily_schedule(
        tasks=tasks,
        settings=settings,
        target_date_str=target_date,
        gemini_key=settings.get("gemini_api_key", "")
    )
    return schedule

@router.post("/generate", response_model=DailyScheduleResponse)
def regenerate_schedule(date: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()

    target_date = date or datetime.now().strftime("%Y-%m-%d")

    cursor.execute("SELECT * FROM tasks")
    task_rows = cursor.fetchall()
    tasks = [enrich_task_dict(dict(r)) for r in task_rows]

    cursor.execute("SELECT * FROM user_settings WHERE id = 1")
    settings_row = cursor.fetchone()
    settings = dict(settings_row) if settings_row else {}

    schedule = generate_daily_schedule(
        tasks=tasks,
        settings=settings,
        target_date_str=target_date,
        gemini_key=settings.get("gemini_api_key", "")
    )

    # Persist the newly generated start and end times to the tasks table for linked tasks
    for slot in schedule["slots"]:
        if slot.get("task_id"):
            cursor.execute("""
            UPDATE tasks
            SET scheduled_start = ?, scheduled_end = ?
            WHERE id = ?
            """, (slot["start_time"], slot["end_time"], slot["task_id"]))

    conn.commit()
    conn.close()

    return schedule

@router.post("/reorder")
def reorder_schedule(reorder_req: ScheduleReorderRequest):
    conn = get_connection()
    cursor = conn.cursor()

    for idx, slot in enumerate(reorder_req.slots):
        cursor.execute("""
        UPDATE tasks
        SET scheduled_start = ?, scheduled_end = ?, order_index = ?
        WHERE id = ?
        """, (slot.scheduled_start, slot.scheduled_end, idx + 1, slot.task_id))

    conn.commit()
    conn.close()

    return {"message": "Schedule slots successfully updated"}
