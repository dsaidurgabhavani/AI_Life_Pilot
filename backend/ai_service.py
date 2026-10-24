import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

def get_api_key(db_key: str = "") -> str:
    # First check env var, then db key
    env_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if env_key:
        return env_key
    if db_key and db_key.strip():
        return db_key.strip()
    return ""

def call_gemini(prompt: str, api_key: str, system_instruction: str = "") -> str:
    if not api_key:
        raise ValueError("No Gemini API key provided")
    
    url = f"{GEMINI_ENDPOINT}?key={api_key}"
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 1024
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
    
    with urllib.request.urlopen(req, timeout=12) as response:
        result = json.loads(response.read().decode("utf-8"))
        candidates = result.get("candidates", [])
        if candidates and "content" in candidates[0]:
            parts = candidates[0]["content"].get("parts", [])
            if parts and "text" in parts[0]:
                return parts[0]["text"]
    raise RuntimeError("Empty response from Gemini API")


# ================= RULE-BASED SCHEDULING ENGINE =================

def parse_time_to_minutes(time_str: str) -> int:
    parts = time_str.split(":")
    return int(parts[0]) * 60 + int(parts[1])

def minutes_to_time_str(minutes: int) -> str:
    h = (minutes // 60) % 24
    m = minutes % 60
    return f"{h:02d}:{m:02d}"

def calculate_priority_score(task: Dict[str, Any], current_dt: datetime) -> float:
    score = 0.0
    priority = task.get("priority", "important_not_urgent")
    
    # Eisenhower Matrix weight
    if priority == "urgent_important":
        score += 600
    elif priority == "important_not_urgent":
        score += 350
    elif priority == "urgent_not_important":
        score += 200
    else: # neither
        score += 80

    # Deadline proximity
    deadline_str = task.get("deadline", "")
    if deadline_str:
        try:
            # support formats like YYYY-MM-DDTHH:MM or YYYY-MM-DDTHH:MM:SS
            clean_str = deadline_str[:16]
            dl = datetime.fromisoformat(clean_str)
            hours_diff = (dl - current_dt).total_seconds() / 3600.0

            if hours_diff < 0: # Overdue!
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

    # Status bonus: in_progress tasks should stay near top
    if task.get("status") == "in_progress":
        score += 400

    return score

def generate_daily_schedule(
    tasks: List[Dict[str, Any]],
    settings: Dict[str, Any],
    target_date_str: str,
    gemini_key: str = ""
) -> Dict[str, Any]:
    """
    Builds a realistic daily schedule based on task importance, available time, and deadlines.
    Works either with Gemini or with the deterministic Smart Heuristic Engine.
    """
    now = datetime.now()
    work_start = settings.get("work_start_time", "09:00")
    work_end = settings.get("work_end_time", "18:00")
    buffer_mins = settings.get("buffer_minutes", 15)

    start_mins = parse_time_to_minutes(work_start)
    end_mins = parse_time_to_minutes(work_end)
    total_available_mins = max(0, end_mins - start_mins)

    # Filter eligible tasks (pending or in_progress, or scheduled for today)
    eligible_tasks = [
        t for t in tasks 
        if t.get("status") != "completed"
    ]

    # Calculate total duration needed
    total_task_mins = sum(t.get("estimated_duration", 30) for t in eligible_tasks)
    # Estimate buffer time
    estimated_buffer_mins = max(0, (len(eligible_tasks) - 1) * buffer_mins) if eligible_tasks else 0
    total_planned_mins = total_task_mins + estimated_buffer_mins

    is_overloaded = total_planned_mins > total_available_mins
    overload_mins = max(0, total_planned_mins - total_available_mins)

    # Sort tasks by productivity score
    scored_tasks = []
    for t in eligible_tasks:
        score = calculate_priority_score(t, now)
        scored_tasks.append((score, t))
    
    scored_tasks.sort(key=lambda x: x[0], reverse=True)
    sorted_tasks = [item[1] for item in scored_tasks]

    # Time slot allocation
    slots = []
    current_time_ptr = start_mins

    # Lunch break indicator (around 12:30 - 13:15 if span covers it)
    lunch_start = 12 * 60 + 30
    lunch_duration = 45
    lunch_added = False

    for idx, task in enumerate(sorted_tasks):
        # Insert lunch if reaching midday
        if not lunch_added and current_time_ptr >= lunch_start and current_time_ptr < (lunch_start + 60):
            slots.append({
                "id": f"slot-lunch-{idx}",
                "task_id": None,
                "title": "🥗 Lunch & Mental Recharge Break",
                "start_time": minutes_to_time_str(current_time_ptr),
                "end_time": minutes_to_time_str(current_time_ptr + lunch_duration),
                "duration_minutes": lunch_duration,
                "category": "Health",
                "priority": "important_not_urgent",
                "is_buffer": False,
                "is_break": True,
                "status": "pending"
            })
            current_time_ptr += lunch_duration
            lunch_added = True

        duration = task.get("estimated_duration", 30)
        slot_start = current_time_ptr
        slot_end = current_time_ptr + duration

        slots.append({
            "id": f"slot-task-{task['id']}",
            "task_id": task["id"],
            "title": task["title"],
            "start_time": minutes_to_time_str(slot_start),
            "end_time": minutes_to_time_str(slot_end),
            "duration_minutes": duration,
            "category": task.get("category", "Work"),
            "priority": task.get("priority", "important_not_urgent"),
            "is_buffer": False,
            "is_break": False,
            "status": task.get("status", "pending")
        })

        current_time_ptr = slot_end

        # Add buffer between tasks if not last task
        if idx < len(sorted_tasks) - 1 and buffer_mins > 0:
            slots.append({
                "id": f"slot-buffer-{idx}",
                "task_id": None,
                "title": f"⏱ Buffer & Context Shift ({buffer_mins}m)",
                "start_time": minutes_to_time_str(current_time_ptr),
                "end_time": minutes_to_time_str(current_time_ptr + buffer_mins),
                "duration_minutes": buffer_mins,
                "category": "Personal",
                "priority": "neither",
                "is_buffer": True,
                "is_break": False,
                "status": "pending"
            })
            current_time_ptr += buffer_mins

    # Generate practical suggestions
    suggestions = []
    if is_overloaded:
        suggestions.append(
            f"⚠️ Schedule overload detected: Planned activities exceed available hours by {overload_mins} minutes."
        )
        # Find non-urgent tasks that can be deferred
        deferrable = [t for t in sorted_tasks if t.get("priority") in ["urgent_not_important", "neither"]]
        if deferrable:
            task_titles = '", "'.join([t["title"] for t in deferrable[:2]])
            suggestions.append(
                f"Reschedule lower-priority tasks: Consider moving \"{task_titles}\" to tomorrow to recover focus headroom."
            )
        else:
            suggestions.append(
                "Timebox large tasks: Split deep work sessions into 30-minute high-focus blocks with strict stopping criteria."
            )
        suggestions.append(
            f"Reduce buffer overhead or extend your work window past {work_end} if submitting hard deadlines today."
        )
    else:
        slack = total_available_mins - total_planned_mins
        suggestions.append(
            f"✅ Realistic workload: You have {slack} minutes of remaining buffer time today for emergent tasks."
        )
        suggestions.append(
            "Tackle your Most Important Task (MIT) first thing in the morning when mental energy is at its peak."
        )

    engine_used = "smart_heuristic"

    # Try Gemini enhancement if API key is present
    api_key = get_api_key(gemini_key)
    if api_key:
        try:
            prompt = f"""
Given this daily task list: {[t['title'] + ' (' + str(t.get('estimated_duration',30)) + 'm, ' + t.get('priority','') + ')' for t in sorted_tasks]}
Working hours: {work_start} to {work_end} ({total_available_mins} mins).
Total planned: {total_planned_mins} mins.
Provide 2 short, highly specific, practical productivity recommendations for this exact schedule.
Keep it strictly under 3 sentences total.
"""
            ai_tips = call_gemini(prompt, api_key, "You are AI LifePilot, an elite executive productivity coach.")
            if ai_tips and len(ai_tips.strip()) > 10:
                lines = [line.strip("- *• ") for line in ai_tips.split("\n") if line.strip()]
                if lines:
                    suggestions = lines[:3]
                engine_used = "gemini"
        except Exception:
            # Safe fallback without pretending
            engine_used = "smart_heuristic"

    return {
        "date": target_date_str,
        "work_start_time": work_start,
        "work_end_time": work_end,
        "total_planned_minutes": total_planned_mins,
        "total_available_minutes": total_available_mins,
        "is_overloaded": is_overloaded,
        "overload_minutes": overload_mins,
        "slots": slots,
        "suggestions": suggestions,
        "engine_used": engine_used
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

Break this large goal into 4 to 5 concrete, actionable, bite-sized tasks.
Return ONLY valid JSON in this exact structure:
{{
  "explanation": "Short 1-2 sentence strategy explanation",
  "subtasks": [
    {{
      "title": "Subtask title",
      "description": "Clear action to take",
      "category": "{category}",
      "priority": "urgent_important" or "important_not_urgent",
      "estimated_duration": 30 to 60 (integer minutes),
      "suggested_day_offset": 0 for today, 1 for tomorrow, etc.
    }}
  ]
}}
"""
            raw_response = call_gemini(prompt, api_key, "You are an expert project manager and cognitive planning assistant. Return only valid JSON.")
            clean_json = raw_response.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:]
            if clean_json.endswith("```"):
                clean_json = clean_json[:-3]
            clean_json = clean_json.strip()

            parsed = json.loads(clean_json)
            return {
                "goal_title": goal_title,
                "subtasks": parsed.get("subtasks", []),
                "engine_used": "gemini",
                "explanation": parsed.get("explanation", "Goal structured into prioritized milestones.")
            }
        except Exception:
            pass # Fall through to heuristic

    # Smart Rule-Based Decomposition
    lower = goal_title.lower()
    subtasks = []

    if any(k in lower for k in ["exam", "test", "study", "chapter", "course", "learn", "revision"]):
        subtasks = [
            {
                "title": f"Review key syllabus concepts for {goal_title[:30]}",
                "description": "Skim chapter headings, lecture slides, and highlight core formulas or theorems.",
                "category": "Study",
                "priority": "urgent_important",
                "estimated_duration": 45,
                "suggested_day_offset": 0
            },
            {
                "title": "Create 1-page condensed summary cheat sheet",
                "description": "Synthesize notes, definitions, and edge cases into an active recall map.",
                "category": "Study",
                "priority": "important_not_urgent",
                "estimated_duration": 60,
                "suggested_day_offset": 1
            },
            {
                "title": "Complete 3 practice problems / past exam questions",
                "description": "Timed simulation without referring to solution manuals.",
                "category": "Study",
                "priority": "urgent_important",
                "estimated_duration": 50,
                "suggested_day_offset": 1
            },
            {
                "title": "Targeted review of weak topics & flashcard quiz",
                "description": "Re-solve missed questions and clarify misconceptions.",
                "category": "Study",
                "priority": "important_not_urgent",
                "estimated_duration": 35,
                "suggested_day_offset": 2
            }
        ]
        explanation = "Structured 3-phase study roadmap: Survey -> Active Synthesis -> Practice Testing."
    elif any(k in lower for k in ["code", "app", "project", "build", "develop", "api", "software"]):
        subtasks = [
            {
                "title": f"Draft technical requirements & schema for {goal_title[:30]}",
                "description": "Outline core endpoints, data models, and user workflow wireframe.",
                "category": "Work",
                "priority": "urgent_important",
                "estimated_duration": 40,
                "suggested_day_offset": 0
            },
            {
                "title": "Scaffold repository and implement core backend logic",
                "description": "Build models, validation schemas, and database persistence layer.",
                "category": "Work",
                "priority": "urgent_important",
                "estimated_duration": 60,
                "suggested_day_offset": 0
            },
            {
                "title": "Build responsive user interface components",
                "description": "Connect frontend views with API endpoints and handle loading/empty states.",
                "category": "Work",
                "priority": "important_not_urgent",
                "estimated_duration": 60,
                "suggested_day_offset": 1
            },
            {
                "title": "Integration testing, error edge-cases, and documentation",
                "description": "Verify user flow, test validation rules, and write quick start guide.",
                "category": "Work",
                "priority": "important_not_urgent",
                "estimated_duration": 45,
                "suggested_day_offset": 2
            }
        ]
        explanation = "Agile development sprint: Architecture -> MVP Backend -> UI Layer -> Quality Assurance."
    elif any(k in lower for k in ["presentation", "slides", "pitch", "demo", "meeting"]):
        subtasks = [
            {
                "title": f"Outline narrative story arc for {goal_title[:30]}",
                "description": "Define the problem, core solution, key benefits, and call to action.",
                "category": "Work",
                "priority": "urgent_important",
                "estimated_duration": 30,
                "suggested_day_offset": 0
            },
            {
                "title": "Design 6-8 polished visual slides",
                "description": "Add concise bullet points, diagrams, and clear typography without clutter.",
                "category": "Work",
                "priority": "urgent_important",
                "estimated_duration": 50,
                "suggested_day_offset": 1
            },
            {
                "title": "Dry run rehearsal & timing check",
                "description": "Speak through slides aloud twice and identify transition bottlenecks.",
                "category": "Work",
                "priority": "important_not_urgent",
                "estimated_duration": 25,
                "suggested_day_offset": 1
            }
        ]
        explanation = "High-impact presentation roadmap: Storyline -> Deck Polish -> Live Rehearsal."
    else: # Generic productive breakdown
        subtasks = [
            {
                "title": f"Define scope and success criteria for {goal_title[:30]}",
                "description": "List exact deliverables and eliminate ambiguous requirements.",
                "category": category,
                "priority": "urgent_important",
                "estimated_duration": 30,
                "suggested_day_offset": 0
            },
            {
                "title": "Execute first 50% milestone (High-impact groundwork)",
                "description": "Focus unbroken attention on the single hardest component.",
                "category": category,
                "priority": "urgent_important",
                "estimated_duration": 60,
                "suggested_day_offset": 0
            },
            {
                "title": "Complete remaining deliverables & review",
                "description": "Wrap up secondary elements and refine against criteria.",
                "category": category,
                "priority": "important_not_urgent",
                "estimated_duration": 45,
                "suggested_day_offset": 1
            },
            {
                "title": "Final polish, verification, and submission",
                "description": "Check details, verify deadlines, and mark deliverable complete.",
                "category": category,
                "priority": "important_not_urgent",
                "estimated_duration": 25,
                "suggested_day_offset": 1
            }
        ]
        explanation = "Iterative milestone breakdown: Scope Definition -> Core Deep Work -> Polish -> Final QA."

    return {
        "goal_title": goal_title,
        "subtasks": subtasks,
        "engine_used": "smart_heuristic",
        "explanation": explanation
    }


# ================= CONVERSATIONAL ASSISTANT =================

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
    user_name = context.get("user_name", "Alex")

    # If Gemini is configured, use it
    if api_key:
        try:
            system_prompt = f"""
You are AI LifePilot, an intelligent, empathetic, and highly actionable daily productivity coach for {user_name}.
Current user context:
- Pending tasks: {pending_count}
- Overdue tasks: {overdue_count}
- Focus time logged today: {focus_today} minutes
- Key pending tasks: {[t.get('title') for t in tasks[:4]]}

Instructions:
1. Provide concise, direct, motivating advice (max 3 paragraphs).
2. Recommend concrete ways to tackle overloaded schedules or break down obstacles.
3. Suggest the Pomodoro technique or timeboxing when users feel overwhelmed.
4. Keep tone professional, supportive, and action-oriented.
"""
            reply = call_gemini(message, api_key, system_prompt)
            return {
                "reply": reply,
                "engine_used": "gemini",
                "suggested_actions": [
                    {"label": "View Today's Schedule", "route": "/planner"},
                    {"label": "Start Focus Session", "route": "/focus"}
                ]
            }
        except Exception:
            pass # Fall through to smart rule-based conversational assistant

    # Rule-Based Intelligent Conversational Assistant
    lower = message.lower()
    
    suggested_actions = []

    if any(k in lower for k in ["overload", "overwhelmed", "too much", "stressed", "cannot finish", "busy"]):
        reply = (
            f"Take a deep breath, {user_name}. Feeling overloaded happens when everything feels equally urgent. "
            f"Right now you have {pending_count} pending tasks" + 
            (f", including {overdue_count} that are overdue." if overdue_count > 0 else ".") + "\n\n"
            "Here is the LifePilot 3-Step Relief Protocol:\n"
            "1. **Ruthless Elimination:** Pick the single task that would make today a win if nothing else got done. This is your Most Important Task (MIT).\n"
            "2. **Defer or Timebox:** Defer non-urgent tasks to tomorrow. Lower-priority items can safely wait.\n"
            "3. **25-Minute Rule:** Don't think about the whole day. Set a 25-minute Pomodoro timer on your top task and commit to working until the chime."
        )
        suggested_actions = [
            {"label": "Regenerate Balanced Schedule", "route": "/planner"},
            {"label": "Launch 25m Focus Session", "route": "/focus"}
        ]
    elif any(k in lower for k in ["break", "break down", "goal", "large", "project", "subtask"]):
        reply = (
            "Breaking large goals into bite-sized actions is the best cure for procrastination!\n\n"
            "A well-structured subtask should be:\n"
            "- **Specific:** Describes a physical action (e.g., 'Draft 3 outline points' instead of 'Work on paper').\n"
            "- **Short:** Can be completed in 25 to 50 minutes.\n"
            "- **Independent:** Can be started immediately without waiting for complex approvals.\n\n"
            "💡 You can use the **Breakdown Goal** feature below or tell me the exact goal you want to decompose!"
        )
        suggested_actions = [
            {"label": "Break Down a Goal", "action": "open_breakdown_modal"},
            {"label": "Go to Tasks", "route": "/tasks"}
        ]
    elif any(k in lower for k in ["focus", "pomodoro", "study", "work mode", "timer", "distract"]):
        reply = (
            f"Focused attention is your highest-leverage asset. You have logged {focus_today} minutes of deep focus today!\n\n"
            "Recommended Flow for Deep Work:\n"
            "• **Work Session:** 25 or 50 minutes of single-tasking (close social media, silence notifications).\n"
            "• **Short Break:** 5 to 10 minutes (step away from screens, stretch, drink water).\n"
            "• **Long Break:** After 4 cycles, take a 20-minute walk to reset dopamine levels."
        )
        suggested_actions = [
            {"label": "Start Pomodoro Timer", "route": "/focus"},
            {"label": "View Focus Analytics", "route": "/analytics"}
        ]
    elif any(k in lower for k in ["habit", "routine", "streak", "consistency"]):
        reply = (
            "Consistency compounds faster than intensity! "
            "The secret to building lasting habits is lowering the friction of starting.\n\n"
            "Key Habit Principles:\n"
            "1. **Never Miss Twice:** If you miss a day, prioritize showing up the next day, even for just 2 minutes.\n"
            "2. **Habit Stacking:** Anchor your new habit to an existing routine (e.g., 'After I pour my morning coffee, I will review today's schedule').\n"
            "3. **Track Visual Streaks:** Seeing an unbroken chain triggers the psychology of momentum."
        )
        suggested_actions = [
            {"label": "Check Habit Tracker", "route": "/habits"},
            {"label": "View Consistency Trends", "route": "/analytics"}
        ]
    elif any(k in lower for k in ["schedule", "plan", "timeline", "today", "calendar"]):
        reply = (
            f"Here is your daily planning snapshot, {user_name}:\n"
            f"- You have **{pending_count} active tasks** queued." +
            (f" ⚠️ **{overdue_count} task(s) are currently overdue** and require immediate resolution." if overdue_count > 0 else " All deadlines are on schedule!") + "\n\n"
            "LifePilot organizes your schedule using the Eisenhower Matrix combined with deadline proximity and built-in buffer slots to prevent burnout.\n"
            "Head over to the AI Planner to view your interactive visual timeline or generate an optimized schedule."
        )
        suggested_actions = [
            {"label": "Open AI Planner", "route": "/planner"},
            {"label": "Review My Tasks", "route": "/tasks"}
        ]
    else:
        top_task_title = tasks[0].get("title", "your highest priority task") if tasks else "your priority project"
        reply = (
            f"Hello {user_name}! I am AI LifePilot, your intelligent productivity and daily life assistant.\n\n"
            f"Currently you have {pending_count} pending tasks and {overdue_count} overdue items. "
            f"I recommend giving your primary attention to: **\"{top_task_title}\"**.\n\n"
            "How can I assist you right now? You can ask me to:\n"
            "• Optimize your daily schedule for available hours\n"
            "• Decompose a daunting goal into bite-sized steps\n"
            "• Suggest strategies to overcome study or work fatigue\n"
            "• Guide you through a focused Pomodoro work sprint"
        )
        suggested_actions = [
            {"label": "View Today's Plan", "route": "/planner"},
            {"label": "Start Focus Sprint", "route": "/focus"},
            {"label": "Decompose Goal", "action": "open_breakdown_modal"}
        ]

    return {
        "reply": reply,
        "engine_used": "smart_heuristic",
        "suggested_actions": suggested_actions
    }
