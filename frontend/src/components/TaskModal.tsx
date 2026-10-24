import React, { useState, useEffect } from 'react';
import { X, Calendar, Clock, Tag, Flag, AlertCircle } from 'lucide-react';
import { Task, Category, Priority, TaskCreateInput } from '../types';

interface TaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: TaskCreateInput) => Promise<void>;
  initialTask?: Task | null;
}

const CATEGORIES: Category[] = ['Work', 'Study', 'Health', 'Personal', 'Finance'];

const PRIORITIES: Array<{ value: Priority; label: string; desc: string; color: string }> = [
  {
    value: 'urgent_important',
    label: 'Urgent & Important (Do First)',
    desc: 'Critical deadlines & crises',
    color: 'border-rose-500 bg-rose-50/50 text-rose-700 dark:bg-rose-950/30 dark:text-rose-400'
  },
  {
    value: 'important_not_urgent',
    label: 'Important, Not Urgent (Schedule)',
    desc: 'Strategic goals & deep work',
    color: 'border-blue-500 bg-blue-50/50 text-blue-700 dark:bg-blue-950/30 dark:text-blue-400'
  },
  {
    value: 'urgent_not_important',
    label: 'Urgent, Not Important (Delegate/Quick)',
    desc: 'Interruptions & quick tasks',
    color: 'border-amber-500 bg-amber-50/50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-400'
  },
  {
    value: 'neither',
    label: 'Neither (Eliminate/Low Priority)',
    desc: 'Trivial & low leverage tasks',
    color: 'border-slate-400 bg-slate-50/50 text-slate-700 dark:bg-slate-800/40 dark:text-slate-400'
  }
];

export const TaskModal: React.FC<TaskModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  initialTask
}) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState<Category>('Work');
  const [priority, setPriority] = useState<Priority>('important_not_urgent');
  const [estimatedDuration, setEstimatedDuration] = useState<number>(30);
  const [deadline, setDeadline] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (initialTask) {
      setTitle(initialTask.title);
      setDescription(initialTask.description || '');
      setCategory(initialTask.category);
      setPriority(initialTask.priority);
      setEstimatedDuration(initialTask.estimated_duration);
      setDeadline(initialTask.deadline.slice(0, 16));
    } else {
      // Default deadline: today at 18:00 or 4 hours from now
      const d = new Date();
      d.setHours(d.getHours() + 4, 0, 0, 0);
      const iso = new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
      setTitle('');
      setDescription('');
      setCategory('Work');
      setPriority('important_not_urgent');
      setEstimatedDuration(30);
      setDeadline(iso);
    }
    setError(null);
  }, [initialTask, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError('Please provide a task title.');
      return;
    }
    if (!deadline) {
      setError('Please set a deadline.');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      await onSubmit({
        title: title.trim(),
        description: description.trim(),
        category,
        priority,
        estimated_duration: Number(estimatedDuration),
        deadline
      });
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to save task.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const applyDeadlinePreset = (hoursFromNow: number) => {
    const d = new Date();
    d.setHours(d.getHours() + hoursFromNow);
    const iso = new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
    setDeadline(iso);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-in fade-in">
      <div className="bg-white dark:bg-slate-900 rounded-2xl w-full max-w-lg border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 dark:border-slate-800">
          <div>
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              {initialTask ? 'Edit Task' : 'Create New Task'}
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {initialTask ? 'Update task details and deadlines' : 'Add task to your intelligent schedule'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 overflow-y-auto flex-1">
          {error && (
            <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Title */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
              Task Title *
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Complete Machine Learning Assignment 3"
              className="w-full px-3.5 py-2.5 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800/80 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            />
          </div>

          {/* Category & Estimated Duration */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                <span className="flex items-center gap-1.5">
                  <Tag className="w-3.5 h-3.5 text-slate-400" />
                  Category
                </span>
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value as Category)}
                className="w-full px-3.5 py-2.5 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800/80 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                <span className="flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-slate-400" />
                  Estimated Duration (Minutes)
                </span>
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min="5"
                  max="480"
                  step="5"
                  required
                  value={estimatedDuration}
                  onChange={(e) => setEstimatedDuration(Number(e.target.value))}
                  className="w-full px-3.5 py-2.5 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800/80 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                />
                <span className="text-xs text-slate-400 font-medium whitespace-nowrap">
                  {estimatedDuration >= 60 ? `${(estimatedDuration / 60).toFixed(1)} hrs` : 'mins'}
                </span>
              </div>
            </div>
          </div>

          {/* Priority selection */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">
              <span className="flex items-center gap-1.5">
                <Flag className="w-3.5 h-3.5 text-slate-400" />
                Priority Matrix (Eisenhower)
              </span>
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {PRIORITIES.map((p) => {
                const isSelected = priority === p.value;
                return (
                  <button
                    key={p.value}
                    type="button"
                    onClick={() => setPriority(p.value)}
                    className={`p-2.5 rounded-xl text-left border transition-all ${
                      isSelected
                        ? `${p.color} ring-2 ring-blue-500/20`
                        : 'border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
                    }`}
                  >
                    <div className="text-xs font-bold leading-tight">{p.label}</div>
                    <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">
                      {p.desc}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Deadline */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                Deadline *
              </label>
              {/* Quick presets */}
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => applyDeadlinePreset(2)}
                  className="text-[10px] px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200"
                >
                  +2h
                </button>
                <button
                  type="button"
                  onClick={() => applyDeadlinePreset(6)}
                  className="text-[10px] px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200"
                >
                  Today
                </button>
                <button
                  type="button"
                  onClick={() => applyDeadlinePreset(24)}
                  className="text-[10px] px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200"
                >
                  Tomorrow
                </button>
              </div>
            </div>
            <input
              type="datetime-local"
              required
              value={deadline}
              onChange={(e) => setDeadline(e.target.value)}
              className="w-full px-3.5 py-2.5 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800/80 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
              Description / Notes (Optional)
            </label>
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Key notes, required materials, or completion criteria..."
              className="w-full px-3.5 py-2.5 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800/80 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 resize-none"
            />
          </div>

          {/* Footer Actions */}
          <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-2.5 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-xs shadow-blue-500/20 disabled:opacity-50"
            >
              {isSubmitting ? 'Saving...' : initialTask ? 'Save Changes' : 'Create Task'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
