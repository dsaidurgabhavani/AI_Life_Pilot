import React from 'react';
import {
  BarChart3,
  TrendingUp,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Flame,
  Award,
  Sparkles,
  Info
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { AnalyticsOverview } from '../types';

interface AnalyticsPageProps {
  analytics: AnalyticsOverview | null;
}

const CATEGORY_COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ec4899', '#06b6d4'];

export const AnalyticsPage: React.FC<AnalyticsPageProps> = ({ analytics }) => {
  if (!analytics) {
    return (
      <div className="py-20 text-center text-slate-400">
        Loading analytics overview...
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Top Banner & Productivity Score Gauge */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Productivity Score Card */}
        <div className="p-6 rounded-2xl bg-gradient-to-br from-indigo-900 via-indigo-800 to-slate-900 text-white shadow-xl flex flex-col justify-between">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-white/10 text-indigo-200 border border-white/10">
              <Award className="w-3.5 h-3.5 text-amber-400" />
              <span>LifePilot Productivity Index</span>
            </div>
            <h3 className="text-xl font-bold tracking-tight">Overall Performance</h3>
            <p className="text-xs text-indigo-200/80">
              Computed from task velocity, habit consistency, deep focus minutes, and deadline reliability.
            </p>
          </div>

          <div className="my-6 flex items-baseline gap-3">
            <span className="font-mono text-6xl font-black text-white tracking-tight">
              {analytics.productivity_score}
            </span>
            <span className="text-lg font-bold text-indigo-300">/ 100</span>
          </div>

          <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
            <div
              className="bg-gradient-to-r from-amber-400 to-emerald-400 h-2 rounded-full transition-all duration-700"
              style={{ width: `${analytics.productivity_score}%` }}
            />
          </div>
        </div>

        {/* 4 Summary Cards in 2x2 grid */}
        <div className="lg:col-span-2 grid grid-cols-2 gap-4">
          <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xs space-y-1">
            <div className="flex items-center justify-between text-slate-500">
              <span className="text-xs font-semibold">Task Completion Rate</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            </div>
            <div className="text-2xl font-bold text-slate-900 dark:text-white">
              {analytics.completion_rate_percent}%
            </div>
            <div className="text-[11px] text-slate-400">
              {analytics.completed_tasks} completed of {analytics.total_tasks} total
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xs space-y-1">
            <div className="flex items-center justify-between text-slate-500">
              <span className="text-xs font-semibold">Overdue Tasks</span>
              <AlertTriangle className={`w-4 h-4 ${analytics.overdue_tasks > 0 ? 'text-rose-500' : 'text-slate-400'}`} />
            </div>
            <div className={`text-2xl font-bold ${analytics.overdue_tasks > 0 ? 'text-rose-600' : 'text-slate-900 dark:text-white'}`}>
              {analytics.overdue_tasks}
            </div>
            <div className="text-[11px] text-slate-400">
              {analytics.pending_tasks} tasks currently in queue
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xs space-y-1">
            <div className="flex items-center justify-between text-slate-500">
              <span className="text-xs font-semibold">Focus Time Logged</span>
              <Clock className="w-4 h-4 text-indigo-500" />
            </div>
            <div className="text-2xl font-bold text-slate-900 dark:text-white">
              {analytics.total_focus_minutes}m
            </div>
            <div className="text-[11px] text-slate-400">
              Study: {analytics.study_focus_minutes}m • Work: {analytics.work_focus_minutes}m
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xs space-y-1">
            <div className="flex items-center justify-between text-slate-500">
              <span className="text-xs font-semibold">Weekly Habit Consistency</span>
              <Flame className="w-4 h-4 text-amber-500" />
            </div>
            <div className="text-2xl font-bold text-slate-900 dark:text-white">
              {analytics.overall_habit_consistency_percent}%
            </div>
            <div className="text-[11px] text-slate-400">
              Across {analytics.active_habits_count} active daily routines
            </div>
          </div>
        </div>
      </div>

      {/* Dynamic Data-Driven Smart Insights */}
      <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-indigo-500" />
          <h3 className="font-bold text-sm text-slate-900 dark:text-white">
            Data-Driven Productivity Insights
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {analytics.smart_insights.map((insight, idx) => (
            <div
              key={idx}
              className="p-3.5 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-800/40 text-xs text-slate-700 dark:text-slate-300 leading-relaxed"
            >
              {insight}
            </div>
          ))}
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Weekly Focus Minutes & Completed Tasks */}
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-sm text-slate-900 dark:text-white">
                Daily Focus Minutes (Past 7 Days)
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Deep work session duration logged per day
              </p>
            </div>
            <Clock className="w-4 h-4 text-blue-500" />
          </div>

          <div className="h-64 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={analytics.weekly_trend}>
                <defs>
                  <linearGradient id="focusGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    borderRadius: '12px',
                    fontSize: '12px',
                    backgroundColor: '#1e293b',
                    color: '#fff',
                    border: 'none'
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="focus_minutes"
                  name="Focus Minutes"
                  stroke="#3b82f6"
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#focusGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Category Breakdown */}
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-sm text-slate-900 dark:text-white">
                Category Distribution (Task Count)
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Workload allocation across Study, Work, Health & Personal
              </p>
            </div>
            <BarChart3 className="w-4 h-4 text-indigo-500" />
          </div>

          <div className="h-64 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={analytics.category_distribution}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                <XAxis dataKey="category" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    borderRadius: '12px',
                    fontSize: '12px',
                    backgroundColor: '#1e293b',
                    color: '#fff',
                    border: 'none'
                  }}
                />
                <Bar dataKey="count" name="Tasks" radius={[6, 6, 0, 0]}>
                  {analytics.category_distribution.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
