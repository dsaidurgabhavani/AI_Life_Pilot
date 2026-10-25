from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from database import (
    create_reminder_record,
    get_reminders_list,
    mark_reminder_status,
    delete_reminder_record,
    get_due_reminders
)
from models import ReminderCreate, ReminderUpdate, ReminderResponse
from scheduler import pop_due_alerts, peek_due_alerts

router = APIRouter(prefix="/api/reminders", tags=["Real-Time Reminders"])

@router.get("", response_model=List[ReminderResponse])
def list_reminders(
    status: Optional[str] = Query(None, description="pending, sent, failed, cancelled, or all"),
    limit: int = Query(50, ge=1, le=100)
):
    reminders = get_reminders_list(status=status, limit=limit)
    return [ReminderResponse(**r) for r in reminders]

@router.post("", response_model=ReminderResponse)
def create_reminder(payload: ReminderCreate):
    created = create_reminder_record(
        title=payload.title,
        remind_at=payload.remind_at,
        task_id=payload.task_id,
        channel=payload.channel
    )
    return ReminderResponse(**created)

@router.patch("/{id}", response_model=ReminderResponse)
def update_reminder(id: str, payload: ReminderUpdate):
    if payload.status:
        mark_reminder_status(id, payload.status)
    reminders = get_reminders_list(limit=200)
    matched = next((r for r in reminders if r["id"] == id), None)
    if not matched:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return ReminderResponse(**matched)

@router.delete("/{id}")
def delete_reminder(id: str):
    success = delete_reminder_record(id)
    if not success:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"message": "Reminder deleted successfully", "id": id}

@router.get("/due")
def get_live_due_alerts():
    """
    Returns alerts that are currently due according to the background scheduler.
    Pops them so connected clients receive each alert once without duplicate notifications.
    """
    alerts = pop_due_alerts()
    return {"due_count": len(alerts), "alerts": alerts}
