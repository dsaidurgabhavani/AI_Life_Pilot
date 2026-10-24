import uuid
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, HTTPException
from database import get_connection
from models import HabitCreate, HabitUpdate, HabitResponse, HabitToggleRequest, HabitLogDay

router = APIRouter(prefix="/api/habits", tags=["Habit Tracker"])

def compute_streaks_and_history(cursor, habit_id: str, today: datetime):
    # Fetch all logs for this habit sorted by date descending
    cursor.execute("""
    SELECT log_date, completed FROM habit_logs 
    WHERE habit_id = ? AND completed = 1
    ORDER BY log_date DESC
    """, (habit_id,))
    completed_rows = cursor.fetchall()
    completed_dates = {row["log_date"] for row in completed_rows}

    today_str = today.strftime("%Y-%m-%d")
    completed_today = today_str in completed_dates

    # Calculate Current Streak
    # If completed today, streak starts from today; if not yet completed today, check if yesterday was completed
    current_streak = 0
    check_day = today
    if today_str not in completed_dates:
        # Check yesterday
        yesterday_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        if yesterday_str in completed_dates:
            check_day = today - timedelta(days=1)
        else:
            current_streak = 0
            check_day = None

    if check_day is not None:
        while True:
            d_str = check_day.strftime("%Y-%m-%d")
            if d_str in completed_dates:
                current_streak += 1
                check_day -= timedelta(days=1)
            else:
                break

    # Calculate Best Streak (all-time)
    best_streak = current_streak
    sorted_dates = sorted([datetime.strptime(d, "%Y-%m-%d") for d in completed_dates])
    if sorted_dates:
        temp_streak = 1
        for i in range(1, len(sorted_dates)):
            if sorted_dates[i] - sorted_dates[i-1] == timedelta(days=1):
                temp_streak += 1
            elif sorted_dates[i] - sorted_dates[i-1] > timedelta(days=1):
                temp_streak = 1
            if temp_streak > best_streak:
                best_streak = temp_streak

    # 7-day history matrix (6 days ago through today)
    history = []
    completed_count_7d = 0
    for offset in range(6, -1, -1):
        day_dt = today - timedelta(days=offset)
        d_str = day_dt.strftime("%Y-%m-%d")
        is_done = d_str in completed_dates
        if is_done:
            completed_count_7d += 1
        history.append(HabitLogDay(
            date=d_str,
            day_name=day_dt.strftime("%a"),
            completed=is_done
        ))

    completion_rate_week = round((completed_count_7d / 7.0) * 100.0, 1)

    return current_streak, best_streak, completion_rate_week, history, completed_today

@router.get("", response_model=List[HabitResponse])
def get_habits():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM habits ORDER BY created_at ASC")
    habit_rows = cursor.fetchall()

    today = datetime.now()
    results = []

    for r in habit_rows:
        h = dict(r)
        current_streak, best_streak, rate, history, done_today = compute_streaks_and_history(cursor, h["id"], today)
        results.append(HabitResponse(
            id=h["id"],
            title=h["title"],
            description=h.get("description", ""),
            category=h.get("category", "Personal"),
            frequency=h.get("frequency", "daily"),
            target_days_per_week=h.get("target_days_per_week", 7),
            icon=h.get("icon", "sparkles"),
            color=h.get("color", "#3b82f6"),
            created_at=h["created_at"],
            current_streak=current_streak,
            best_streak=best_streak,
            completion_rate_week=rate,
            history=history,
            completed_today=done_today
        ))

    conn.close()
    return results

@router.post("", response_model=HabitResponse)
def create_habit(habit_in: HabitCreate):
    conn = get_connection()
    cursor = conn.cursor()

    habit_id = f"habit-{uuid.uuid4().hex[:8]}"
    now_iso = datetime.now().isoformat()

    cursor.execute("""
    INSERT INTO habits (id, title, description, category, frequency, target_days_per_week, icon, color, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        habit_id,
        habit_in.title,
        habit_in.description or "",
        habit_in.category,
        habit_in.frequency,
        habit_in.target_days_per_week,
        habit_in.icon,
        habit_in.color,
        now_iso
    ))
    conn.commit()

    today = datetime.now()
    current_streak, best_streak, rate, history, done_today = compute_streaks_and_history(cursor, habit_id, today)
    conn.close()

    return HabitResponse(
        id=habit_id,
        title=habit_in.title,
        description=habit_in.description or "",
        category=habit_in.category,
        frequency=habit_in.frequency,
        target_days_per_week=habit_in.target_days_per_week,
        icon=habit_in.icon,
        color=habit_in.color,
        created_at=now_iso,
        current_streak=current_streak,
        best_streak=best_streak,
        completion_rate_week=rate,
        history=history,
        completed_today=done_today
    )

@router.post("/{habit_id}/toggle", response_model=HabitResponse)
def toggle_habit_day(habit_id: str, toggle_req: HabitToggleRequest):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM habits WHERE id = ?", (habit_id,))
    habit_row = cursor.fetchone()
    if not habit_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Habit not found")

    date_str = toggle_req.date

    # Check if entry exists
    cursor.execute("SELECT completed FROM habit_logs WHERE habit_id = ? AND log_date = ?", (habit_id, date_str))
    existing = cursor.fetchone()

    new_val = 1
    if existing:
        if toggle_req.completed is not None:
            new_val = 1 if toggle_req.completed else 0
        else:
            new_val = 0 if existing["completed"] == 1 else 1

        cursor.execute("UPDATE habit_logs SET completed = ? WHERE habit_id = ? AND log_date = ?", (new_val, habit_id, date_str))
    else:
        log_id = f"hl-{uuid.uuid4().hex[:8]}"
        cursor.execute("""
        INSERT INTO habit_logs (id, habit_id, log_date, completed)
        VALUES (?, ?, ?, ?)
        """, (log_id, habit_id, date_str, new_val))

    conn.commit()

    today = datetime.now()
    current_streak, best_streak, rate, history, done_today = compute_streaks_and_history(cursor, habit_id, today)
    conn.close()

    h = dict(habit_row)
    return HabitResponse(
        id=h["id"],
        title=h["title"],
        description=h.get("description", ""),
        category=h.get("category", "Personal"),
        frequency=h.get("frequency", "daily"),
        target_days_per_week=h.get("target_days_per_week", 7),
        icon=h.get("icon", "sparkles"),
        color=h.get("color", "#3b82f6"),
        created_at=h["created_at"],
        current_streak=current_streak,
        best_streak=best_streak,
        completion_rate_week=rate,
        history=history,
        completed_today=done_today
    )

@router.patch("/{habit_id}", response_model=HabitResponse)
def update_habit(habit_id: str, updates: HabitUpdate):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM habits WHERE id = ?", (habit_id,))
    habit_row = cursor.fetchone()
    if not habit_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Habit not found")

    update_data = updates.model_dump(exclude_unset=True)
    if update_data:
        fields = [f"{k} = ?" for k in update_data.keys()]
        values = list(update_data.values())
        values.append(habit_id)
        cursor.execute(f"UPDATE habits SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()

    cursor.execute("SELECT * FROM habits WHERE id = ?", (habit_id,))
    updated_row = cursor.fetchone()
    today = datetime.now()
    current_streak, best_streak, rate, history, done_today = compute_streaks_and_history(cursor, habit_id, today)
    conn.close()

    h = dict(updated_row)
    return HabitResponse(
        id=h["id"],
        title=h["title"],
        description=h.get("description", ""),
        category=h.get("category", "Personal"),
        frequency=h.get("frequency", "daily"),
        target_days_per_week=h.get("target_days_per_week", 7),
        icon=h.get("icon", "sparkles"),
        color=h.get("color", "#3b82f6"),
        created_at=h["created_at"],
        current_streak=current_streak,
        best_streak=best_streak,
        completion_rate_week=rate,
        history=history,
        completed_today=done_today
    )

@router.delete("/{habit_id}")
def delete_habit(habit_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
    conn.commit()
    conn.close()
    return {"message": "Habit deleted successfully", "id": habit_id}
