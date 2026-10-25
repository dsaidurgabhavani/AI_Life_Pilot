export type Category = 'Study' | 'Work' | 'Health' | 'Personal' | 'Finance' | 'General';

export type Priority = 'urgent_important' | 'important_not_urgent' | 'urgent_not_important' | 'neither';

export type TaskStatus = 'pending' | 'in_progress' | 'completed';

export type UrgencyLevel = 'overdue' | 'urgent' | 'today' | 'upcoming' | 'completed' | 'normal';

export interface Task {
  id: string;
  title: string;
  description: string;
  category: Category;
  priority: Priority;
  status: TaskStatus;
  estimated_duration: number; // in minutes
  deadline: string; // ISO string
  scheduled_start?: string | null;
  scheduled_end?: string | null;
  created_at: string;
  completed_at?: string | null;
  order_index: number;
  is_overdue: boolean;
  time_remaining_formatted: string;
  urgency_level: UrgencyLevel;
}

export interface TaskCreateInput {
  title: string;
  description?: string;
  category: Category;
  priority: Priority;
  estimated_duration: number;
  deadline: string;
  scheduled_start?: string;
  scheduled_end?: string;
}

export interface HabitLogDay {
  date: string; // YYYY-MM-DD
  day_name: string; // Mon, Tue...
  completed: boolean;
}

export interface Habit {
  id: string;
  title: string;
  description: string;
  category: string;
  frequency: string;
  target_days_per_week: number;
  icon: string;
  color: string;
  created_at: string;
  current_streak: number;
  best_streak: number;
  completion_rate_week: number;
  history: HabitLogDay[];
  completed_today: boolean;
}

export interface HabitCreateInput {
  title: string;
  description?: string;
  category?: string;
  frequency?: string;
  target_days_per_week?: number;
  icon?: string;
  color?: string;
}

export interface FocusSession {
  id: string;
  task_id?: string | null;
  task_title: string;
  mode: 'study' | 'work';
  duration_minutes: number;
  completed_at: string;
  notes?: string;
}

export interface FocusStats {
  today_minutes: number;
  week_minutes: number;
  study_minutes: number;
  work_minutes: number;
  total_sessions: number;
}

export interface Reminder {
  id: string;
  task_id?: string | null;
  title: string;
  remind_at: string;
  status: 'pending' | 'sent' | 'failed' | 'cancelled';
  channel: string;
  created_at: string;
  sent_at?: string | null;
}

export interface ReminderCreateInput {
  title: string;
  remind_at: string;
  task_id?: string | null;
  channel?: string;
}

export interface UserSettings {
  user_name: string;
  work_start_time: string;
  work_end_time: string;
  buffer_minutes: number;
  pomodoro_work_duration: number;
  pomodoro_break_duration: number;
  pomodoro_long_break_duration: number;
  theme: string;
  notifications_enabled: boolean;
  ai_provider: string;
  gemini_api_key?: string;
  timezone?: string;
}

export interface ScheduleSlot {
  id: string;
  task_id?: string | null;
  title: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  category: string;
  priority: string;
  is_buffer: boolean;
  is_break: boolean;
  status: string;
}

export interface DailySchedule {
  date: string;
  work_start_time: string;
  work_end_time: string;
  total_planned_minutes: number;
  total_available_minutes: number;
  is_overloaded: boolean;
  overload_minutes: number;
  slots: ScheduleSlot[];
  suggestions: string[];
  engine_used: string;
}

export interface SubtaskItem {
  title: string;
  description: string;
  category: string;
  priority: Priority;
  estimated_duration: number;
  suggested_day_offset: number;
}

export interface GoalBreakdown {
  goal_title: string;
  subtasks: SubtaskItem[];
  engine_used: string;
  explanation: string;
}

export interface ToolExecution {
  tool_name: string;
  arguments: Record<string, any>;
  result?: any;
  success: boolean;
  message: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  engine_used?: string;
  suggested_actions?: Array<{ label: string; route?: string; action?: string }>;
  tool_executions?: ToolExecution[];
  action_executed?: any;
}

export interface CategoryBreakdown {
  category: string;
  count: number;
  minutes: number;
}

export interface DailyCompletionPoint {
  day: string;
  date: string;
  completed: number;
  focus_minutes: number;
}

export interface AnalyticsOverview {
  total_tasks: number;
  completed_tasks: number;
  pending_tasks: number;
  overdue_tasks: number;
  completion_rate_percent: number;
  total_focus_minutes: number;
  study_focus_minutes: number;
  work_focus_minutes: number;
  active_habits_count: number;
  overall_habit_consistency_percent: number;
  productivity_score: number;
  category_distribution: CategoryBreakdown[];
  weekly_trend: DailyCompletionPoint[];
  smart_insights: string[];
}
