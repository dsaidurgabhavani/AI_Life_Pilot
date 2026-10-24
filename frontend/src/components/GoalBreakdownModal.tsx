import React, { useState } from 'react';
import { X, Sparkles, Layers, ArrowRight, CheckCircle2, Clock, Calendar } from 'lucide-react';
import confetti from 'canvas-confetti';
import { api } from '../api';
import { GoalBreakdown, SubtaskItem } from '../types';

interface GoalBreakdownModalProps {
  isOpen: boolean;
  onClose: () => void;
  onTasksImported: () => void;
}

export const GoalBreakdownModal: React.FC<GoalBreakdownModalProps> = ({
  isOpen,
  onClose,
  onTasksImported
}) => {
  const [goalTitle, setGoalTitle] = useState('');
  const [category, setCategory] = useState('Study');
  const [isLoading, setIsLoading] = useState(false);
  const [breakdown, setBreakdown] = useState<GoalBreakdown | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleDecompose = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!goalTitle.trim()) {
      setError('Please enter a goal to break down.');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      const res = await api.breakdownGoal(goalTitle.trim(), category);
      setBreakdown(res);
    } catch (err: any) {
      setError(err.message || 'Failed to decompose goal.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleImportAll = async () => {
    if (!breakdown || !breakdown.subtasks.length) return;

    try {
      setIsImporting(true);
      await api.importSubtasks(breakdown.subtasks);
      confetti({
        particleCount: 80,
        spread: 60,
        origin: { y: 0.6 }
      });
      onTasksImported();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to import subtasks.');
    } finally {
      setIsImporting(false);
    }
  };

  const sampleGoals = [
    'Prepare for Distributed Systems Final Exam',
    'Build and launch AI LifePilot sprint web app',
    'Prepare pitch deck & 10m client presentation',
    'Organize weekly health, meal prep & workout routine'
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-in fade-in">
      <div className="bg-white dark:bg-slate-900 rounded-2xl w-full max-w-xl border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                Decompose Large Goal
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300">
                  AI Actionable Roadmap
                </span>
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Transform an overwhelming objective into bite-sized, prioritized daily tasks.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1">
          {error && (
            <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-xs">
              {error}
            </div>
          )}

          {!breakdown ? (
            <form onSubmit={handleDecompose} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                  What is your high-level goal?
                </label>
                <input
                  type="text"
                  required
                  value={goalTitle}
                  onChange={(e) => setGoalTitle(e.target.value)}
                  placeholder="e.g. Master React and TypeScript by building 3 real-world projects"
                  className="w-full px-3.5 py-2.5 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800/80 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                  Category
                </label>
                <div className="flex flex-wrap gap-2">
                  {['Study', 'Work', 'Health', 'Personal'].map((cat) => (
                    <button
                      key={cat}
                      type="button"
                      onClick={() => setCategory(cat)}
                      className={`px-3 py-1.5 rounded-xl text-xs font-medium border transition-colors ${
                        category === cat
                          ? 'border-indigo-600 bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300'
                          : 'border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400'
                      }`}
                    >
                      {cat}
                    </button>
                  ))}
                </div>
              </div>

              {/* Sample goal inspiration */}
              <div>
                <span className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider block mb-2">
                  Quick Inspiration:
                </span>
                <div className="space-y-1.5">
                  {sampleGoals.map((sample, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setGoalTitle(sample)}
                      className="w-full text-left p-2 rounded-lg text-xs bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 transition-colors flex items-center justify-between"
                    >
                      <span>{sample}</span>
                      <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
                    </button>
                  ))}
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-2.5 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-md shadow-indigo-500/20 flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <Sparkles className="w-4 h-4 animate-spin" />
                {isLoading ? 'Decomposing Goal with AI...' : 'Decompose Goal into Actionable Tasks'}
              </button>
            </form>
          ) : (
            <div className="space-y-4">
              <div className="p-3.5 rounded-xl bg-indigo-50/70 dark:bg-indigo-950/30 border border-indigo-100 dark:border-indigo-900/60">
                <div className="text-xs font-bold text-indigo-900 dark:text-indigo-200">
                  {breakdown.goal_title}
                </div>
                <p className="text-xs text-indigo-700 dark:text-indigo-300 mt-1">
                  {breakdown.explanation}
                </p>
                <div className="mt-2 text-[10px] text-slate-400 font-medium">
                  Engine: {breakdown.engine_used === 'gemini' ? 'Google Gemini 2.5 Flash' : 'Smart Heuristic Planner'}
                </div>
              </div>

              {/* Subtasks List */}
              <div className="space-y-2">
                <div className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Generated Subtasks ({breakdown.subtasks.length}):
                </div>
                {breakdown.subtasks.map((st: SubtaskItem, index: number) => (
                  <div
                    key={index}
                    className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800/60 space-y-1.5"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold text-xs text-slate-900 dark:text-white">
                        {index + 1}. {st.title}
                      </span>
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-blue-50 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
                        {st.priority === 'urgent_important' ? 'Priority 1' : 'Priority 2'}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400">
                      {st.description}
                    </p>
                    <div className="flex items-center gap-3 text-[11px] text-slate-400">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3 text-slate-400" />
                        {st.estimated_duration} mins
                      </span>
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3 text-slate-400" />
                        {st.suggested_day_offset === 0 ? 'Today' : `+${st.suggested_day_offset} Day(s)`}
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setBreakdown(null)}
                  className="px-3.5 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  Back
                </button>
                <button
                  type="button"
                  onClick={handleImportAll}
                  disabled={isImporting}
                  className="flex-1 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white shadow-md shadow-emerald-500/20 flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  {isImporting ? 'Importing Tasks...' : `Import All ${breakdown.subtasks.length} Tasks to My Schedule`}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
