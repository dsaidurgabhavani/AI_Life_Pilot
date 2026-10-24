import React from 'react';
import {
  Sparkles,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Flame,
  ArrowRight,
  Play,
  Calendar,
  Layers,
  Check,
  TrendingUp,
  Brain
} from 'lucide-react';
import confetti from 'canvas-confetti';
import { Task, DailySchedule, Habit, FocusStats } from '../types';

interface DashboardPageProps {
  tasks: Task[];
  recommendedTask: Task | null;
  todaySchedule: DailySchedule | null;
  habits: Habit[];
  focusStats: FocusStats | null;
  onNavigateTab: (tab: any) => void;
  onOpenAddTask: () => void;
  onOpenGoalBreakdown: () => void;
  onToggleTask: (id: string) => Promise<void>;
  onStartFocusOnTask: (task: Task) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  tasks,
  recommendedTask,
  todaySchedule,
  habits,
  focusStats,
  onNavigateTab,
  onOpenAddTask,
  onOpenGoalBreakdown,
  onToggleTask,
  onStartFocusOnTask
}) => {
  const completedTasks = tasks.filter((t) => t.status === 'completed');
  const pendingTasks = tasks.filter((t) => t.status !== 'completed');
  const overdueTasks = tasks.filter((t) => t.is_overdue && t.status !== 'completed');
  const completionRate = tasks.length > 0 ? Math.round((completedTasks.length / tasks.length) * 100) : 0;

  const handleQuickComplete = async (taskId: string) => {
    confetti({
      particleCount: 50,
      spread: 45,
      origin: { y: 0.7 }
    });
    await onToggleTask(taskId);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Hero Welcome & Next Recommended Task Card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Recommended Next Task (Hero) */}
        <div className="lg:col-span-2 relative overflow-hidden rounded-2xl bg-gradient-to-br from-blue-600 via-indigo-600 to-sky-700 p-6 md:p-8 text-white shadow-xl shadow-blue-600/10">
          <div className="absolute top-0 right-0 -mt-6 -mr-6 w-52 h-52 bg-white/10 rounded-full blur-2xl pointer-events-none" />

          <div className="relative z-10 flex flex-col justify-between h-full space-y-6">
            <div>
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-white/15 backdrop-blur-md text-white/95 mb-3 border border-white/20">
                <Brain className="w-3.5 h-3.5 text-sky-200" />
                <span>AI Recommendation Engine</span>
              </div>

              <h2 className="text-xl md:text-2xl font-bold tracking-tight text-white mb-2">
                What to Focus on Next
              </h2>

              {recommendedTask ? (
                <div className="mt-4 p-4 rounded-xl bg-white/10 backdrop-blur-md border border-white/15 space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="font-bold text-base md:text-lg text-white">
                      {recommendedTask.title}
                    </span>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-white text-indigo-900 shadow-xs">
                      {recommendedTask.category} • {recommendedTask.estimated_duration} mins
                    </span>
                  </div>

                  {recommendedTask.description && (
                    <p className="text-xs md:text-sm text-sky-100/90 line-clamp-2">
                      {recommendedTask.description}
                    </p>
                  )}

                  <div className="flex items-center justify-between text-xs text-sky-200 pt-1">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      {recommendedTask.time_remaining_formatted}
                    </span>
                    {recommendedTask.is_overdue && (
                      <span className="text-rose-200 font-bold flex items-center gap-1">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        Needs Immediate Attention
                      </span>
                    )}
                  </div>
                </div>
              ) : (
                <div className="p-4 rounded-xl bg-white/10 backdrop-blur-md border border-white/15 text-sm text-sky-100">
                  🎉 All queued tasks are complete! Add a new task or take a well-deserved break.
                </div>
              )}
            </div>

            {/* Quick Action bar inside hero */}
            <div className="flex flex-wrap items-center gap-3 pt-2">
              {recommendedTask && (
                <button
                  onClick={() => onStartFocusOnTask(recommendedTask)}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-xs md:text-sm bg-white text-indigo-900 hover:bg-sky-50 shadow-md transition-all active:scale-98"
                >
                  <Play className="w-4 h-4 fill-current text-indigo-600" />
                  <span>Start Focus Sprint ({recommendedTask.estimated_duration}m)</span>
                </button>
              )}

              <button
                onClick={() => onNavigateTab('planner')}
                className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl font-semibold text-xs md:text-sm bg-white/15 hover:bg-white/20 text-white backdrop-blur-md border border-white/20 transition-all"
              >
                <span>View Daily Timeline</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Quick Actions & Goal Assistant Widget */}
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 flex flex-col justify-between shadow-xs">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-sm text-slate-900 dark:text-white">
                Productivity Shortcuts
              </h3>
              <Sparkles className="w-4 h-4 text-indigo-500" />
            </div>

            <div className="space-y-2.5">
              <button
                onClick={onOpenAddTask}
                className="w-full p-3 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 hover:bg-blue-50/50 dark:hover:bg-blue-950/20 hover:border-blue-200 text-left transition-all flex items-center justify-between group"
              >
                <div>
                  <div className="text-xs font-semibold text-slate-800 dark:text-slate-200 group-hover:text-blue-600 dark:group-hover:text-blue-400">
                    + Add New Task
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400">
                    Categorize, set deadline & priority
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600 transition-transform group-hover:translate-x-0.5" />
              </button>

              <button
                onClick={onOpenGoalBreakdown}
                className="w-full p-3 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 hover:bg-indigo-50/50 dark:hover:bg-indigo-950/20 hover:border-indigo-200 text-left transition-all flex items-center justify-between group"
              >
                <div>
                  <div className="text-xs font-semibold text-slate-800 dark:text-slate-200 group-hover:text-indigo-600 dark:group-hover:text-indigo-400">
                    Break Down Big Goal
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400">
                    AI splits large milestones into subtasks
                  </div>
                </div>
                <Layers className="w-4 h-4 text-slate-400 group-hover:text-indigo-600 transition-transform group-hover:translate-x-0.5" />
              </button>

              <button
                onClick={() => onNavigateTab('focus')}
                className="w-full p-3 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 hover:bg-emerald-50/50 dark:hover:bg-emerald-950/20 hover:border-emerald-200 text-left transition-all flex items-center justify-between group"
              >
                <div>
                  <div className="text-xs font-semibold text-slate-800 dark:text-slate-200 group-hover:text-emerald-600 dark:group-hover:text-emerald-400">
                    Pomodoro Focus Mode
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400">
                    25/5 Study & Work deep work timer
                  </div>
                </div>
                <Play className="w-4 h-4 text-slate-400 group-hover:text-emerald-600 transition-transform group-hover:translate-x-0.5" />
              </button>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
            <span>Daily Plan Health</span>
            <span className="font-semibold text-emerald-600 dark:text-emerald-400">
              {todaySchedule?.is_overloaded ? '⚠️ Overload Risk' : 'Optimal Pace'}
            </span>
          </div>
        </div>
      </div>

      {/* 4 Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Task Completion Rate */}
        <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xs space-y-2">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold">Completion Rate</span>
            <CheckCircle2 className="w-4 h-4 text-blue-500" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-900 dark:text-white">
              {completionRate}%
            </span>
            <span className="text-xs text-slate-400">
              ({completedTasks.length}/{tasks.length})
            </span>
          </div>
          {/* Progress bar */}
          <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-blue-600 h-1.5 rounded-full transition-all duration-500"
              style={{ width: `${completionRate}%` }}
            />
          </div>
        </div>

        {/* Overdue / Urgent Alert */}
        <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xs space-y-2">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold">Overdue Tasks</span>
            <AlertTriangle className={`w-4 h-4 ${overdueTasks.length > 0 ? 'text-rose-500' : 'text-slate-400'}`} />
          </div>
          <div className="flex items-baseline gap-2">
            <span className={`text-2xl font-bold ${overdueTasks.length > 0 ? 'text-rose-600 dark:text-rose-400' : 'text-slate-900 dark:text-white'}`}>
              {overdueTasks.length}
            </span>
            <span className="text-xs text-slate-400">
              {overdueTasks.length > 0 ? 'Action needed' : 'All on track'}
            </span>
          </div>
          <div className="text-[11px] text-slate-500 truncate">
            {pendingTasks.length} active tasks remaining
          </div>
        </div>

        {/* Focus Time Today */}
        <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xs space-y-2">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold">Focus Logged Today</span>
            <Clock className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-900 dark:text-white">
              {focusStats ? focusStats.today_minutes : 0}
            </span>
            <span className="text-xs text-slate-400">mins (Goal: 120m)</span>
          </div>
          <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-indigo-600 h-1.5 rounded-full transition-all duration-500"
              style={{
                width: `${Math.min(100, (((focusStats?.today_minutes || 0) / 120) * 100))}%`
              }}
            />
          </div>
        </div>

        {/* Habit Streaks */}
        <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xs space-y-2">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold">Active Habits</span>
            <Flame className="w-4 h-4 text-amber-500" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-900 dark:text-white">
              {habits.length}
            </span>
            <span className="text-xs text-slate-400">routines</span>
          </div>
          <div className="text-[11px] text-emerald-600 dark:text-emerald-400 font-medium truncate">
            Top streak: {Math.max(0, ...habits.map((h) => h.current_streak))} days unbroken 🔥
          </div>
        </div>
      </div>

      {/* Main Grid: Today's Timeline Preview & Urgent Tasks */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Today's Schedule Preview */}
        <div className="lg:col-span-2 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-2xs space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-base text-slate-900 dark:text-white">
                Today's Time-Blocked Schedule
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Optimized by priority, deadline proximity, and cognitive buffers
              </p>
            </div>
            <button
              onClick={() => onNavigateTab('planner')}
              className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
            >
              <span>Full Schedule</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {todaySchedule?.slots && todaySchedule.slots.length > 0 ? (
            <div className="space-y-2.5">
              {todaySchedule.slots.slice(0, 5).map((slot) => (
                <div
                  key={slot.id}
                  className={`p-3 rounded-xl border flex items-center justify-between gap-3 text-xs ${
                    slot.is_break
                      ? 'border-emerald-200 bg-emerald-50/60 dark:bg-emerald-950/20 text-emerald-800 dark:text-emerald-300'
                      : slot.is_buffer
                      ? 'border-dashed border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 text-slate-500'
                      : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800/60 text-slate-800 dark:text-slate-200'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="font-mono font-bold text-slate-500 dark:text-slate-400 shrink-0">
                      {slot.start_time} - {slot.end_time}
                    </span>
                    <span className="font-medium truncate max-w-xs sm:max-w-md">
                      {slot.title}
                    </span>
                  </div>

                  <span className="text-[11px] text-slate-400 shrink-0">
                    {slot.duration_minutes}m
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-400 text-xs">
              No schedule slots generated yet.
            </div>
          )}
        </div>

        {/* Pending & Urgent Deadlines */}
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-2xs space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-base text-slate-900 dark:text-white">
              Upcoming Deadlines
            </h3>
            <button
              onClick={() => onNavigateTab('tasks')}
              className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
            >
              <span>All Tasks</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-2.5">
            {pendingTasks.slice(0, 5).map((task) => (
              <div
                key={task.id}
                className="p-3 rounded-xl border border-slate-100 dark:border-slate-800/80 bg-slate-50/60 dark:bg-slate-800/40 hover:bg-white dark:hover:bg-slate-800 transition-all flex items-center justify-between gap-2 text-xs"
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <button
                    onClick={() => handleQuickComplete(task.id)}
                    className="w-5 h-5 rounded-md border border-slate-300 dark:border-slate-600 flex items-center justify-center hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/40 shrink-0 transition-colors"
                  >
                    <Check className="w-3 h-3 text-transparent hover:text-blue-600" />
                  </button>
                  <div className="truncate">
                    <div className="font-medium text-slate-900 dark:text-white truncate">
                      {task.title}
                    </div>
                    <div className="text-[10px] text-slate-400 flex items-center gap-1 mt-0.5">
                      <span>{task.category}</span>
                      <span>•</span>
                      <span className={task.is_overdue ? 'text-rose-500 font-semibold' : ''}>
                        {task.time_remaining_formatted}
                      </span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => onStartFocusOnTask(task)}
                  title="Sprint on this task"
                  className="p-1.5 rounded-lg bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 hover:bg-blue-100 shrink-0"
                >
                  <Play className="w-3 h-3 fill-current" />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
