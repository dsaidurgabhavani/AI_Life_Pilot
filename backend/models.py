from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# ================= Tasks =================
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = ""
    category: str = Field("Work", description="Study, Work, Health, Personal, Finance, etc.")
    priority: str = Field("important_not_urgent", description="urgent_important, important_not_urgent, urgent_not_important, neither")
    estimated_duration: int = Field(30, ge=5, le=480, description="Duration in minutes")
    deadline: str = Field(..., description="ISO 8601 string, e.g., 2026-10-24T18:00")
    scheduled_start: Optional[str] = None
    scheduled_end: Optional[str] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None # pending, in_progress, completed
    estimated_duration: Optional[int] = None
    deadline: Optional[str] = None
    scheduled_start: Optional[str] = None
    scheduled_end: Optional[str] = None

class TaskResponse(TaskBase):
    id: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    order_index: int = 0
    is_overdue: bool = False
    time_remaining_formatted: str = ""
    urgency_level: str = "normal" # overdue, due_soon (<3 hrs), today, upcoming

# ================= Habits =================
class HabitBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = ""
    category: str = "Personal"
    frequency: str = "daily"
    target_days_per_week: int = Field(7, ge=1, le=7)
    icon: str = "sparkles"
    color: str = "#3b82f6"

class HabitCreate(HabitBase):
    pass

class HabitUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    frequency: Optional[str] = None
    target_days_per_week: Optional[int] = None
    icon: Optional[str] = None
    color: Optional[str] = None

class HabitLogDay(BaseModel):
    date: str
    day_name: str
    completed: bool

class HabitResponse(HabitBase):
    id: str
    created_at: str
    current_streak: int
    best_streak: int
    completion_rate_week: float
    history: List[HabitLogDay]
    completed_today: bool

class HabitToggleRequest(BaseModel):
    date: str # YYYY-MM-DD
    completed: Optional[bool] = None # If None, toggles current value

# ================= Focus Sessions =================
class FocusSessionCreate(BaseModel):
    task_id: Optional[str] = None
    task_title: str
    mode: str = "work" # study or work
    duration_minutes: int = Field(..., ge=1, le=180)
    notes: Optional[str] = ""

class FocusSessionResponse(BaseModel):
    id: str
    task_id: Optional[str] = None
    task_title: str
    mode: str
    duration_minutes: int
    completed_at: str
    notes: str = ""

# ================= Settings =================
class UserSettingsBase(BaseModel):
    user_name: str = "User"
    work_start_time: str = "09:00"
    work_end_time: str = "18:00"
    buffer_minutes: int = 15
    pomodoro_work_duration: int = 25
    pomodoro_break_duration: int = 5
    pomodoro_long_break_duration: int = 15
    theme: str = "light"
    notifications_enabled: bool = True
    ai_provider: str = "auto"
    gemini_api_key: Optional[str] = ""

class UserSettingsResponse(UserSettingsBase):
    pass

class UserSettingsUpdate(BaseModel):
    user_name: Optional[str] = None
    work_start_time: Optional[str] = None
    work_end_time: Optional[str] = None
    buffer_minutes: Optional[int] = None
    pomodoro_work_duration: Optional[int] = None
    pomodoro_break_duration: Optional[int] = None
    pomodoro_long_break_duration: Optional[int] = None
    theme: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    ai_provider: Optional[str] = None
    gemini_api_key: Optional[str] = None

# ================= Planner / Timeline =================
class ScheduleSlot(BaseModel):
    id: str
    task_id: Optional[str] = None
    title: str
    start_time: str # "09:00"
    end_time: str   # "09:45"
    duration_minutes: int
    category: str
    priority: str
    is_buffer: bool = False
    is_break: bool = False
    status: str = "pending"

class DailyScheduleResponse(BaseModel):
    date: str
    work_start_time: str
    work_end_time: str
    total_planned_minutes: int
    total_available_minutes: int
    is_overloaded: bool
    overload_minutes: int
    slots: List[ScheduleSlot]
    suggestions: List[str]
    engine_used: str # "gemini" | "smart_heuristic" | "deterministic"

class ScheduleReorderSlot(BaseModel):
    task_id: str
    scheduled_start: str
    scheduled_end: str

class ScheduleReorderRequest(BaseModel):
    slots: List[ScheduleReorderSlot]

# ================= AI Assistant =================
class ChatMessageRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = []

class ChatMessageResponse(BaseModel):
    reply: str
    engine_used: str # "gemini" | "smart_heuristic" | "deterministic_engine"
    suggested_actions: List[Dict[str, Any]] = []
    action_executed: Optional[Dict[str, Any]] = None

class ChatMessageRecord(BaseModel):
    id: str
    sender: str
    text: str
    timestamp: str
    engine_used: Optional[str] = ""
    suggested_actions: List[Dict[str, Any]] = []
    created_at: str

class GoalBreakdownRequest(BaseModel):
    goal_title: str
    target_deadline: Optional[str] = None
    category: Optional[str] = "Study"

class SubtaskItem(BaseModel):
    title: str
    description: str
    category: str
    priority: str
    estimated_duration: int
    suggested_day_offset: int # 0 for today, 1 for tomorrow, etc.

class GoalBreakdownResponse(BaseModel):
    goal_title: str
    subtasks: List[SubtaskItem]
    engine_used: str
    explanation: str

# ================= Analytics & Insights =================
class CategoryBreakdown(BaseModel):
    category: str
    count: int
    minutes: int

class DailyCompletionPoint(BaseModel):
    day: str # "Mon", "Tue"
    date: str
    completed: int
    focus_minutes: int

class AnalyticsOverviewResponse(BaseModel):
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    overdue_tasks: int
    completion_rate_percent: float
    total_focus_minutes: int
    study_focus_minutes: int
    work_focus_minutes: int
    active_habits_count: int
    overall_habit_consistency_percent: float
    productivity_score: int # 0 - 100
    category_distribution: List[CategoryBreakdown]
    weekly_trend: List[DailyCompletionPoint]
    smart_insights: List[str]
