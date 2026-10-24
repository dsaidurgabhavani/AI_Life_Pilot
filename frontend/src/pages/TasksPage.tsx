import React, { useState } from 'react';
import {
  Search,
  Plus,
  Filter,
  ArrowUpDown,
  Clock,
  AlertTriangle,
  CheckCircle2,
  Trash2,
  Edit2,
  Play,
  Check,
  Calendar,
  Layers,
  Sparkles
} from 'lucide-react';
import confetti from 'canvas-confetti';
import { Task, Category, Priority, TaskStatus } from '../types';

interface TasksPageProps {
  tasks: Task[];
  onOpenAddTask: () => void;
  onEditTask: (task: Task) => void;
  onDeleteTask: (id: string) => Promise<void>;
  onToggleTask: (id: string) => Promise<void>;
  onStartFocus: (task: Task) => void;
}

export const TasksPage: React.FC<TasksPageProps> = ({
  tasks,
  onOpenAddTask,
  onEditTask,
  onDeleteTask,
  onToggleTask,
  onStartFocus
}) => {
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [selectedPriority, setSelectedPriority] = useState<string>('All');
  const [selectedStatus, setSelectedStatus] = useState<string>('All');
  const [sortBy, setSortBy] = useState<string>('deadline');
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const categories = ['All', 'Work', 'Study', 'Health', 'Personal', 'Finance'];
  const priorities = [
    { value: 'All', label: 'All Priorities' },
    { value: 'urgent_important', label: 'Urgent & Important (P1)' },
    { value: 'important_not_urgent', label: 'Important, Not Urgent (P2)' },
    { value: 'urgent_not_important', label: 'Urgent, Not Important (P3)' },
    { value: 'neither', label: 'Neither (P4)' }
  ];
  const statuses = [
    { value: 'All', label: 'All Statuses' },
    { value: 'pending', label: 'Pending' },
    { value: 'in_progress', label: 'In Progress' },
    { value: 'completed', label: 'Completed' }
  ];

  const filteredTasks = tasks
    .filter((task) => {
      const matchesSearch =
        task.title.toLowerCase().includes(search.toLowerCase()) ||
        task.description.toLowerCase().includes(search.toLowerCase());
      const matchesCategory =
        selectedCategory === 'All' || task.category.toLowerCase() === selectedCategory.toLowerCase();
      const matchesPriority =
        selectedPriority === 'All' || task.priority === selectedPriority;
      const matchesStatus =
        selectedStatus === 'All' || task.status === selectedStatus;
      return matchesSearch && matchesCategory && matchesPriority && matchesStatus;
    })
    .sort((a, b) => {
      if (sortBy === 'priority') {
        const order: Record<Priority, number> = {
          urgent_important: 0,
          urgent_not_important: 1,
          important_not_urgent: 2,
          neither: 3
        };
        return order[a.priority] - order[b.priority];
      }
      if (sortBy === 'duration') return a.estimated_duration - b.estimated_duration;
      if (sortBy === 'created_at') return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      // default deadline (completed last, then closest deadline)
      if (a.status === 'completed' && b.status !== 'completed') return 1;
      if (a.status !== 'completed' && b.status === 'completed') return -1;
      return new Date(a.deadline).getTime() - new Date(b.deadline).getTime();
    });

  const handleToggle = async (taskId: string) => {
    confetti({
      particleCount: 50,
      spread: 60,
      origin: { y: 0.6 }
    });
    await onToggleTask(taskId);
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      try {
        setDeletingId(id);
        await onDeleteTask(id);
      } finally {
        setDeletingId(null);
      }
    }
  };

  const overdueCount = tasks.filter((t) => t.is_overdue && t.status !== 'completed').length;

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Top Banner & Stats Overview */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h2 className="text-base md:text-lg font-bold text-slate-900 dark:text-white">
              Smart Deadline Manager
            </h2>
            {overdueCount > 0 && (
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300 flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" />
                {overdueCount} Overdue
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Real-time deadline countdowns, Eisenhower prioritization, and actionable delays recovery.
          </p>
        </div>

        <button
          onClick={onOpenAddTask}
          className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-xs shadow-blue-500/20 active:scale-98 transition-all shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>New Task</span>
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Search Input */}
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search tasks..."
              className="w-full pl-9 pr-3.5 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            />
          </div>

          {/* Priority filter */}
          <div>
            <select
              value={selectedPriority}
              onChange={(e) => setSelectedPriority(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            >
              {priorities.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label}
                </option>
              ))}
            </select>
          </div>

          {/* Status filter */}
          <div>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            >
              {statuses.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>

          {/* Sort By */}
          <div className="flex items-center gap-2">
            <ArrowUpDown className="w-4 h-4 text-slate-400 shrink-0" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            >
              <option value="deadline">Sort: Deadline</option>
              <option value="priority">Sort: Priority</option>
              <option value="duration">Sort: Duration</option>
              <option value="created_at">Sort: Created Date</option>
            </select>
          </div>
        </div>

        {/* Category Pill Filters */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 pt-1 border-t border-slate-100 dark:border-slate-800/80">
          <span className="text-[11px] font-semibold text-slate-400 mr-1 shrink-0">Category:</span>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                selectedCategory === cat
                  ? 'bg-blue-600 text-white font-semibold'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Tasks List */}
      <div className="space-y-3">
        {filteredTasks.length > 0 ? (
          filteredTasks.map((task) => {
            const isCompleted = task.status === 'completed';

            return (
              <div
                key={task.id}
                className={`p-4 rounded-2xl border transition-all ${
                  isCompleted
                    ? 'border-slate-200 dark:border-slate-800/80 bg-slate-50/60 dark:bg-slate-900/40 opacity-75'
                    : task.is_overdue
                    ? 'border-rose-300 dark:border-rose-900/60 bg-rose-50/30 dark:bg-rose-950/20 shadow-xs'
                    : task.urgency_level === 'urgent'
                    ? 'border-amber-300 dark:border-amber-900/60 bg-amber-50/20 dark:bg-amber-950/10'
                    : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xs hover:border-slate-300'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  {/* Left: Checkbox & Title Details */}
                  <div className="flex items-start gap-3 flex-1 min-w-0">
                    <button
                      onClick={() => handleToggle(task.id)}
                      className={`w-5 h-5 rounded-md border flex items-center justify-center shrink-0 mt-0.5 transition-colors ${
                        isCompleted
                          ? 'bg-emerald-500 border-emerald-500 text-white'
                          : 'border-slate-300 dark:border-slate-600 hover:border-blue-500'
                      }`}
                    >
                      {isCompleted && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                    </button>

                    <div className="space-y-1.5 flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span
                          className={`font-semibold text-sm ${
                            isCompleted ? 'line-through text-slate-400 dark:text-slate-500' : 'text-slate-900 dark:text-white'
                          }`}
                        >
                          {task.title}
                        </span>

                        {/* Category badge */}
                        <span className="text-[10px] px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-medium">
                          {task.category}
                        </span>

                        {/* Priority Badge */}
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded-md font-semibold ${
                            task.priority === 'urgent_important'
                              ? 'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300'
                              : task.priority === 'important_not_urgent'
                              ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                              : task.priority === 'urgent_not_important'
                              ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'
                              : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
                          }`}
                        >
                          {task.priority === 'urgent_important'
                            ? 'Urgent & Important'
                            : task.priority === 'important_not_urgent'
                            ? 'Important'
                            : task.priority === 'urgent_not_important'
                            ? 'Quick / Urgent'
                            : 'Low Priority'}
                        </span>
                      </div>

                      {task.description && (
                        <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2">
                          {task.description}
                        </p>
                      )}

                      {/* Actionable delay recovery tip if overdue or urgent */}
                      {task.is_overdue && !isCompleted && (
                        <div className="text-[11px] font-medium text-rose-700 dark:text-rose-300 bg-rose-100/60 dark:bg-rose-950/40 p-2 rounded-lg border border-rose-200/60 dark:border-rose-900/40 flex items-center gap-1.5">
                          <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                          <span>
                            Delayed Risk Action: Allocate a 25-minute Pomodoro focus block right now to unblock submission.
                          </span>
                        </div>
                      )}

                      <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 pt-1">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5" />
                          {task.estimated_duration} mins
                        </span>

                        <span className="flex items-center gap-1">
                          <Calendar className="w-3.5 h-3.5" />
                          Due:{' '}
                          <span
                            className={
                              task.is_overdue && !isCompleted
                                ? 'text-rose-600 dark:text-rose-400 font-bold'
                                : 'text-slate-700 dark:text-slate-300'
                            }
                          >
                            {task.time_remaining_formatted}
                          </span>
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Right Actions */}
                  <div className="flex items-center gap-1.5 shrink-0">
                    {!isCompleted && (
                      <button
                        onClick={() => onStartFocus(task)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-semibold bg-blue-50 dark:bg-blue-950/50 text-blue-700 dark:text-blue-300 hover:bg-blue-100"
                        title="Start focus timer on this task"
                      >
                        <Play className="w-3.5 h-3.5 fill-current text-blue-600" />
                        <span className="hidden sm:inline">Focus</span>
                      </button>
                    )}

                    <button
                      onClick={() => onEditTask(task)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
                      title="Edit Task"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>

                    <button
                      onClick={() => handleDelete(task.id)}
                      disabled={deletingId === task.id}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40"
                      title="Delete Task"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        ) : (
          <div className="py-16 text-center text-slate-400 space-y-3 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
            <CheckCircle2 className="w-10 h-10 mx-auto text-slate-300 dark:text-slate-600" />
            <div className="text-sm font-semibold text-slate-700 dark:text-slate-300">
              No Tasks Match Your Filter
            </div>
            <p className="text-xs max-w-sm mx-auto">
              Try adjusting your search criteria or create a new task to organize your day.
            </p>
            <button
              onClick={onOpenAddTask}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-blue-600 text-white"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Create Task</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
