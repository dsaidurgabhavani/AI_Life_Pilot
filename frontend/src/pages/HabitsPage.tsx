import React, { useState } from 'react';
import {
  Flame,
  Plus,
  CheckCircle2,
  Sparkles,
  BookOpen,
  Activity,
  Code,
  Trash2,
  Calendar,
  X,
  TrendingUp,
  Award
} from 'lucide-react';
import confetti from 'canvas-confetti';
import { Habit, HabitCreateInput } from '../types';

interface HabitsPageProps {
  habits: Habit[];
  onToggleHabitDay: (id: string, date: string, completed?: boolean) => Promise<void>;
  onCreateHabit: (habit: HabitCreateInput) => Promise<void>;
  onDeleteHabit: (id: string) => Promise<void>;
}

export const HabitsPage: React.FC<HabitsPageProps> = ({
  habits,
  onToggleHabitDay,
  onCreateHabit,
  onDeleteHabit
}) => {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('Personal');
  const [targetDays, setTargetDays] = useState(7);
  const [color, setColor] = useState('#3b82f6');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const colors = ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ec4899', '#06b6d4'];

  const handleToggle = async (habitId: string, date: string, currentCompleted: boolean) => {
    if (!currentCompleted) {
      confetti({
        particleCount: 40,
        spread: 45,
        origin: { y: 0.7 }
      });
    }
    await onToggleHabitDay(habitId, date, !currentCompleted);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError('Please provide a habit title.');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      await onCreateHabit({
        title: title.trim(),
        description: description.trim(),
        category,
        frequency: 'daily',
        target_days_per_week: Number(targetDays),
        color
      });
      setIsAddModalOpen(false);
      setTitle('');
      setDescription('');
    } catch (err: any) {
      setError(err.message || 'Failed to create habit');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this habit?')) {
      await onDeleteHabit(id);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Top Banner & Control */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h2 className="text-base md:text-lg font-bold text-slate-900 dark:text-white">
              Habit Consistency Tracker
            </h2>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 flex items-center gap-1">
              <Flame className="w-3 h-3 text-amber-500" />
              Streak Momentum
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Form lasting study, health, and work disciplines through visual chains and consistency tracking.
          </p>
        </div>

        <button
          onClick={() => setIsAddModalOpen(true)}
          className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-xs shadow-blue-500/20 active:scale-98 transition-all shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>New Habit</span>
        </button>
      </div>

      {/* Habits Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {habits.map((habit) => (
          <div
            key={habit.id}
            className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4 hover:border-slate-300 dark:hover:border-slate-700 transition-all"
          >
            {/* Header: Title, Category & Streak */}
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-start gap-3">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center text-white shrink-0 shadow-xs"
                  style={{ backgroundColor: habit.color || '#3b82f6' }}
                >
                  <Flame className="w-5 h-5 fill-current" />
                </div>
                <div>
                  <h3 className="font-bold text-sm text-slate-900 dark:text-white">
                    {habit.title}
                  </h3>
                  {habit.description && (
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                      {habit.description}
                    </p>
                  )}
                  <span className="inline-block mt-1 text-[10px] font-semibold px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                    {habit.category}
                  </span>
                </div>
              </div>

              {/* Streak Badge & Delete */}
              <div className="flex items-center gap-2">
                <div className="text-right">
                  <div className="flex items-center gap-1 font-bold text-sm text-amber-600 dark:text-amber-400">
                    <Flame className="w-4 h-4 fill-current" />
                    <span>{habit.current_streak}d streak</span>
                  </div>
                  <div className="text-[10px] text-slate-400">
                    Best: {habit.best_streak}d
                  </div>
                </div>

                <button
                  onClick={() => handleDelete(habit.id)}
                  className="p-1 rounded-lg text-slate-300 hover:text-rose-500 transition-colors"
                  title="Delete Habit"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Past 7-Days Interactive Tracker */}
            <div>
              <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                <span className="font-semibold text-slate-600 dark:text-slate-300 text-[11px]">
                  Past 7 Days
                </span>
                <span className="text-[11px] font-bold text-slate-700 dark:text-slate-300">
                  {habit.completion_rate_week}% weekly consistency
                </span>
              </div>

              <div className="grid grid-cols-7 gap-2">
                {habit.history.map((day) => (
                  <button
                    key={day.date}
                    onClick={() => handleToggle(habit.id, day.date, day.completed)}
                    className={`flex flex-col items-center justify-center p-2 rounded-xl border text-xs transition-all ${
                      day.completed
                        ? 'border-emerald-300 dark:border-emerald-800 bg-emerald-500 text-white shadow-xs'
                        : 'border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800 text-slate-400 hover:border-slate-300'
                    }`}
                  >
                    <span className="text-[10px] font-semibold opacity-80 uppercase">
                      {day.day_name}
                    </span>
                    <span className="text-xs font-bold mt-0.5">
                      {day.completed ? '✓' : '•'}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Weekly Progress bar */}
            <div className="space-y-1">
              <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden">
                <div
                  className="h-1.5 rounded-full transition-all duration-500"
                  style={{
                    width: `${habit.completion_rate_week}%`,
                    backgroundColor: habit.color || '#3b82f6'
                  }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Add Habit Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-in fade-in">
          <div className="bg-white dark:bg-slate-900 rounded-2xl w-full max-w-md border border-slate-200 dark:border-slate-800 shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <h3 className="font-bold text-base text-slate-900 dark:text-white">
                Create New Habit
              </h3>
              <button
                onClick={() => setIsAddModalOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {error && (
              <div className="p-3 rounded-xl bg-rose-50 text-rose-700 text-xs">
                {error}
              </div>
            )}

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                  Habit Title *
                </label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Read 20 pages or Solve 1 LeetCode problem"
                  className="w-full px-3.5 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                  Description
                </label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Why is this habit important to you?"
                  className="w-full px-3.5 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                    Category
                  </label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  >
                    <option value="Personal">Personal</option>
                    <option value="Study">Study</option>
                    <option value="Health">Health</option>
                    <option value="Work">Work</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                    Target Days/Week
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="7"
                    value={targetDays}
                    onChange={(e) => setTargetDays(Number(e.target.value))}
                    className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              {/* Color Selection */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                  Habit Color Theme
                </label>
                <div className="flex items-center gap-2">
                  {colors.map((c) => (
                    <button
                      key={c}
                      type="button"
                      onClick={() => setColor(c)}
                      className={`w-7 h-7 rounded-full transition-transform ${
                        color === c ? 'scale-110 ring-2 ring-blue-500 ring-offset-2' : ''
                      }`}
                      style={{ backgroundColor: c }}
                    />
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-xs disabled:opacity-50"
                >
                  {isSubmitting ? 'Creating...' : 'Create Habit'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
