import React from 'react';
import { X, AlertTriangle, Clock, CheckCircle2, ArrowRight } from 'lucide-react';
import { Task } from '../types';

interface NotificationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  tasks: Task[];
  onToggleTask: (id: string) => void;
  onStartFocus: (task: Task) => void;
}

export const NotificationDrawer: React.FC<NotificationDrawerProps> = ({
  isOpen,
  onClose,
  tasks,
  onToggleTask,
  onStartFocus
}) => {
  if (!isOpen) return null;

  const overdueTasks = tasks.filter((t) => t.is_overdue && t.status !== 'completed');
  const urgentTasks = tasks.filter(
    (t) => !t.is_overdue && t.urgency_level === 'urgent' && t.status !== 'completed'
  );

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-xs transition-opacity"
        onClick={onClose}
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col">
          {/* Header */}
          <div className="p-5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                Deadline & Risk Notifications
                {(overdueTasks.length > 0 || urgentTasks.length > 0) && (
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-400">
                    {overdueTasks.length + urgentTasks.length} Alerts
                  </span>
                )}
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Actionable interventions to protect your daily timeline
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* List */}
          <div className="p-5 overflow-y-auto space-y-4 flex-1">
            {overdueTasks.length === 0 && urgentTasks.length === 0 ? (
              <div className="text-center py-12 text-slate-400 space-y-2">
                <CheckCircle2 className="w-10 h-10 mx-auto text-emerald-500" />
                <div className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                  All Clear! No Overdue Tasks
                </div>
                <p className="text-xs max-w-xs mx-auto">
                  Your deadlines are under control. Keep up the steady momentum!
                </p>
              </div>
            ) : (
              <>
                {/* Overdue Section */}
                {overdueTasks.length > 0 && (
                  <div className="space-y-3">
                    <div className="text-xs font-bold uppercase tracking-wider text-rose-600 dark:text-rose-400 flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5" />
                      Critical Overdue Tasks ({overdueTasks.length})
                    </div>

                    {overdueTasks.map((task) => (
                      <div
                        key={task.id}
                        className="p-3.5 rounded-xl border border-rose-200 dark:border-rose-900/60 bg-rose-50/50 dark:bg-rose-950/20 space-y-2"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <span className="font-semibold text-xs text-slate-900 dark:text-white">
                            {task.title}
                          </span>
                          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300 whitespace-nowrap">
                            {task.time_remaining_formatted}
                          </span>
                        </div>

                        {/* Actionable Next Step Suggestion */}
                        <div className="text-[11px] p-2 rounded-lg bg-white/80 dark:bg-slate-800/80 border border-rose-100 dark:border-rose-900 text-slate-700 dark:text-slate-300">
                          <span className="font-semibold text-rose-600 dark:text-rose-400">💡 Recommended Action: </span>
                          {task.estimated_duration > 40
                            ? 'Timebox this task into a 25m Pomodoro sprint now or split into subtasks to break inertia.'
                            : 'Quick win: Allocate 15 uninterrupted minutes right now to finish and submit.'}
                        </div>

                        <div className="flex items-center justify-end gap-2 pt-1">
                          <button
                            onClick={() => onStartFocus(task)}
                            className="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-rose-600 hover:bg-rose-700 text-white flex items-center gap-1"
                          >
                            <Clock className="w-3 h-3" />
                            Focus Now
                          </button>
                          <button
                            onClick={() => onToggleTask(task.id)}
                            className="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200"
                          >
                            Done
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Urgent Section */}
                {urgentTasks.length > 0 && (
                  <div className="space-y-3 pt-2">
                    <div className="text-xs font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400 flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5" />
                      Due Within 4 Hours ({urgentTasks.length})
                    </div>

                    {urgentTasks.map((task) => (
                      <div
                        key={task.id}
                        className="p-3.5 rounded-xl border border-amber-200 dark:border-amber-900/60 bg-amber-50/50 dark:bg-amber-950/20 space-y-2"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <span className="font-semibold text-xs text-slate-900 dark:text-white">
                            {task.title}
                          </span>
                          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300 whitespace-nowrap">
                            {task.time_remaining_formatted}
                          </span>
                        </div>

                        <div className="text-[11px] text-slate-600 dark:text-slate-400">
                          Estimated duration: {task.estimated_duration} mins.
                        </div>

                        <div className="flex items-center justify-end gap-2 pt-1">
                          <button
                            onClick={() => onStartFocus(task)}
                            className="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-amber-600 hover:bg-amber-700 text-white flex items-center gap-1"
                          >
                            <Clock className="w-3 h-3" />
                            Sprint ({task.estimated_duration}m)
                          </button>
                          <button
                            onClick={() => onToggleTask(task.id)}
                            className="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200"
                          >
                            Mark Done
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
