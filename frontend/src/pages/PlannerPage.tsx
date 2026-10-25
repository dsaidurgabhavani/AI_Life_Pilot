import React, { useState } from 'react';
import {
  Sparkles,
  AlertTriangle,
  Clock,
  CheckCircle2,
  Calendar,
  RefreshCw,
  Plus,
  Play,
  Coffee,
  Check,
  ChevronRight,
  ShieldCheck,
  Info,
  Download
} from 'lucide-react';
import confetti from 'canvas-confetti';
import { DailySchedule, Task } from '../types';
import { api } from '../api';

interface PlannerPageProps {
  schedule: DailySchedule | null;
  tasks: Task[];
  onRegenerate: () => Promise<void>;
  onOpenAddTask: () => void;
  onToggleTask: (id: string) => Promise<void>;
  onStartFocusOnTask: (task: Task) => void;
  isRegenerating: boolean;
}

export const PlannerPage: React.FC<PlannerPageProps> = ({
  schedule,
  tasks,
  onRegenerate,
  onOpenAddTask,
  onToggleTask,
  onStartFocusOnTask,
  isRegenerating
}) => {
  const [activeDate] = useState(() => new Date().toISOString().slice(0, 10));

  const handleToggle = async (taskId: string) => {
    confetti({
      particleCount: 40,
      spread: 50,
      origin: { y: 0.6 }
    });
    await onToggleTask(taskId);
  };

  const getTaskById = (taskId?: string | null): Task | undefined => {
    if (!taskId) return undefined;
    return tasks.find((t) => t.id === taskId);
  };

  const handleExportIcs = () => {
    window.open(api.getCalendarDownloadUrl(), '_blank');
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Top Banner & Control Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="font-bold text-base md:text-lg text-slate-900 dark:text-white">
              Daily Time-Blocking Engine
            </span>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
              Working Window: {schedule?.work_start_time || '09:00'} – {schedule?.work_end_time || '18:00'}
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Automatically arranges tasks by Eisenhower matrix urgency, deadline proximity, and cognitive recovery buffers.
          </p>
        </div>

        <div className="flex items-center gap-2.5 w-full sm:w-auto">
          <button
            onClick={handleExportIcs}
            title="Export to Google Calendar, Apple Calendar, or Outlook (.ics)"
            className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-xl text-xs font-semibold bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            <span>Export .ics</span>
          </button>

          <button
            onClick={onOpenAddTask}
            className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-1.5 px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Task</span>
          </button>

          <button
            onClick={onRegenerate}
            disabled={isRegenerating}
            className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-xs shadow-blue-500/20 active:scale-98 disabled:opacity-50 transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRegenerating ? 'animate-spin' : ''}`} />
            <span>{isRegenerating ? 'Optimizing Schedule...' : 'Regenerate Schedule'}</span>
          </button>
        </div>
      </div>

      {/* Overload Alert & Smart Practical Suggestions */}
      {schedule && (
        <div
          className={`p-5 rounded-2xl border transition-all ${
            schedule.is_overloaded
              ? 'border-amber-300/80 bg-amber-50/70 dark:bg-amber-950/20 dark:border-amber-900/60'
              : 'border-emerald-200 bg-emerald-50/60 dark:bg-emerald-950/20 dark:border-emerald-900/40'
          }`}
        >
          <div className="flex items-start gap-3">
            {schedule.is_overloaded ? (
              <div className="p-2 rounded-xl bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-300 shrink-0">
                <AlertTriangle className="w-5 h-5" />
              </div>
            ) : (
              <div className="p-2 rounded-xl bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-300 shrink-0">
                <ShieldCheck className="w-5 h-5" />
              </div>
            )}

            <div className="space-y-2 flex-1">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="font-bold text-sm text-slate-900 dark:text-white">
                  {schedule.is_overloaded
                    ? `⚠️ Schedule Overload Detected (${schedule.overload_minutes}m Over Capacity)`
                    : '✅ Balanced Schedule Confirmed'}
                </h3>

                <div className="text-xs text-slate-600 dark:text-slate-300 font-mono">
                  Planned: <span className="font-bold">{schedule.total_planned_minutes}m</span> / Available:{' '}
                  <span className="font-bold">{schedule.total_available_minutes}m</span>
                </div>
              </div>

              {/* Practical AI / Heuristic Suggestions */}
              <div className="space-y-1.5 pt-1">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 block">
                  Actionable Recommendations:
                </span>
                {schedule.suggestions.map((suggestion, idx) => (
                  <div
                    key={idx}
                    className="text-xs text-slate-700 dark:text-slate-300 flex items-start gap-2 bg-white/70 dark:bg-slate-900/50 p-2.5 rounded-xl border border-black/5 dark:border-white/5"
                  >
                    <Info className="w-3.5 h-3.5 text-blue-500 shrink-0 mt-0.5" />
                    <span>{suggestion}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Visual Timeline Section */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-blue-500" />
            <h3 className="font-bold text-sm text-slate-900 dark:text-white">
              Daily Chronological Timeline
            </h3>
          </div>
          <span className="text-xs text-slate-400 font-medium">
            {schedule?.slots.length || 0} Scheduled Blocks
          </span>
        </div>

        {/* Timeline Slots */}
        <div className="space-y-3 relative before:absolute before:inset-0 before:left-[45px] sm:before:left-[60px] before:w-0.5 before:bg-slate-100 dark:before:bg-slate-800">
          {schedule?.slots && schedule.slots.length > 0 ? (
            schedule.slots.map((slot) => {
              const linkedTask = getTaskById(slot.task_id);
              const isTaskDone = linkedTask?.status === 'completed';

              return (
                <div key={slot.id} className="relative flex items-start gap-3 sm:gap-4 group">
                  {/* Time label */}
                  <div className="w-12 sm:w-14 text-right pt-2 shrink-0">
                    <span className="font-mono text-xs font-bold text-slate-500 dark:text-slate-400">
                      {slot.start_time}
                    </span>
                  </div>

                  {/* Bullet */}
                  <div className="pt-2.5 shrink-0 z-10">
                    <div
                      className={`w-3 h-3 rounded-full border-2 bg-white dark:bg-slate-900 ${
                        slot.is_break
                          ? 'border-emerald-500'
                          : slot.is_buffer
                          ? 'border-slate-400'
                          : isTaskDone
                          ? 'border-emerald-500 bg-emerald-500'
                          : slot.priority === 'urgent_important'
                          ? 'border-rose-500'
                          : 'border-blue-500'
                      }`}
                    />
                  </div>

                  {/* Slot Card */}
                  <div
                    className={`flex-1 p-3.5 rounded-xl border transition-all ${
                      slot.is_break
                        ? 'border-emerald-200 dark:border-emerald-900/60 bg-emerald-50/40 dark:bg-emerald-950/10'
                        : slot.is_buffer
                        ? 'border-dashed border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30'
                        : isTaskDone
                        ? 'border-slate-200 dark:border-slate-800 bg-slate-50/40 dark:bg-slate-800/20 opacity-75'
                        : slot.priority === 'urgent_important'
                        ? 'border-rose-200 dark:border-rose-900/50 bg-rose-50/30 dark:bg-rose-950/10'
                        : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800/60'
                    }`}
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span
                            className={`font-semibold text-xs md:text-sm ${
                              isTaskDone ? 'line-through text-slate-400' : 'text-slate-900 dark:text-white'
                            }`}
                          >
                            {slot.title}
                          </span>

                          {slot.category && (
                            <span className="text-[10px] px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-700/60 text-slate-600 dark:text-slate-300 font-medium">
                              {slot.category}
                            </span>
                          )}

                          {slot.priority === 'urgent_important' && !slot.is_break && (
                            <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300 font-bold">
                              P1
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-3 text-[11px] text-slate-400">
                          <span className="flex items-center gap-1 font-mono">
                            <Clock className="w-3 h-3" />
                            {slot.start_time} - {slot.end_time} ({slot.duration_minutes}m)
                          </span>
                          {linkedTask && linkedTask.time_remaining_formatted && (
                            <span>• Due: {linkedTask.time_remaining_formatted}</span>
                          )}
                        </div>
                      </div>

                      {/* Action buttons on slot */}
                      {!slot.is_buffer && !slot.is_break && linkedTask && (
                        <div className="flex items-center gap-2 shrink-0 pt-1 sm:pt-0">
                          <button
                            onClick={() => onStartFocusOnTask(linkedTask)}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 hover:bg-blue-100"
                          >
                            <Play className="w-3 h-3 fill-current text-blue-600" />
                            <span>Focus</span>
                          </button>

                          <button
                            onClick={() => handleToggle(linkedTask.id)}
                            className={`p-1.5 rounded-lg border text-xs transition-colors ${
                              isTaskDone
                                ? 'bg-emerald-500 border-emerald-500 text-white'
                                : 'border-slate-300 dark:border-slate-600 hover:border-emerald-500 hover:text-emerald-500 text-slate-400'
                            }`}
                            title={isTaskDone ? 'Mark incomplete' : 'Mark complete'}
                          >
                            <Check className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="py-12 text-center text-slate-400 space-y-2">
              <Calendar className="w-8 h-8 mx-auto text-slate-300 dark:text-slate-600" />
              <div className="text-sm font-semibold">No Schedule Generated</div>
              <p className="text-xs">
                Click "Regenerate Schedule" above to generate your optimized daily plan!
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
