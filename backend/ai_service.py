import os
import re
import json
import uuid
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
from database import get_connection

DEFAULT_GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")

def get_api_key(db_key: str = "") -> str:
    env_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if env_key:
        return env_key
    if db_key and db_key.strip():
        return db_key.strip()
    return ""

def call_gemini(
    prompt: str,
    api_key: str,
    system_instruction: str = "",
    history: List[Dict[str, str]] = None,
    model_name: str = None
) -> str:
    if not api_key:
        raise ValueError("No Gemini API key provided")

    active_model = model_name or DEFAULT_GEMINI_MODEL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{active_model}:generateContent?key={api_key}"

    contents = []
    # Include history turns if provided
    if history:
        for turn in history[-10:]: # keep last 10 turns for context
            role = "user" if turn.get("role") in ["user", "human"] else "model"
            text_content = turn.get("content") or turn.get("text") or ""
            if text_content.strip():
                contents.append({
                    "role": role,
                    "parts": [{"text": text_content}]
                })

    # Append current user prompt
    contents.append({
        "role": "user",
        "parts": [{"text": prompt}]
    })

    payload: Dict[str, Any] = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 1500
        }
    }

    if system_instruction:
        payload["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
            candidates = result.get("candidates", [])
            if candidates and "content" in candidates[0]:
                parts = candidates[0]["content"].get("parts", [])
                if parts and "text" in parts[0]:
                    return parts[0]["text"]
        raise RuntimeError("Empty response received from Gemini API")
    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode("utf-8")
            err_json = json.loads(error_body)
            error_msg = err_json.get("error", {}).get("message", error_body)
        except Exception:
            error_msg = str(e)
        raise RuntimeError(f"Gemini API HTTP {e.code}: {error_msg}")
    except Exception as ex:
        raise RuntimeError(f"Gemini API connection failure: {str(ex)}")


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
        # Default deadline: tomorrow at 18:00
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

def execute_plan_schedule(
    fixed_blocks: List[Dict[str, Any]],
    focus_blocks: List[Dict[str, Any]],
    settings: Dict[str, Any],
    target_date_str: str
) -> Dict[str, Any]:
    """
    Builds a real schedule incorporating fixed commitments (e.g. classes 9-1)
    and focus sessions (e.g. 2 hours Java practice) alongside existing pending tasks.
    Saves new events to tasks and sets schedule times.
    """
    now = datetime.now()
    work_start = settings.get("work_start_time", "09:00")
    work_end = settings.get("work_end_time", "18:00")
    buffer_mins = settings.get("buffer_minutes", 15)

    start_mins = parse_time_to_minutes(work_start)
    end_mins = parse_time_to_minutes(work_end)

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
    # Sort eligible tasks by priority score
    scored = []
    for t in eligible_tasks:
        # Don't duplicate fixed commitments
        if fixed_commitments and any(t["title"].lower() in fc.get("title", "").lower() for fc in fixed_commitments):
            continue
        scored.append((calculate_priority_score(t, now), t))
    scored.sort(key=lambda x: x[0], reverse=True)
    sorted_tasks = [item[1] for item in scored]

    current_ptr = start_mins
    lunch_added = False
    lunch_start = 13 * 60 # 1:00 PM
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

    # Sort all slots by start_time
    slots.sort(key=lambda s: parse_time_to_minutes(s["start_time"]))

    total_planned = sum(s["duration_minutes"] for s in slots if not s.get("is_break"))
    is_overloaded = total_planned > total_available_mins
    overload_mins = max(0, total_planned - total_available_mins)

    suggestions = []
    if is_overloaded:
        suggestions.append(f"⚠️ Schedule overload: Planned activities exceed working window by {overload_mins} mins.")
        suggestions.append("Consider timeboxing non-critical tasks or deferring lower priority items to tomorrow.")
    else:
        suggestions.append(f"✅ Balanced schedule: Realistic pace with built-in buffers between focus sprints.")
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


# ================= NATURAL LANGUAGE PARSER & COPILOT =================

def parse_natural_language_intent(message: str) -> Dict[str, Any]:
    """
    Deterministically detects user commands like:
    - 'Create a task to finish my project report tomorrow'
    - 'Plan my day. I have classes from 9 AM to 1 PM and need two hours for Java practice.'
    - 'Mark finish my project report as completed'
    - 'Delete task ...'
    """
    lower = message.strip().lower()

    # 1. Create Task Intent
    create_match = re.search(r"(?:create|add|schedule|set up)(?:\s+a)?\s+task\s+(?:to\s+|for\s+|called\s+)?(.+)", lower, re.IGNORECASE)
    if create_match and not any(k in lower for k in ["plan my day", "classes from"]):
        raw_task_info = create_match.group(1).strip()
        # Extract title and relative deadline
        now = datetime.now()
        deadline = (now + timedelta(days=1)).strftime("%Y-%m-%dT18:00")
        dur = 60
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

        # Clean trailing prepositions
        raw_task_info = re.sub(r"\s+(?:by|at|for|on)$", "", raw_task_info).strip()
        if not raw_task_info:
            raw_task_info = "New Task"

        # Capitalize nicely
        clean_title = raw_task_info.capitalize()

        if any(w in lower for w in ["study", "exam", "reading", "java", "python", "course", "assignment", "homework"]):
            cat = "Study"

        return {
            "intent": "create_task",
            "title": clean_title,
            "deadline": deadline,
            "category": cat,
            "priority": priority,
            "estimated_duration": dur,
            "description": f"Created via AI Copilot instruction: '{message}'"
        }

    # 2. Plan Day Intent with constraints
    # Example: "Plan my day. I have classes from 9 AM to 1 PM and need two hours for Java practice."
    if any(k in lower for k in ["plan my day", "plan today", "schedule my day", "classes from", "schedule today"]):
        fixed_events = []
        focus_blocks = []

        # Check for classes or meetings from X to Y
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

        # Check for focus/practice block: "two hours for Java practice" or "2 hours of X"
        duration_match = re.search(r"(?:need|want|have)\s+(\w+|\d+)\s+hours?\s+(?:for|of)\s+([^.,;\n]+)", lower)
        if duration_match:
            dur_word = duration_match.group(1).lower()
            topic = duration_match.group(2).strip().capitalize()
            dur_map = {"one": 60, "two": 120, "three": 180, "four": 240, "1": 60, "2": 120, "3": 180}
            mins = dur_map.get(dur_word, 120)
            focus_blocks.append({
                "title": topic,
                "duration_minutes": mins
            })

        return {
            "intent": "plan_day",
            "fixed_events": fixed_events,
            "focus_blocks": focus_blocks
        }

    # 3. Complete Task Intent
    complete_match = re.search(r"(?:complete|finish|mark as (?:completed|done))\s+(?:task\s+)?(.+)", lower)
    if complete_match:
        target = complete_match.group(1).strip()
        return {"intent": "complete_task", "target": target}

    # 4. Delete Task Intent
    delete_match = re.search(r"(?:delete|remove)\s+(?:task\s+)?(.+)", lower)
    if delete_match:
        target = delete_match.group(1).strip()
        return {"intent": "delete_task", "target": target}

    return {"intent": "conversational"}


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

    parsed_intent = parse_natural_language_intent(message)

    # --- 1. HANDLE REAL ACTION: CREATE TASK ---
    if parsed_intent["intent"] == "create_task":
        try:
            created = execute_create_task(
                title=parsed_intent["title"],
                deadline=parsed_intent["deadline"],
                category=parsed_intent["category"],
                priority=parsed_intent["priority"],
                estimated_duration=parsed_intent["estimated_duration"],
                description=parsed_intent["description"]
            )
            clean_deadline = created["deadline"][:16].replace("T", " at ")
            reply_text = (
                f"✅ **Task Created and Saved**\n\n"
                f"• **Title:** {created['title']}\n"
                f"• **Category:** {created['category']} | **Priority:** Urgent & Important\n"
                f"• **Duration:** {created['estimated_duration']} mins\n"
                f"• **Deadline:** {clean_deadline}\n\n"
                f"This task is now stored in your SQLite database and added to your **My Tasks** board and daily schedule."
            )
            return {
                "reply": reply_text,
                "engine_used": "real_action_engine",
                "suggested_actions": [
                    {"label": "View in Tasks", "route": "tasks"},
                    {"label": "View Today's Schedule", "route": "planner"},
                    {"label": "Start Focus Session", "route": "focus"}
                ],
                "action_executed": {
                    "type": "task_created",
                    "task": created
                }
            }
        except Exception as e:
            return {
                "reply": f"❌ Failed to save task to database: {str(e)}",
                "engine_used": "system_error",
                "suggested_actions": [{"label": "Try Again", "action": "retry"}]
            }

    # --- 2. HANDLE REAL ACTION: PLAN DAY WITH CONSTRAINTS ---
    if parsed_intent["intent"] == "plan_day":
        try:
            today_str = datetime.now().strftime("%Y-%m-%d")
            sched = execute_plan_schedule(
                fixed_blocks=parsed_intent.get("fixed_events", []),
                focus_blocks=parsed_intent.get("focus_blocks", []),
                settings=settings,
                target_date_str=today_str
            )
            # Build clean schedule breakdown string
            slot_lines = []
            for s in sched.get("slots", []):
                slot_lines.append(f"• **{s['start_time']} – {s['end_time']}**: {s['title']} ({s['duration_minutes']}m)")

            schedule_summary = "\n".join(slot_lines[:8])

            reply_text = (
                f"📅 **Custom Daily Schedule Created & Saved**\n\n"
                f"{schedule_summary}\n\n"
                f"• **Total Planned:** {sched.get('total_planned_minutes')} mins (Available: {sched.get('total_available_minutes')} mins)\n"
                f"• **Status:** {'⚠️ Overload Warning' if sched.get('is_overloaded') else '✅ Realistic & Balanced'}\n\n"
                f"Your commitments have been saved to your database and populated directly in the **AI Planner**."
            )
            return {
                "reply": reply_text,
                "engine_used": "real_action_engine",
                "suggested_actions": [
                    {"label": "Open AI Planner", "route": "planner"},
                    {"label": "View Task Queue", "route": "tasks"},
                    {"label": "Start First Sprint", "route": "focus"}
                ],
                "action_executed": {
                    "type": "schedule_updated",
                    "schedule": sched
                }
            }
        except Exception as e:
            return {
                "reply": f"❌ Failed to generate and save schedule: {str(e)}",
                "engine_used": "system_error",
                "suggested_actions": [{"label": "Open Planner", "route": "planner"}]
            }

    # --- 3. HANDLE REAL ACTION: COMPLETE TASK ---
    if parsed_intent["intent"] == "complete_task":
        completed = execute_complete_task(parsed_intent["target"])
        if completed:
            return {
                "reply": f"🎉 **Task Completed!**\n\nMarked **\"{completed['title']}\"** as complete in your database.",
                "engine_used": "real_action_engine",
                "suggested_actions": [{"label": "View Tasks", "route": "tasks"}],
                "action_executed": {"type": "task_completed", "task": completed}
            }
        else:
            return {
                "reply": f"⚠️ Could not find an active task matching \"{parsed_intent['target']}\". Check your task list in the Tasks tab.",
                "engine_used": "real_action_engine",
                "suggested_actions": [{"label": "View Tasks", "route": "tasks"}]
            }

    # --- 4. HANDLE REAL ACTION: DELETE TASK ---
    if parsed_intent["intent"] == "delete_task":
        deleted = execute_delete_task(parsed_intent["target"])
        if deleted:
            return {
                "reply": f"🗑️ **Task Deleted**\n\nSuccessfully removed **\"{deleted['title']}\"** from your database.",
                "engine_used": "real_action_engine",
                "suggested_actions": [{"label": "View Tasks", "route": "tasks"}],
                "action_executed": {"type": "task_deleted", "task_id": deleted["id"]}
            }
        else:
            return {
                "reply": f"⚠️ Could not find a task matching \"{parsed_intent['target']}\" to delete.",
                "engine_used": "real_action_engine",
                "suggested_actions": [{"label": "View Tasks", "route": "tasks"}]
            }

    # --- 5. CONVERSATIONAL / COACHING ---
    # If Gemini is configured, use real Gemini API
    if api_key:
        try:
            task_titles = [t.get("title") for t in tasks[:5]]
            system_prompt = f"""
You are AI LifePilot, an intelligent, concise, and highly actionable daily productivity coach for {user_name}.
Current user context:
- Pending tasks: {pending_count} ({overdue_count} overdue)
- Focus logged today: {focus_today} minutes
- Top queued tasks: {task_titles}
- Work hours: {settings.get('work_start_time', '09:00')} - {settings.get('work_end_time', '18:00')}

Guidelines:
1. Provide concise, direct, practical answers (max 2-3 short paragraphs).
2. Ground all advice in the user's actual pending tasks and schedule constraints.
3. If recommending focus or study, suggest specific Pomodoro sprints (25m or 50m).
4. Do not fabricate tasks or pretend external systems ran if they didn't.
"""
            reply = call_gemini(message, api_key, system_prompt, conversation_history)
            return {
                "reply": reply,
                "engine_used": "gemini",
                "suggested_actions": [
                    {"label": "View Today's Schedule", "route": "planner"},
                    {"label": "Start Focus Sprint", "route": "focus"}
                ]
            }
        except Exception as e:
            # Report the REAL error honestly to the user! Never fabricate!
            return {
                "reply": (
                    f"⚠️ **Gemini AI Service Notice**: Encountered an error contacting Google Gemini API:\n\n"
                    f"`{str(e)}`\n\n"
                    f"Please verify your API key in **Settings** or check your internet connection. You can also give me direct commands (e.g., *'Create a task to finish my project report tomorrow'* or *'Plan my day. I have classes from 9 AM to 1 PM and need two hours for Java practice'*)."
                ),
                "engine_used": "api_error_notice",
                "suggested_actions": [
                    {"label": "Open Settings", "route": "settings"},
                    {"label": "View My Tasks", "route": "tasks"}
                ]
            }

    # If Gemini API key is NOT configured, be completely honest and transparent!
    # Never return fabricated AI responses!
    top_task = tasks[0]["title"] if tasks else "no active tasks"
    return {
        "reply": (
            f"⚠️ **Google Gemini API Key Required for Live AI Coaching**\n\n"
            f"To enable live generative AI responses and contextual reasoning, please enter your Google Gemini API key in **Settings** (get a free key at [Google AI Studio](https://aistudio.google.com)).\n\n"
            f"**Your Current Workspace Snapshot:**\n"
            f"• **Active Tasks:** {pending_count} pending" + (f" ({overdue_count} overdue)" if overdue_count > 0 else "") + "\n"
            f"• **Top Priority Item:** \"{top_task}\"\n"
            f"• **Focus Logged Today:** {focus_today} minutes\n\n"
            f"💡 **Direct Commands Still Work Locally Without an API Key:**\n"
            f"• *\"Create a task to finish my project report tomorrow\"*\n"
            f"• *\"Plan my day. I have classes from 9 AM to 1 PM and need two hours for Java practice\"*\n"
            f"• *\"Mark [task name] as completed\"*"
        ),
        "engine_used": "deterministic_engine",
        "suggested_actions": [
            {"label": "Configure API Key in Settings", "route": "settings"},
            {"label": "Open AI Planner", "route": "planner"},
            {"label": "Manage Tasks", "route": "tasks"}
        ]
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
        try:
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
            raw_response = call_gemini(
                prompt,
                api_key,
                "You are an expert project manager. Return ONLY valid JSON with no markdown backticks."
            )
            # Robust JSON extraction
            match = re.search(r"\{.*\}", raw_response, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                return {
                    "goal_title": goal_title,
                    "subtasks": parsed.get("subtasks", []),
                    "engine_used": "gemini",
                    "explanation": parsed.get("explanation", "Goal structured into prioritized milestones.")
                }
        except Exception:
            pass

    # High-quality deterministic decomposition
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
