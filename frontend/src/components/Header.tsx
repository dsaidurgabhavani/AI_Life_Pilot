import React from 'react';
import {
  Menu,
  Plus,
  Bell,
  Cpu,
  Calendar,
  Layers
} from 'lucide-react';
import { NavItemKey } from './Sidebar';

interface HeaderProps {
  currentTab: NavItemKey;
  onOpenMobileSidebar: () => void;
  onOpenAddTaskModal: () => void;
  onOpenGoalBreakdownModal: () => void;
  onToggleNotifications: () => void;
  overdueCount: number;
  engineUsed: string;
}

const titles: Record<NavItemKey, { title: string; subtitle: string }> = {
  dashboard: {
    title: 'Daily Dashboard',
    subtitle: 'Streamline your day, tackle high-impact priorities, and maintain momentum.'
  },
  planner: {
    title: 'AI Daily Planner',
    subtitle: 'Intelligent schedule optimization with automatic priority & buffer management.'
  },
  tasks: {
    title: 'Smart Deadline Manager',
    subtitle: 'Manage tasks, track upcoming deadlines, and avoid schedule bottlenecks.'
  },
  focus: {
    title: 'Smart Study & Work Mode',
    subtitle: 'Pomodoro focus timer, deep work intervals, and session completion tracking.'
  },
  assistant: {
    title: 'Intelligent AI Assistant',
    subtitle: 'Conversational productivity coach, schedule optimization, and goal breakdown.'
  },
  habits: {
    title: 'Habit Consistency Tracker',
    subtitle: 'Build lasting daily routines with visual streaks and 7-day tracking.'
  },
  analytics: {
    title: 'Productivity Analytics',
    subtitle: 'Data-driven insights, focus metrics, and actual task completion rates.'
  },
  settings: {
    title: 'Settings & Preferences',
    subtitle: 'Configure work hours, buffer intervals, themes, and AI provider.'
  }
};

export const Header: React.FC<HeaderProps> = ({
  currentTab,
  onOpenMobileSidebar,
  onOpenAddTaskModal,
  onOpenGoalBreakdownModal,
  onToggleNotifications,
  overdueCount,
  engineUsed
}) => {
  const currentInfo = titles[currentTab] || { title: 'AI LifePilot', subtitle: '' };
  const todayFormatted = new Intl.DateTimeFormat('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric'
  }).format(new Date());

  return (
    <header className="sticky top-0 z-30 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 px-4 md:px-8 py-3.5 transition-colors">
      <div className="flex items-center justify-between gap-4">
        {/* Left: Hamburger & Titles */}
        <div className="flex items-center gap-3">
          <button
            onClick={onOpenMobileSidebar}
            className="p-2 -ml-2 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 md:hidden"
            aria-label="Open navigation menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg md:text-xl font-bold tracking-tight text-slate-900 dark:text-white">
                {currentInfo.title}
              </h1>
              {/* Engine badge */}
              <div className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-200/60 dark:border-emerald-800/40">
                <Cpu className="w-3 h-3 text-emerald-500" />
                <span>{engineUsed === 'gemini' ? 'Gemini AI Active' : 'Smart Heuristic Engine'}</span>
              </div>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 hidden sm:block truncate max-w-lg">
              {currentInfo.subtitle}
            </p>
          </div>
        </div>

        {/* Right Action Controls */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Today Date pill */}
          <div className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-xs font-medium text-slate-700 dark:text-slate-300">
            <Calendar className="w-3.5 h-3.5 text-blue-500" />
            <span>{todayFormatted}</span>
          </div>

          {/* Goal Breakdown Quick Action */}
          <button
            onClick={onOpenGoalBreakdownModal}
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 hover:bg-indigo-100 dark:hover:bg-indigo-900/50 border border-indigo-200/60 dark:border-indigo-800/40 transition-colors shadow-2xs"
            title="Decompose a large goal into manageable tasks"
          >
            <Layers className="w-3.5 h-3.5 text-indigo-500" />
            <span>Breakdown Goal</span>
          </button>

          {/* Add Task Primary Action */}
          <button
            onClick={onOpenAddTaskModal}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-xs shadow-blue-500/20 active:scale-98 transition-all"
          >
            <Plus className="w-4 h-4" />
            <span className="hidden xs:inline">New Task</span>
          </button>

          {/* Notifications Bell */}
          <button
            onClick={onToggleNotifications}
            className="relative p-2 rounded-xl text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            aria-label="Open deadline notifications"
          >
            <Bell className="w-4 h-4" />
            {overdueCount > 0 && (
              <span className="absolute top-1 right-1 flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500" />
              </span>
            )}
          </button>
        </div>
      </div>
    </header>
  );
};
