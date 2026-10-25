import os
import re
import json
import uuid
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional

from database import (
    get_connection,
    create_reminder_record,
    get_reminders_list,
    save_user_document
)
from external_services import (
    get_live_weather,
    search_web,
    get_current_time,
    generate_icalendar
)

# Automatically load .env if present
def _load_env_if_present():
    env_paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        os.path.join(os.path.dirname(__file__), ".env")
    ]
    for p in env_paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k, v = k.strip(), v.strip().strip("'\"")
                            if k not in os.environ:
                                os.environ[k] = v
            except Exception:
                pass

_load_env_if_present()

# Default to modern high-speed Gemini 3.1 Flash Lite model
DEFAULT_GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")
# Verified available models supporting generateContent from ModelService.ListModels
FALLBACK_GEMINI_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-flash-lite-latest"
]

# Tool declarations for Gemini Function Calling
GEMINI_TOOLS_DECLARATION = [
    {
        "functionDeclarations": [
            {
                "name": "create_task",
                "description": "Create a new actionable task in the persistent SQLite database.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "title": {"type": "STRING", "description": "Concise task title"},
                        "deadline": {"type": "STRING", "description": "ISO 8601 deadline date/time string, e.g. 2026-10-26T18:00"},
                        "category": {"type": "STRING", "description": "Work, Study, Health, Personal, Finance"},
                        "priority": {"type": "STRING", "description": "urgent_important, important_not_urgent, urgent_not_important, neither"},
                        "estimated_duration": {"type": "INTEGER", "description": "Estimated minutes (15 to 240)"},
                        "description": {"type": "STRING", "description": "Optional notes or details"}
                    },
                    "required": ["title"]
                }
            },
            {
                "name": "get_weather",
                "description": "Get current real-time live weather and forecast for any city or location worldwide.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "location": {"type": "STRING", "description": "City or region name, e.g. Vijayawada, London, New York"}
                    },
                    "required": ["location"]
                }
            },
            {
                "name": "web_search",
                "description": "Perform a live web search for current events, news, technical facts, and real links.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {"type": "STRING", "description": "Search terms to look up"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "create_reminder",
                "description": "Schedule a real-time reminder at a specific ISO timestamp for the user.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "title": {"type": "STRING", "description": "Reminder text"},
                        "remind_at": {"type": "STRING", "description": "ISO 8601 datetime string when notification triggers"},
                        "channel": {"type": "STRING", "description": "in_app or browser"}
                    },
                    "required": ["title", "remind_at"]
                }
            },
            {
                "name": "complete_task",
                "description": "Mark an existing task in the database as completed.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "title_or_id": {"type": "STRING", "description": "The task title or ID to complete"}
                    },
                    "required": ["title_or_id"]
                }
            },
            {
                "name": "delete_task",
                "description": "Delete a task permanently from the database.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "title_or_id": {"type": "STRING", "description": "The task title or ID to delete"}
                    },
                    "required": ["title_or_id"]
                }
            },
            {
                "name": "list_tasks",
                "description": "Fetch the user's active tasks and deadlines from the database.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "status": {"type": "STRING", "description": "pending, in_progress, completed, or all"}
                    }
                }
            },
            {
                "name": "get_schedule",
                "description": "Retrieve today's optimized schedule and overload status.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "date": {"type": "STRING", "description": "YYYY-MM-DD date string"}
                    }
                }
            },
            {
                "name": "get_current_time",
                "description": "Get current real-time date, time, and timezone information.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "timezone": {"type": "STRING", "description": "Timezone name, e.g. Asia/Kolkata, UTC, America/New_York"}
                    }
                }
            }
        ]
    }
]

def get_api_key(db_key: str = "") -> str:
    if db_key and db_key.strip():
        return db_key.strip()
    env_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if env_key:
        return env_key
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT gemini_api_key FROM user_settings WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        if row and row["gemini_api_key"]:
            return row["gemini_api_key"].strip()
    except Exception:
        pass
    return ""

# ================= TIME AND SCHEDULING UTILITIES =================

def parse_time_to_minutes(time_str: str) -> int:
    try:
        parts = time_str.split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        return 9 * 60

def minutes_to_time_str(minutes: int) -> str:
    h = (minutes // 60) % 24
    m = minutes % 60
    return f"{h:02d}:{m:02d}"

def calculate_priority_score(task: Dict[str, Any], current_dt: datetime) -> float:
    score = 0.0
    priority = task.get("priority", "important_not_urgent")

    if priority == "urgent_important":
        score += 600
    elif priority == "important_not_urgent":
        score += 350
    elif priority == "urgent_not_important":
        score += 200
    else:
        score += 80

    deadline_str = task.get("deadline", "")
    if deadline_str:
        try:
            clean_str = deadline_str[:16]
            dl = datetime.fromisoformat(clean_str)
            hours_diff = (dl - current_dt).total_seconds() / 3600.0

            if hours_diff < 0:
                score += 1500 + abs(hours_diff) * 10
            elif hours_diff <= 3:
                score += 500
            elif hours_diff <= 8:
                score += 300
            elif hours_diff <= 24:
                score += 150
            else:
                score += 50
        except Exception:
            pass

    if task.get("status") == "in_progress":
        score += 400

    return score

# ================= REAL DATABASE ACTION EXECUTORS =================

def execute_create_task(
    title: str,
    deadline: str = None,
    category: str = "Work",
    priority: str = "important_not_urgent",
    estimated_duration: int = 45,
    description: str = ""
) -> Dict[str, Any]:
    """Saves a real task into SQLite and validates write before returning."""
    now = datetime.now()
    if not deadline:
        deadline = (now + timedelta(days=1)).strftime("%Y-%m-%dT18:00")
    elif len(deadline) == 10: # YYYY-MM-DD
        deadline = f"{deadline}T18:00"

    task_id = f"task-{uuid.uuid4().hex[:8]}"
    now_iso = now.isoformat()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(MAX(order_index), 0) + 1 FROM tasks")
    next_order = cursor.fetchone()[0]

    cursor.execute("""
    INSERT INTO tasks (
        id, title, description, category, priority, status,
        estimated_duration, deadline, scheduled_start, scheduled_end,
        created_at, completed_at, order_index
    )
    VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, NULL, NULL, ?, NULL, ?)
    """, (
        task_id,
        title.strip(),
        description.strip(),
        category,
        priority,
        int(estimated_duration),
        deadline,
        now_iso,
        next_order
    ))
    conn.commit()

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise RuntimeError("Failed to verify created task in database")

    return dict(row)

def execute_complete_task(title_or_id: str) -> Optional[Dict[str, Any]]:
    """Marks a task as completed in SQLite."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks WHERE id = ? OR LOWER(title) LIKE ?", (title_or_id, f"%{title_or_id.lower()}%"))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    task_id = row["id"]
    completed_at = datetime.now().isoformat()
    cursor.execute("""
    UPDATE tasks 
    SET status = 'completed', completed_at = ? 
    WHERE id = ?
    """, (completed_at, task_id))
    conn.commit()

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    updated_row = cursor.fetchone()
    conn.close()
    return dict(updated_row) if updated_row else None

def execute_delete_task(title_or_id: str) -> Optional[Dict[str, Any]]:
    """Deletes a task from SQLite."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks WHERE id = ? OR LOWER(title) LIKE ?", (title_or_id, f"%{title_or_id.lower()}%"))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    task_id = row["id"]
    task_dict = dict(row)
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return task_dict

def execute_list_tasks(status: str = "pending") -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if status and status != "all":
        cursor.execute("SELECT * FROM tasks WHERE status = ? ORDER BY deadline ASC", (status,))
    else:
        cursor.execute("SELECT * FROM tasks ORDER BY deadline ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def execute_plan_schedule(
    fixed_blocks: List[Dict[str, Any]],
    focus_blocks: List[Dict[str, Any]],
    settings: Dict[str, Any],
    target_date_str: str
) -> Dict[str, Any]:
    now = datetime.now()
    work_start = settings.get("work_start_time", "09:00")
    work_end = settings.get("work_end_time", "18:00")
    buffer_mins = settings.get("buffer_minutes", 15)

    conn = get_connection()
    cursor = conn.cursor()

    # 1. Insert fixed commitments as tasks if not already present
    created_tasks = []
    for fb in fixed_blocks:
        title = fb.get("title", "Commitment")
        s_time = fb.get("start_time", "09:00")
        e_time = fb.get("end_time", "13:00")
        s_min = parse_time_to_minutes(s_time)
        e_min = parse_time_to_minutes(e_time)
        dur = max(30, e_min - s_min)

        cursor.execute("SELECT * FROM tasks WHERE title = ? AND status != 'completed'", (title,))
        existing = cursor.fetchone()
        if not existing:
            t_id = f"task-{uuid.uuid4().hex[:8]}"
            cursor.execute("""
            INSERT INTO tasks (
                id, title, description, category, priority, status,
                estimated_duration, deadline, scheduled_start, scheduled_end,
                created_at, order_index
            ) VALUES (?, ?, 'Scheduled fixed commitment', 'Study', 'urgent_important', 'in_progress', ?, ?, ?, ?, ?, 0)
            """, (t_id, title, dur, f"{target_date_str}T{e_time}", s_time, e_time, now.isoformat()))
            created_tasks.append(t_id)
        else:
            cursor.execute("UPDATE tasks SET scheduled_start = ?, scheduled_end = ? WHERE id = ?", (s_time, e_time, existing["id"]))

    # 2. Insert focus blocks as tasks if not already present
    for foc in focus_blocks:
        title = foc.get("title", "Focus Session")
        dur = foc.get("duration_minutes", 120)
        cursor.execute("SELECT * FROM tasks WHERE title = ? AND status != 'completed'", (title,))
        existing = cursor.fetchone()
        if not existing:
            t_id = f"task-{uuid.uuid4().hex[:8]}"
            cursor.execute("""
            INSERT INTO tasks (
                id, title, description, category, priority, status,
                estimated_duration, deadline, created_at, order_index
            ) VALUES (?, ?, 'Deep work focus block', 'Study', 'urgent_important', 'pending', ?, ?, ?, 1)
            """, (t_id, title, dur, f"{target_date_str}T{work_end}", now.isoformat()))
            created_tasks.append(t_id)

    conn.commit()

    # Fetch all non-completed tasks
    cursor.execute("SELECT * FROM tasks WHERE status != 'completed'")
    pending_rows = cursor.fetchall()
    all_tasks = [dict(r) for r in pending_rows]
    conn.close()

    # Build schedule slots
    schedule = generate_daily_schedule(
        tasks=all_tasks,
        settings=settings,
        target_date_str=target_date_str,
        fixed_commitments=fixed_blocks
    )

    # Persist scheduled slots back into database
    conn = get_connection()
    cursor = conn.cursor()
    for s in schedule.get("slots", []):
        if s.get("task_id"):
            cursor.execute("""
            UPDATE tasks SET scheduled_start = ?, scheduled_end = ? WHERE id = ?
            """, (s["start_time"], s["end_time"], s["task_id"]))
    conn.commit()
    conn.close()

    return schedule

# ================= DAILY SCHEDULE GENERATOR =================

def generate_daily_schedule(
    tasks: List[Dict[str, Any]],
    settings: Dict[str, Any],
    target_date_str: str,
    gemini_key: str = "",
    fixed_commitments: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    now = datetime.now()
    work_start = settings.get("work_start_time", "09:00")
    work_end = settings.get("work_end_time", "18:00")
    buffer_mins = settings.get("buffer_minutes", 15)

    start_mins = parse_time_to_minutes(work_start)
    end_mins = parse_time_to_minutes(work_end)
    total_available_mins = max(0, end_mins - start_mins)

    slots: List[Dict[str, Any]] = []
    busy_intervals: List[Tuple[int, int]] = []

    # 1. Place fixed commitments first
    if fixed_commitments:
        for idx, fc in enumerate(fixed_commitments):
            fc_s = parse_time_to_minutes(fc.get("start_time", "09:00"))
            fc_e = parse_time_to_minutes(fc.get("end_time", "13:00"))
            busy_intervals.append((fc_s, fc_e))
            slots.append({
                "id": f"slot-fixed-{idx}",
                "task_id": None,
                "title": f"📌 {fc.get('title', 'Commitment')}",
                "start_time": minutes_to_time_str(fc_s),
                "end_time": minutes_to_time_str(fc_e),
                "duration_minutes": fc_e - fc_s,
                "category": "Study",
                "priority": "urgent_important",
                "is_buffer": False,
                "is_break": False,
                "status": "pending"
            })

    # Filter tasks to schedule
    eligible_tasks = [t for t in tasks if t.get("status") != "completed"]
    scored = []
    for t in eligible_tasks:
        if fixed_commitments and any(t["title"].lower() in fc.get("title", "").lower() for fc in fixed_commitments):
            continue
        scored.append((calculate_priority_score(t, now), t))
    scored.sort(key=lambda x: x[0], reverse=True)
    sorted_tasks = [item[1] for item in scored]

    current_ptr = start_mins
    lunch_added = False
    lunch_duration = 30

    for idx, t in enumerate(sorted_tasks):
        # Jump over busy fixed intervals
        for b_s, b_e in sorted(busy_intervals):
            if current_ptr < b_e and (current_ptr + 15) >= b_s:
                current_ptr = b_e + buffer_mins

        # Add lunch if around 12:30 - 13:30
        if not lunch_added and current_ptr >= (12 * 60 + 30) and current_ptr < (14 * 60):
            slots.append({
                "id": f"slot-lunch-{idx}",
                "task_id": None,
                "title": "🥗 Lunch & Cognitive Reset",
                "start_time": minutes_to_time_str(current_ptr),
                "end_time": minutes_to_time_str(current_ptr + lunch_duration),
                "duration_minutes": lunch_duration,
                "category": "Health",
                "priority": "important_not_urgent",
                "is_buffer": False,
                "is_break": True,
                "status": "pending"
            })
            current_ptr += lunch_duration
            lunch_added = True

        dur = t.get("estimated_duration", 45)
        s_end = current_ptr + dur

        slots.append({
            "id": f"slot-task-{t['id']}",
            "task_id": t["id"],
            "title": t["title"],
            "start_time": minutes_to_time_str(current_ptr),
            "end_time": minutes_to_time_str(s_end),
            "duration_minutes": dur,
            "category": t.get("category", "Work"),
            "priority": t.get("priority", "important_not_urgent"),
            "is_buffer": False,
            "is_break": False,
            "status": t.get("status", "pending")
        })
        current_ptr = s_end

        if buffer_mins > 0 and idx < len(sorted_tasks) - 1:
            slots.append({
                "id": f"slot-buffer-{idx}",
                "task_id": None,
                "title": f"⏱ Buffer Slot ({buffer_mins}m)",
                "start_time": minutes_to_time_str(current_ptr),
                "end_time": minutes_to_time_str(current_ptr + buffer_mins),
                "duration_minutes": buffer_mins,
                "category": "Personal",
                "priority": "neither",
                "is_buffer": True,
                "is_break": False,
                "status": "pending"
            })
            current_ptr += buffer_mins

    slots.sort(key=lambda s: parse_time_to_minutes(s["start_time"]))
    total_planned = sum(s["duration_minutes"] for s in slots if not s.get("is_break"))
    is_overloaded = total_planned > total_available_mins
    overload_mins = max(0, total_planned - total_available_mins)

    suggestions = []
    if is_overloaded:
        suggestions.append(f"⚠️ Schedule overload: Planned activities exceed working window by {overload_mins} mins.")
        suggestions.append("Consider timeboxing non-critical tasks or deferring lower priority items to tomorrow.")
    else:
        suggestions.append("✅ Balanced schedule: Realistic pace with built-in buffers between focus sprints.")
        suggestions.append("Tackle your primary deep work block when energy is highest.")

    return {
        "date": target_date_str,
        "work_start_time": work_start,
        "work_end_time": work_end,
        "total_planned_minutes": total_planned,
        "total_available_minutes": total_available_mins,
        "is_overloaded": is_overloaded,
        "overload_minutes": overload_mins,
        "slots": slots,
        "suggestions": suggestions,
        "engine_used": "deterministic" if not gemini_key else "gemini"
    }

# ================= TOOL DISPATCHER =================

def execute_tool(tool_name: str, args: Dict[str, Any], settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes a requested tool on the backend, validates the operation,
    and returns a structured execution result.
    """
    if tool_name == "create_task":
        title = args.get("title", "").strip()
        if not title:
            return {"success": False, "error": "Task title is required"}
        created = execute_create_task(
            title=title,
            deadline=args.get("deadline"),
            category=args.get("category", "Work"),
            priority=args.get("priority", "important_not_urgent"),
            estimated_duration=args.get("estimated_duration", 45),
            description=args.get("description", "")
        )
        return {"success": True, "task": created, "message": f"Task '{created['title']}' created successfully in database."}

    elif tool_name == "get_weather":
        location = args.get("location", "Vijayawada")
        res = get_live_weather(location)
        return res

    elif tool_name == "web_search":
        query = args.get("query", "")
        if not query:
            return {"success": False, "error": "Query cannot be empty"}
        res = search_web(query, max_results=4)
        return res

    elif tool_name == "create_reminder":
        title = args.get("title", "").strip()
        remind_at = args.get("remind_at", "")
        if not title:
            return {"success": False, "error": "Reminder title is required"}
        if not remind_at:
            remind_at = (datetime.now() + timedelta(minutes=30)).isoformat()
        created = create_reminder_record(
            title=title,
            remind_at=remind_at,
            channel=args.get("channel", "in_app")
        )
        return {"success": True, "reminder": created, "message": f"Reminder for '{title}' scheduled at {remind_at}."}

    elif tool_name == "complete_task":
        target = args.get("title_or_id", "")
        if not target:
            return {"success": False, "error": "Task title or ID required"}
        completed = execute_complete_task(target)
        if completed:
            return {"success": True, "task": completed, "message": f"Task '{completed['title']}' marked completed."}
        return {"success": False, "error": f"No active task found matching '{target}'."}

    elif tool_name == "delete_task":
        target = args.get("title_or_id", "")
        if not target:
            return {"success": False, "error": "Task title or ID required"}
        deleted = execute_delete_task(target)
        if deleted:
            return {"success": True, "task_id": deleted["id"], "title": deleted["title"], "message": f"Task '{deleted['title']}' deleted from database."}
        return {"success": False, "error": f"No task found matching '{target}' to delete."}

    elif tool_name == "list_tasks":
        tasks = execute_list_tasks(status=args.get("status", "pending"))
        return {"success": True, "count": len(tasks), "tasks": tasks[:10]}

    elif tool_name == "get_schedule":
        today_str = args.get("date") or datetime.now().strftime("%Y-%m-%d")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE status != 'completed'")
        all_tasks = [dict(r) for r in cursor.fetchall()]
        conn.close()
        sched = generate_daily_schedule(all_tasks, settings, today_str)
        return {"success": True, "schedule": sched}

    elif tool_name == "get_current_time":
        tz = args.get("timezone", settings.get("timezone", "auto"))
        return get_current_time(timezone_name=tz)

    return {"success": False, "error": f"Unknown tool: {tool_name}"}

# ================= DETERMINISTIC INTENT PARSER =================

def parse_natural_language_intent(message: str) -> Optional[Dict[str, Any]]:
    """
    Deterministically recognizes common user instructions without needing an external API key.
    Enables weather, web search, tasks, schedule planning, and reminders directly.
    """
    lower = message.strip().lower()

    # Weather: "what is the weather in Vijayawada right now?", "weather in London", "temperature in New York"
    weather_match = re.search(r"(?:what(?:'s| is) the weather in|weather in|weather for|temperature in)\s+([a-zA-Z\s]+?)(?:\s+right now|\s+today|\?|$)", lower)
    if weather_match:
        loc = weather_match.group(1).strip()
        return {"tool": "get_weather", "args": {"location": loc}}

    # Web search: "search for the latest AI developments", "search web for X", "search for X"
    search_match = re.search(r"(?:search for|search the web for|look up|search)\s+(?:the\s+)?(.+)", lower)
    if search_match and not any(k in lower for k in ["task", "schedule", "reminder", "plan"]):
        query = search_match.group(1).strip()
        return {"tool": "web_search", "args": {"query": query}}

    # Reminder: "remind me to finish report in 30 minutes", "remind me at 5 PM to call mom", "create a reminder for ..."
    if "remind" in lower:
        time_offset_match = re.search(r"in\s+(\d+)\s*(mins?|minutes?|hours?|hrs?)", lower)
        target_time = None
        now = datetime.now()
        if time_offset_match:
            val = int(time_offset_match.group(1))
            unit = time_offset_match.group(2)
            if "h" in unit:
                target_time = now + timedelta(hours=val)
            else:
                target_time = now + timedelta(minutes=val)
        else:
            target_time = now + timedelta(minutes=30)

        rem_title_match = re.search(r"remind\s+(?:me\s+)?(?:to\s+|for\s+)?(.+?)(?:\s+in\s+\d+|\s+at\s+\d+|$)", lower)
        title = rem_title_match.group(1).strip() if rem_title_match else "Reminder"
        title = title.capitalize()
        return {
            "tool": "create_reminder",
            "args": {
                "title": title,
                "remind_at": target_time.strftime("%Y-%m-%dT%H:%M:%S")
            }
        }

    # Create task: "create a task to finish my Java assignment tomorrow"
    create_match = re.search(r"(?:create|add|schedule|set up)(?:\s+a)?\s+task\s+(?:to\s+|for\s+|called\s+)?(.+)", lower)
    if create_match and not any(k in lower for k in ["plan my day", "classes from"]):
        raw_task_info = create_match.group(1).strip()
        raw_task_info = re.sub(r"^(?:finish|complete)\s+", "", raw_task_info, flags=re.IGNORECASE).strip()

        now = datetime.now()
        deadline = (now + timedelta(days=1)).strftime("%Y-%m-%dT18:00")
        dur = 45
        cat = "Work"
        priority = "urgent_important"

        if "tomorrow" in raw_task_info:
            deadline = (now + timedelta(days=1)).strftime("%Y-%m-%dT18:00")
            raw_task_info = re.sub(r"\btomorrow\b", "", raw_task_info).strip()
        elif "today" in raw_task_info:
            deadline = now.strftime("%Y-%m-%dT21:00")
            raw_task_info = re.sub(r"\btoday\b", "", raw_task_info).strip()
        elif "next week" in raw_task_info:
            deadline = (now + timedelta(days=7)).strftime("%Y-%m-%dT18:00")
            raw_task_info = re.sub(r"\bnext week\b", "", raw_task_info).strip()

        raw_task_info = re.sub(r"\s+(?:by|at|for|on)$", "", raw_task_info).strip()
        if not raw_task_info:
            raw_task_info = "New Assignment"

        if any(w in lower for w in ["study", "exam", "reading", "java", "python", "course", "assignment", "homework", "math"]):
            cat = "Study"

        return {
            "tool": "create_task",
            "args": {
                "title": raw_task_info.capitalize(),
                "deadline": deadline,
                "category": cat,
                "priority": priority,
                "estimated_duration": dur,
                "description": f"Created via user instruction: '{message}'"
            }
        }

    # Complete task
    complete_match = re.search(r"(?:complete|finish|mark as (?:completed|done))\s+(?:task\s+)?(.+)", lower)
    if complete_match:
        return {"tool": "complete_task", "args": {"title_or_id": complete_match.group(1).strip()}}

    # Delete task
    delete_match = re.search(r"(?:delete|remove)\s+(?:task\s+)?(.+)", lower)
    if delete_match:
        return {"tool": "delete_task", "args": {"title_or_id": delete_match.group(1).strip()}}

    # Plan day: "plan my day", "plan today"
    if any(k in lower for k in ["plan my day", "plan today", "schedule my day", "classes from"]):
        fixed_events = []
        focus_blocks = []

        time_range_match = re.search(r"(\w+)\s+from\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s+to\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)", lower)
        if time_range_match:
            event_title = time_range_match.group(1).capitalize()
            raw_s = time_range_match.group(2).strip()
            raw_e = time_range_match.group(3).strip()

            def normalize_hour(s: str) -> str:
                s = s.lower().strip()
                is_pm = "pm" in s
                is_am = "am" in s
                num_part = re.sub(r"[^\d:]", "", s)
                parts = num_part.split(":")
                h = int(parts[0])
                m = int(parts[1]) if len(parts) > 1 else 0
                if is_pm and h < 12:
                    h += 12
                elif is_am and h == 12:
                    h = 0
                return f"{h:02d}:{m:02d}"

            fixed_events.append({
                "title": event_title,
                "start_time": normalize_hour(raw_s),
                "end_time": normalize_hour(raw_e)
            })

        duration_match = re.search(r"(?:need|want|have)\s+(\w+|\d+)\s+hours?\s+(?:for|of)\s+([^.,;\n]+)", lower)
        if duration_match:
            dur_word = duration_match.group(1).lower()
            topic = duration_match.group(2).strip().capitalize()
            dur_map = {"one": 60, "two": 120, "three": 180, "four": 240, "1": 60, "2": 120, "3": 180}
            mins = dur_map.get(dur_word, 120)
            focus_blocks.append({"title": topic, "duration_minutes": mins})

        return {
            "tool": "plan_schedule",
            "fixed_events": fixed_events,
            "focus_blocks": focus_blocks
        }

    # Date / Time
    if any(k in lower for k in ["what time is it", "current time", "what day is today", "what's the date"]):
        return {"tool": "get_current_time", "args": {}}

    return None

# ================= GEMINI API INFERENCE WITH RESILIENT MODEL CALLING =================

def _execute_gemini_request(
    model_name: str,
    api_key: str,
    contents: list,
    system_instruction: str = ""
) -> dict:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    payload = {
        "contents": contents,
        "tools": GEMINI_TOOLS_DECLARATION,
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1500
        }
    }
    if system_instruction:
        payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=18) as resp:
        return json.loads(resp.read().decode("utf-8"))

def call_gemini_with_tools(
    prompt: str,
    api_key: str,
    system_instruction: str,
    conversation_history: List[Dict[str, str]],
    settings: Dict[str, Any],
    model_name: str = None
) -> Tuple[str, List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Calls Google Gemini with full function calling (tool execution) capabilities.
    If the requested model is sunset or returns 404, automatically tries active fallback models.
    """
    configured_model = os.environ.get("GEMINI_MODEL", "").strip() or DEFAULT_GEMINI_MODEL
    primary_model = model_name or configured_model
    # Order candidates: primary model first, followed by known active fallback models
    candidate_models = [primary_model]
    for fb in FALLBACK_GEMINI_MODELS:
        if fb not in candidate_models:
            candidate_models.append(fb)

    contents = []
    if conversation_history:
        for turn in conversation_history[-10:]:
            role = "user" if turn.get("role") in ["user", "human"] else "model"
            text = turn.get("content") or turn.get("text") or ""
            if text.strip():
                contents.append({"role": role, "parts": [{"text": text}]})

    contents.append({"role": "user", "parts": [{"text": prompt}]})

    resp_data = None
    last_error = None

    for candidate in candidate_models:
        try:
            resp_data = _execute_gemini_request(candidate, api_key, contents, system_instruction)
            if resp_data:
                break
        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")
                err_json = json.loads(error_body)
                error_msg = err_json.get("error", {}).get("message", error_body)
            except Exception:
                error_msg = str(e)

            # Distinguish authentication / authorization failures
            if e.code in (401, 403) or "api_key_invalid" in error_msg.lower() or "api key not valid" in error_msg.lower() or "permission_denied" in error_msg.lower():
                raise RuntimeError(f"Gemini API Authentication Error (HTTP {e.code}): Your Gemini API key is invalid or unauthorized. Please verify your API key in Settings or .env.")
            # Distinguish rate limits / quota
            elif e.code == 429 or "resource_exhausted" in error_msg.lower() or "quota" in error_msg.lower():
                raise RuntimeError(f"Gemini API Quota Exceeded (HTTP 429): Rate limit or quota exhausted. Please try again shortly.")
            # If model is 404/not supported, try next candidate model
            elif e.code == 404 or "not found" in error_msg.lower() or "no longer available" in error_msg.lower():
                last_error = RuntimeError(f"Gemini API HTTP 404 on model '{candidate}': {error_msg}")
                continue
            else:
                # Other HTTP errors (e.g. 400 Bad Request)
                raise RuntimeError(f"Gemini API HTTP {e.code}: {error_msg}")
        except Exception as ex:
            last_error = ex
            continue

    if not resp_data:
        if last_error:
            raise last_error
        raise RuntimeError("No response received from any configured Gemini model.")

    candidates = resp_data.get("candidates", [])
    if not candidates:
        return "No response generated by Gemini model.", [], None

    candidate = candidates[0]
    parts = candidate.get("content", {}).get("parts", [])

    # Check if model requested a function call
    function_call = None
    for p in parts:
        if "functionCall" in p:
            function_call = p["functionCall"]
            break

    tool_executions = []
    action_executed = None

    if function_call:
        fn_name = function_call.get("name")
        fn_args = function_call.get("args", {})

        # Execute the tool on the backend
        exec_result = execute_tool(fn_name, fn_args, settings)
        tool_rec = {
            "tool_name": fn_name,
            "arguments": fn_args,
            "result": exec_result,
            "success": exec_result.get("success", True),
            "message": exec_result.get("message", f"Executed {fn_name}")
        }
        tool_executions.append(tool_rec)
        action_executed = {"type": fn_name, "data": exec_result}

        # Synthesize natural response from executed tool
        if fn_name == "create_task" and exec_result.get("success"):
            t = exec_result["task"]
            clean_dl = t["deadline"][:16].replace("T", " at ")
            reply = (
                f"✅ **Task Created and Saved to Database**\n\n"
                f"• **Title:** {t['title']}\n"
                f"• **Category:** {t['category']} | **Priority:** {t['priority']}\n"
                f"• **Estimated Duration:** {t['estimated_duration']} mins\n"
                f"• **Deadline:** {clean_dl}\n\n"
                f"The task is now persistently stored in your SQLite database and visible in your **My Tasks** board."
            )
        elif fn_name == "get_weather" and exec_result.get("success"):
            reply = (
                f"🌤️ **Current Weather in {exec_result['city']}, {exec_result.get('country', '')}**\n\n"
                f"• **Condition:** {exec_result.get('condition')}\n"
                f"• **Temperature:** {exec_result.get('temperature_c')}°C ({exec_result.get('temperature_f')}°F)\n"
                f"• **Feels Like:** {exec_result.get('feels_like_c')}°C | **Humidity:** {exec_result.get('humidity_percent')}%\n"
                f"• **Wind Speed:** {exec_result.get('wind_speed_kmh')} km/h\n"
                f"• **Observation Time:** {exec_result.get('observation_time', '')} ({exec_result.get('timezone', '')})\n\n"
                f"*Source: {exec_result.get('source')} (Live Real-Time Data)*"
            )
        elif fn_name == "web_search" and exec_result.get("success"):
            results = exec_result.get("results", [])
            lines = [f"🔍 **Live Search Results for \"{exec_result.get('query')}\":**\n"]
            for idx, r in enumerate(results[:4], 1):
                lines.append(f"**{idx}. [{r['title']}]({r['url']})**\n{r['snippet']}\n*Source:* {r['url']}\n")
            reply = "\n".join(lines)
        elif fn_name == "create_reminder" and exec_result.get("success"):
            rem = exec_result["reminder"]
            reply = (
                f"⏰ **Reminder Scheduled**\n\n"
                f"• **Title:** {rem['title']}\n"
                f"• **Scheduled For:** {rem['remind_at'].replace('T', ' ')}\n"
                f"• **Channel:** In-app alert & browser notification\n\n"
                f"The backend scheduler will trigger this alert automatically at the scheduled time."
            )
        elif fn_name == "complete_task":
            if exec_result.get("success"):
                reply = f"🎉 **Task Completed!** Marked **\"{exec_result['task']['title']}\"** as complete in the database."
            else:
                reply = f"⚠️ {exec_result.get('error', 'Could not complete task.')}"
        elif fn_name == "delete_task":
            if exec_result.get("success"):
                reply = f"🗑️ **Task Deleted:** Removed **\"{exec_result.get('title')}\"** from the database."
            else:
                reply = f"⚠️ {exec_result.get('error', 'Could not delete task.')}"
        elif fn_name == "get_current_time":
            reply = (
                f"🕒 **Current Local Time**\n\n"
                f"• **Date:** {exec_result.get('date')} ({exec_result.get('day_of_week')})\n"
                f"• **Time:** {exec_result.get('time_12h')} ({exec_result.get('time_24h')})\n"
                f"• **Timezone:** {exec_result.get('timezone')}"
            )
        else:
            reply = f"✅ Executed operation `{fn_name}`: {exec_result.get('message', 'Completed successfully.')}"

        return reply, tool_executions, action_executed

    text_parts = [p.get("text", "") for p in parts if "text" in p]
    return "".join(text_parts).strip(), [], None

# ================= ASSISTANT MAIN ENTRY POINT =================

def chat_with_assistant(
    message: str,
    conversation_history: List[Dict[str, str]],
    context: Dict[str, Any],
    gemini_key: str = ""
) -> Dict[str, Any]:
    api_key = get_api_key(gemini_key)
    tasks = context.get("tasks", [])
    overdue_count = context.get("overdue_count", 0)
    pending_count = context.get("pending_count", 0)
    focus_today = context.get("focus_today_minutes", 0)
    user_name = context.get("user_name", "User")
    settings = context.get("settings", {})

    parsed = parse_natural_language_intent(message)

    # 1. If parsed as a direct deterministic tool, execute immediately
    if parsed and parsed.get("tool"):
        tool_name = parsed["tool"]

        if tool_name == "plan_schedule":
            try:
                today_str = datetime.now().strftime("%Y-%m-%d")
                sched = execute_plan_schedule(
                    fixed_blocks=parsed.get("fixed_events", []),
                    focus_blocks=parsed.get("focus_blocks", []),
                    settings=settings,
                    target_date_str=today_str
                )
                slot_lines = []
                for s in sched.get("slots", [])[:8]:
                    slot_lines.append(f"• **{s['start_time']} – {s['end_time']}**: {s['title']} ({s['duration_minutes']}m)")

                reply_text = (
                    f"📅 **Custom Daily Schedule Created & Saved**\n\n"
                    + "\n".join(slot_lines) + "\n\n"
                    f"• **Total Planned:** {sched.get('total_planned_minutes')} mins (Available: {sched.get('total_available_minutes')} mins)\n"
                    f"• **Status:** {'⚠️ Overload Warning' if sched.get('is_overloaded') else '✅ Realistic & Balanced'}\n\n"
                    f"Your commitments have been saved to your database and populated directly in the **AI Planner**."
                )
                return {
                    "reply": reply_text,
                    "engine_used": "real_action_engine",
                    "suggested_actions": [
                        {"label": "Open AI Planner", "route": "planner"},
                        {"label": "View Tasks", "route": "tasks"}
                    ],
                    "action_executed": {"type": "schedule_updated", "schedule": sched},
                    "tool_executions": [{
                        "tool_name": "plan_schedule",
                        "arguments": {"fixed_events": parsed.get("fixed_events", []), "focus_blocks": parsed.get("focus_blocks", [])},
                        "success": True,
                        "message": "Schedule generated and saved to SQLite"
                    }]
                }
            except Exception as e:
                return {
                    "reply": f"❌ Failed to generate schedule: {str(e)}",
                    "engine_used": "system_error",
                    "suggested_actions": [{"label": "Open Planner", "route": "planner"}]
                }

        # For other direct tools
        exec_res = execute_tool(tool_name, parsed.get("args", {}), settings)
        tool_rec = {
            "tool_name": tool_name,
            "arguments": parsed.get("args", {}),
            "result": exec_res,
            "success": exec_res.get("success", True),
            "message": exec_res.get("message", f"Executed {tool_name}")
        }

        if tool_name == "create_task" and exec_res.get("success"):
            t = exec_res["task"]
            clean_dl = t["deadline"][:16].replace("T", " at ")
            reply_text = (
                f"✅ **Task Created and Saved**\n\n"
                f"• **Title:** {t['title']}\n"
                f"• **Category:** {t['category']} | **Priority:** {t['priority']}\n"
                f"• **Duration:** {t['estimated_duration']} mins\n"
                f"• **Deadline:** {clean_dl}\n\n"
                f"Saved to SQLite database. Visible in **My Tasks** and schedule."
            )
            return {
                "reply": reply_text,
                "engine_used": "real_action_engine",
                "suggested_actions": [
                    {"label": "View in Tasks", "route": "tasks"},
                    {"label": "View Schedule", "route": "planner"}
                ],
                "action_executed": {"type": "task_created", "task": t},
                "tool_executions": [tool_rec]
            }

        elif tool_name == "get_weather":
            if exec_res.get("success"):
                reply_text = (
                    f"🌤️ **Current Weather in {exec_res['city']}, {exec_res.get('country', '')}**\n\n"
                    f"• **Condition:** {exec_res.get('condition')}\n"
                    f"• **Temperature:** {exec_res.get('temperature_c')}°C ({exec_res.get('temperature_f')}°F)\n"
                    f"• **Feels Like:** {exec_res.get('feels_like_c')}°C | **Humidity:** {exec_res.get('humidity_percent')}%\n"
                    f"• **Wind Speed:** {exec_res.get('wind_speed_kmh')} km/h\n"
                    f"• **Observation Time:** {exec_res.get('observation_time', '')}\n\n"
                    f"*Source: {exec_res.get('source')} (Live Real-Time Data)*"
                )
            else:
                reply_text = f"⚠️ Weather error: {exec_res.get('error')}"
            return {
                "reply": reply_text,
                "engine_used": "real_action_engine",
                "suggested_actions": [{"label": "Search Weather for Another City", "route": "assistant"}],
                "action_executed": {"type": "weather_retrieved", "weather": exec_res},
                "tool_executions": [tool_rec]
            }

        elif tool_name == "web_search":
            if exec_res.get("success"):
                results = exec_res.get("results", [])
                lines = [f"🔍 **Live Web Search Results for \"{exec_res.get('query')}\":**\n"]
                for idx, r in enumerate(results[:4], 1):
                    lines.append(f"**{idx}. [{r['title']}]({r['url']})**\n{r['snippet']}\n*Source:* {r['url']}\n")
                reply_text = "\n".join(lines)
            else:
                reply_text = f"⚠️ Search error: {exec_res.get('error')}"
            return {
                "reply": reply_text,
                "engine_used": "real_action_engine",
                "suggested_actions": [{"label": "View Tasks", "route": "tasks"}],
                "action_executed": {"type": "web_search", "search": exec_res},
                "tool_executions": [tool_rec]
            }

        elif tool_name == "create_reminder":
            if exec_res.get("success"):
                rem = exec_res["reminder"]
                reply_text = (
                    f"⏰ **Reminder Created and Scheduled**\n\n"
                    f"• **Title:** {rem['title']}\n"
                    f"• **Remind At:** {rem['remind_at'].replace('T', ' ')}\n"
                    f"• **Channel:** In-app notification & browser alert\n\n"
                    f"Processed by background scheduler."
                )
            else:
                reply_text = f"⚠️ Reminder error: {exec_res.get('error')}"
            return {
                "reply": reply_text,
                "engine_used": "real_action_engine",
                "suggested_actions": [{"label": "View Tasks", "route": "tasks"}],
                "action_executed": {"type": "reminder_created", "reminder": exec_res.get("reminder")},
                "tool_executions": [tool_rec]
            }

        elif tool_name == "complete_task":
            if exec_res.get("success"):
                reply_text = f"🎉 **Task Completed:** Marked **\"{exec_res['task']['title']}\"** as complete in your database."
            else:
                reply_text = f"⚠️ {exec_res.get('error')}"
            return {
                "reply": reply_text,
                "engine_used": "real_action_engine",
                "suggested_actions": [{"label": "View Tasks", "route": "tasks"}],
                "action_executed": {"type": "task_completed", "task": exec_res.get("task")},
                "tool_executions": [tool_rec]
            }

        elif tool_name == "delete_task":
            if exec_res.get("success"):
                reply_text = f"🗑️ **Task Deleted:** Successfully removed **\"{exec_res.get('title')}\"** from your database."
            else:
                reply_text = f"⚠️ {exec_res.get('error')}"
            return {
                "reply": reply_text,
                "engine_used": "real_action_engine",
                "suggested_actions": [{"label": "View Tasks", "route": "tasks"}],
                "action_executed": {"type": "task_deleted", "task_id": exec_res.get("task_id")},
                "tool_executions": [tool_rec]
            }

        elif tool_name == "get_current_time":
            reply_text = (
                f"🕒 **Current Date & Time:**\n\n"
                f"• {exec_res.get('formatted_display')}\n"
                f"• Timezone: {exec_res.get('timezone')}"
            )
            return {
                "reply": reply_text,
                "engine_used": "real_action_engine",
                "suggested_actions": [{"label": "Plan My Day", "route": "planner"}],
                "tool_executions": [tool_rec]
            }

    # 2. Conversational query: If Gemini is configured, use real Gemini model inference with tools
    if api_key:
        try:
            task_titles = [t.get("title") for t in tasks[:5]]
            system_prompt = f"""
You are AI LifePilot, an intelligent, concise, and highly capable daily productivity copilot for {user_name}.
Current user context:
- Pending tasks in DB: {pending_count} ({overdue_count} overdue)
- Focus logged today: {focus_today} minutes
- Top queued tasks: {task_titles}
- Working hours: {settings.get('work_start_time', '09:00')} - {settings.get('work_end_time', '18:00')}
- Timezone: {settings.get('timezone', 'auto')}

Rules:
1. When asked to create a task, get weather, search web, set a reminder, or manage tasks, use your declared tools!
2. Answer questions concisely and practically.
3. Never invent tasks or claim actions succeeded without invoking the tool.
"""
            reply, tool_recs, action_exec = call_gemini_with_tools(
                prompt=message,
                api_key=api_key,
                system_instruction=system_prompt,
                conversation_history=conversation_history,
                settings=settings
            )
            return {
                "reply": reply,
                "engine_used": "gemini",
                "suggested_actions": [
                    {"label": "View Schedule", "route": "planner"},
                    {"label": "View Tasks", "route": "tasks"}
                ],
                "tool_executions": tool_recs,
                "action_executed": action_exec
            }
        except Exception as e:
            return {
                "reply": (
                    f"⚠️ **Google Gemini API Error**: Unable to contact AI model provider:\n\n"
                    f"`{str(e)}`\n\n"
                    f"Please verify your API key in **Settings** or check your internet connection. Supported actions (creating tasks, weather, web search, scheduling, reminders) remain active."
                ),
                "engine_used": "api_error_notice",
                "suggested_actions": [
                    {"label": "Open Settings", "route": "settings"},
                    {"label": "View Tasks", "route": "tasks"}
                ],
                "tool_executions": []
            }

    # 3. If Gemini API key is NOT configured
    top_task = tasks[0]["title"] if tasks else "no active tasks"
    return {
        "reply": (
            f"ℹ️ **Google Gemini API Key Optional for Conversational Coaching**\n\n"
            f"To enable open-ended generative chat and AI coaching, enter your Google Gemini API key in **Settings** (obtain free at [Google AI Studio](https://aistudio.google.com)).\n\n"
            f"**All Real-Time Tools and Backend Services Are Fully Operational Without an API Key:**\n"
            f"• **Weather:** *\"What is the weather in Vijayawada right now?\"*\n"
            f"• **Web Search:** *\"Search for the latest AI developments\"*\n"
            f"• **Task Management:** *\"Create a task to finish my Java assignment tomorrow\"*\n"
            f"• **Scheduling:** *\"Plan my day. I have classes from 9 AM to 1 PM and need two hours for Java practice\"*\n"
            f"• **Reminders:** *\"Remind me in 30 minutes to review my code\"*\n"
            f"• **Status:** *\"Complete [task name]\"* or *\"Delete task [task name]\"*\n\n"
            f"**Workspace Snapshot:** {pending_count} pending tasks ({overdue_count} overdue) | Top: \"{top_task}\""
        ),
        "engine_used": "deterministic_engine",
        "suggested_actions": [
            {"label": "Configure API Key in Settings", "route": "settings"},
            {"label": "Open AI Planner", "route": "planner"},
            {"label": "Manage Tasks", "route": "tasks"}
        ],
        "tool_executions": []
    }

# ================= GOAL BREAKDOWN ENGINE =================

def breakdown_goal(
    goal_title: str,
    target_deadline: str = None,
    category: str = "Study",
    gemini_key: str = ""
) -> Dict[str, Any]:
    api_key = get_api_key(gemini_key)

    if api_key:
        configured_model = os.environ.get("GEMINI_MODEL", "").strip() or DEFAULT_GEMINI_MODEL
        candidate_models = [configured_model] + [m for m in FALLBACK_GEMINI_MODELS if m != configured_model]
        prompt = f"""
Goal: "{goal_title}"
Category: {category}
Deadline: {target_deadline or 'This week'}

Break this goal into 4 to 5 concrete, actionable, bite-sized tasks.
Return ONLY valid JSON in this exact structure:
{{
  "explanation": "Short 1-2 sentence strategy explanation",
  "subtasks": [
    {{
      "title": "Subtask title",
      "description": "Clear physical action to take",
      "category": "{category}",
      "priority": "urgent_important",
      "estimated_duration": 45,
      "suggested_day_offset": 0
    }}
  ]
}}
"""
        for model in candidate_models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                payload = {
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1000}
                }
                req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=12) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    text = result["candidates"][0]["content"]["parts"][0]["text"]
                    match = re.search(r"\{.*\}", text, re.DOTALL)
                    if match:
                        parsed = json.loads(match.group(0))
                        return {
                            "goal_title": goal_title,
                            "subtasks": parsed.get("subtasks", []),
                            "engine_used": "gemini",
                            "explanation": parsed.get("explanation", "Goal structured into prioritized milestones.")
                        }
            except Exception:
                continue

    # Deterministic fallback decomposition
    subtasks = [
        {
            "title": f"Phase 1: Define scope & requirements for {goal_title[:35]}",
            "description": "Outline objectives, success criteria, and assemble reference materials.",
            "category": category,
            "priority": "urgent_important",
            "estimated_duration": 45,
            "suggested_day_offset": 0
        },
        {
            "title": f"Phase 2: Core execution & drafting for {goal_title[:35]}",
            "description": "Focus sprint executing the foundational components.",
            "category": category,
            "priority": "urgent_important",
            "estimated_duration": 60,
            "suggested_day_offset": 1
        },
        {
            "title": "Phase 3: Review, testing & edge case validation",
            "description": "Check quality against requirements, fix gaps, and polish results.",
            "category": category,
            "priority": "important_not_urgent",
            "estimated_duration": 45,
            "suggested_day_offset": 2
        },
        {
            "title": "Phase 4: Final packaging & milestone completion",
            "description": "Deliver final output and perform retrospective review.",
            "category": category,
            "priority": "important_not_urgent",
            "estimated_duration": 30,
            "suggested_day_offset": 3
        }
    ]

    return {
        "goal_title": goal_title,
        "subtasks": subtasks,
        "engine_used": "deterministic_engine",
        "explanation": "Structured into a practical 4-stage execution roadmap (Scope -> Build -> Polish -> Deliver)."
    }
