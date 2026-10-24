from datetime import datetime, timedelta
from fastapi import APIRouter
from database import get_connection
from models import AnalyticsOverviewResponse, CategoryBreakdown, DailyCompletionPoint
from routers.tasks import enrich_task_dict

router = APIRouter(prefix="/api/analytics", tags=["Productivity Analytics"])

@router.get("/overview", response_model=AnalyticsOverviewResponse)
def get_analytics_overview():
    conn = get_connection()
    cursor = conn.cursor()

    # Tasks stats
    cursor.execute("SELECT * FROM tasks")
    all_tasks = [enrich_task_dict(dict(r)) for r in cursor.fetchall()]

    total_tasks = len(all_tasks)
    completed_tasks = sum(1 for t in all_tasks if t["status"] == "completed")
    pending_tasks = sum(1 for t in all_tasks if t["status"] in ["pending", "in_progress"])
    overdue_tasks = sum(1 for t in all_tasks if t["is_overdue"])

    completion_rate = round((completed_tasks / total_tasks * 100.0), 1) if total_tasks > 0 else 0.0

    # Focus minutes
    cursor.execute("SELECT COALESCE(SUM(duration_minutes), 0) FROM focus_sessions")
    total_focus_mins = cursor.fetchone()[0]

    cursor.execute("SELECT mode, COALESCE(SUM(duration_minutes), 0) FROM focus_sessions GROUP BY mode")
    mode_map = {r[0]: r[1] for r in cursor.fetchall()}
    study_focus_mins = mode_map.get("study", 0)
    work_focus_mins = mode_map.get("work", 0)

    # Habits stats
    cursor.execute("SELECT COUNT(*) FROM habits")
    active_habits_count = cursor.fetchone()[0]

    # Calculate overall habit consistency for past 7 days
    now = datetime.now()
    seven_days_ago_str = (now - timedelta(days=6)).strftime("%Y-%m-%d")
    cursor.execute("""
    SELECT COUNT(*) FROM habit_logs 
    WHERE completed = 1 AND log_date >= ?
    """, (seven_days_ago_str,))
    completed_habit_logs_count = cursor.fetchone()[0]
    total_possible_habit_logs = max(1, active_habits_count * 7)
    habit_consistency = round((completed_habit_logs_count / total_possible_habit_logs) * 100.0, 1)

    # Category distribution
    cat_counts = {}
    cat_minutes = {}
    for t in all_tasks:
        c = t.get("category", "General")
        cat_counts[c] = cat_counts.get(c, 0) + 1
        cat_minutes[c] = cat_minutes.get(c, 0) + t.get("estimated_duration", 30)

    category_distribution = [
        CategoryBreakdown(category=k, count=v, minutes=cat_minutes.get(k, 0))
        for k, v in cat_counts.items()
    ]

    # Weekly trend (past 7 days)
    weekly_trend = []
    for i in range(6, -1, -1):
        day_date = now - timedelta(days=i)
        day_str = day_date.strftime("%Y-%m-%d")
        day_label = day_date.strftime("%a")

        # tasks completed on this date
        completed_on_day = sum(
            1 for t in all_tasks 
            if t.get("completed_at") and t["completed_at"].startswith(day_str)
        )

        # focus on this date
        cursor.execute("""
        SELECT COALESCE(SUM(duration_minutes), 0) FROM focus_sessions 
        WHERE completed_at LIKE ?
        """, (f"{day_str}%",))
        f_mins = cursor.fetchone()[0]

        weekly_trend.append(DailyCompletionPoint(
            day=day_label,
            date=day_str,
            completed=completed_on_day,
            focus_minutes=f_mins
        ))

    conn.close()

    # Productivity Score (0 - 100) formula:
    # 40% task completion rate + 30% habit consistency + 30% focus time achieved vs 120m target - 10 penalty per overdue
    focus_target_mins = 120
    focus_score = min(100.0, (total_focus_mins / focus_target_mins) * 100.0) if total_focus_mins > 0 else 20.0
    raw_score = (completion_rate * 0.4) + (habit_consistency * 0.3) + (focus_score * 0.3) - (overdue_tasks * 8)
    productivity_score = max(5, min(100, int(round(raw_score))))

    # Dynamic Smart Insights based on actual data
    smart_insights = []
    if overdue_tasks > 0:
        smart_insights.append(
            f"🚨 Priority Bottleneck: You have {overdue_tasks} overdue task(s). Completing or rescheduling them will boost your score by {overdue_tasks * 8} points."
        )
    else:
        smart_insights.append(
            "🌟 Clean Radar: Zero overdue tasks! You are maintaining excellent deadline discipline."
        )

    if total_focus_mins >= 90:
        smart_insights.append(
            f"🔥 Deep Work Momentum: Logged {total_focus_mins} minutes of focused study and work sessions."
        )
    else:
        smart_insights.append(
            "⏱ Focus Boost: Consider initiating a 25-minute Pomodoro sprint to cross today's focus threshold."
        )

    if habit_consistency >= 75.0:
        smart_insights.append(
            f"💪 Strong Habit Chain: Your weekly habit consistency is {habit_consistency}%, reflecting strong long-term momentum."
        )
    else:
        smart_insights.append(
            f"📈 Habit Opportunity: Weekly habit consistency stands at {habit_consistency}%. Checking off today's habits will reinforce your streak."
        )

    return AnalyticsOverviewResponse(
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        overdue_tasks=overdue_tasks,
        completion_rate_percent=completion_rate,
        total_focus_minutes=total_focus_mins,
        study_focus_minutes=study_focus_mins,
        work_focus_minutes=work_focus_mins,
        active_habits_count=active_habits_count,
        overall_habit_consistency_percent=habit_consistency,
        productivity_score=productivity_score,
        category_distribution=category_distribution,
        weekly_trend=weekly_trend,
        smart_insights=smart_insights
    )
