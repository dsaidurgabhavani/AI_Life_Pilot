import {
  Task,
  TaskCreateInput,
  Habit,
  HabitCreateInput,
  FocusSession,
  FocusStats,
  UserSettings,
  DailySchedule,
  GoalBreakdown,
  AnalyticsOverview
} from './types';

const API_BASE = (import.meta.env.VITE_API_URL ? import.meta.env.VITE_API_URL.replace(/\/$/, '') : '') + '/api';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorMsg = `HTTP error ${res.status}`;
    try {
      const err = await res.json();
      if (err.detail) errorMsg = err.detail;
    } catch {
      // ignore
    }
    throw new Error(errorMsg);
  }
  return res.json();
}

// Tasks
export const api = {
  getTasks: async (params?: { search?: string; category?: string; priority?: string; status?: string; sort_by?: string }): Promise<Task[]> => {
    const searchParams = new URLSearchParams();
    if (params?.search) searchParams.set('search', params.search);
    if (params?.category) searchParams.set('category', params.category);
    if (params?.priority) searchParams.set('priority', params.priority);
    if (params?.status) searchParams.set('status', params.status);
    if (params?.sort_by) searchParams.set('sort_by', params.sort_by);
    const res = await fetch(`${API_BASE}/tasks?${searchParams.toString()}`);
    return handleResponse<Task[]>(res);
  },

  getTask: async (id: string): Promise<Task> => {
    const res = await fetch(`${API_BASE}/tasks/${id}`);
    return handleResponse<Task>(res);
  },

  getNextRecommendedTask: async (): Promise<Task | null> => {
    const res = await fetch(`${API_BASE}/tasks/recommendation/next`);
    return handleResponse<Task | null>(res);
  },

  createTask: async (task: TaskCreateInput): Promise<Task> => {
    const res = await fetch(`${API_BASE}/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(task)
    });
    return handleResponse<Task>(res);
  },

  updateTask: async (id: string, updates: Partial<Task>): Promise<Task> => {
    const res = await fetch(`${API_BASE}/tasks/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates)
    });
    return handleResponse<Task>(res);
  },

  toggleTask: async (id: string): Promise<Task> => {
    const res = await fetch(`${API_BASE}/tasks/${id}/toggle`, {
      method: 'POST'
    });
    return handleResponse<Task>(res);
  },

  deleteTask: async (id: string): Promise<{ message: string; id: string }> => {
    const res = await fetch(`${API_BASE}/tasks/${id}`, {
      method: 'DELETE'
    });
    return handleResponse(res);
  },

  // Planner
  getTodaySchedule: async (date?: string): Promise<DailySchedule> => {
    const url = date ? `${API_BASE}/planner/today?date=${date}` : `${API_BASE}/planner/today`;
    const res = await fetch(url);
    return handleResponse<DailySchedule>(res);
  },

  generateSchedule: async (date?: string): Promise<DailySchedule> => {
    const url = date ? `${API_BASE}/planner/generate?date=${date}` : `${API_BASE}/planner/generate`;
    const res = await fetch(url, { method: 'POST' });
    return handleResponse<DailySchedule>(res);
  },

  reorderSchedule: async (slots: Array<{ task_id: string; scheduled_start: string; scheduled_end: string }>): Promise<{ message: string }> => {
    const res = await fetch(`${API_BASE}/planner/reorder`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ slots })
    });
    return handleResponse(res);
  },

  // Habits
  getHabits: async (): Promise<Habit[]> => {
    const res = await fetch(`${API_BASE}/habits`);
    return handleResponse<Habit[]>(res);
  },

  createHabit: async (habit: HabitCreateInput): Promise<Habit> => {
    const res = await fetch(`${API_BASE}/habits`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(habit)
    });
    return handleResponse<Habit>(res);
  },

  updateHabit: async (id: string, updates: Partial<Habit>): Promise<Habit> => {
    const res = await fetch(`${API_BASE}/habits/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates)
    });
    return handleResponse<Habit>(res);
  },

  toggleHabitDay: async (id: string, date: string, completed?: boolean): Promise<Habit> => {
    const res = await fetch(`${API_BASE}/habits/${id}/toggle`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ date, completed })
    });
    return handleResponse<Habit>(res);
  },

  deleteHabit: async (id: string): Promise<{ message: string; id: string }> => {
    const res = await fetch(`${API_BASE}/habits/${id}`, {
      method: 'DELETE'
    });
    return handleResponse(res);
  },

  // Focus
  getFocusSessions: async (): Promise<FocusSession[]> => {
    const res = await fetch(`${API_BASE}/focus/sessions`);
    return handleResponse<FocusSession[]>(res);
  },

  recordFocusSession: async (session: { task_id?: string | null; task_title: string; mode: 'study' | 'work'; duration_minutes: number; notes?: string }): Promise<FocusSession> => {
    const res = await fetch(`${API_BASE}/focus/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(session)
    });
    return handleResponse<FocusSession>(res);
  },

  getFocusStats: async (): Promise<FocusStats> => {
    const res = await fetch(`${API_BASE}/focus/stats`);
    return handleResponse<FocusStats>(res);
  },

  // Assistant
  sendChatMessage: async (message: string, conversationHistory: Array<{ role: string; content: string }>) => {
    const res = await fetch(`${API_BASE}/assistant/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        conversation_history: conversationHistory
      })
    });
    return handleResponse<{ reply: string; engine_used: string; suggested_actions: Array<{ label: string; route?: string; action?: string }> }>(res);
  },

  breakdownGoal: async (goalTitle: string, category: string = 'Study', targetDeadline?: string): Promise<GoalBreakdown> => {
    const res = await fetch(`${API_BASE}/assistant/breakdown`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        goal_title: goalTitle,
        category,
        target_deadline: targetDeadline
      })
    });
    return handleResponse<GoalBreakdown>(res);
  },

  importSubtasks: async (subtasks: any[]): Promise<{ imported_count: number; message: string }> => {
    const res = await fetch(`${API_BASE}/assistant/import-subtasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subtasks })
    });
    return handleResponse(res);
  },

  // Analytics
  getAnalyticsOverview: async (): Promise<AnalyticsOverview> => {
    const res = await fetch(`${API_BASE}/analytics/overview`);
    return handleResponse<AnalyticsOverview>(res);
  },

  // Settings
  getSettings: async (): Promise<UserSettings> => {
    const res = await fetch(`${API_BASE}/settings`);
    return handleResponse<UserSettings>(res);
  },

  updateSettings: async (updates: Partial<UserSettings>): Promise<UserSettings> => {
    const res = await fetch(`${API_BASE}/settings`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates)
    });
    return handleResponse<UserSettings>(res);
  },

  // Demo Data Reset / Clear
  resetDemoData: async (): Promise<{ message: string }> => {
    const res = await fetch(`${API_BASE}/demo/reset`, { method: 'POST' });
    return handleResponse(res);
  },

  clearUserData: async (): Promise<{ message: string }> => {
    const res = await fetch(`${API_BASE}/demo/clear`, { method: 'POST' });
    return handleResponse(res);
  }
};
