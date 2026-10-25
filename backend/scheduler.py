import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any
from database import get_due_reminders, mark_reminder_status

logger = logging.getLogger("lifepilot.scheduler")

# In-memory queue of recent fired alerts waiting for frontend delivery
_active_due_alerts: List[Dict[str, Any]] = []
_scheduler_running = False
_scheduler_task: asyncio.Task = None

async def process_due_reminders():
    """
    Checks for pending reminders whose remind_at <= current time,
    marks them as sent in the SQLite database, and queues them for delivery.
    """
    global _active_due_alerts
    try:
        now_iso = datetime.now().isoformat()
        due_items = get_due_reminders(now_iso)

        for item in due_items:
            rem_id = item["id"]
            sent_at = datetime.now().isoformat()
            success = mark_reminder_status(rem_id, status="sent", sent_at=sent_at)
            if success:
                alert_payload = {
                    "id": rem_id,
                    "title": item["title"],
                    "remind_at": item["remind_at"],
                    "channel": item.get("channel", "in_app"),
                    "task_id": item.get("task_id"),
                    "fired_at": sent_at
                }
                # Add to queue without duplicates
                if not any(a["id"] == rem_id for a in _active_due_alerts):
                    _active_due_alerts.append(alert_payload)
                logger.info(f"Fired scheduled reminder: {item['title']} (ID: {rem_id})")

        # Keep active queue from growing indefinitely
        if len(_active_due_alerts) > 50:
            _active_due_alerts = _active_due_alerts[-50:]

    except Exception as e:
        logger.error(f"Error checking due reminders: {e}")

async def _scheduler_loop():
    global _scheduler_running
    logger.info("LifePilot reminder background scheduler started.")
    while _scheduler_running:
        await process_due_reminders()
        await asyncio.sleep(5) # check every 5 seconds

def start_scheduler():
    global _scheduler_running, _scheduler_task
    if not _scheduler_running:
        _scheduler_running = True
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                _scheduler_task = asyncio.create_task(_scheduler_loop())
        except RuntimeError:
            pass

def stop_scheduler():
    global _scheduler_running, _scheduler_task
    _scheduler_running = False
    if _scheduler_task:
        _scheduler_task.cancel()

def pop_due_alerts() -> List[Dict[str, Any]]:
    """Returns and clears all currently due alerts for connected clients."""
    global _active_due_alerts
    alerts = list(_active_due_alerts)
    _active_due_alerts.clear()
    return alerts

def peek_due_alerts() -> List[Dict[str, Any]]:
    """Returns currently due alerts without clearing them."""
    global _active_due_alerts
    return list(_active_due_alerts)
