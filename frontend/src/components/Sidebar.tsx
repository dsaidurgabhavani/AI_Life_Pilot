import React from 'react';
import {
  LayoutDashboard,
  CalendarClock,
  CheckSquare,
  Timer,
  Bot,
  Flame,
  BarChart3,
  Settings,
  Sparkles,
  Sun,
  Moon,
  X,
  AlertCircle
} from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

export type NavItemKey =
  | 'dashboard'
  | 'planner'
  | 'tasks'
  | 'focus'
  | 'assistant'
  | 'habits'
  | 'analytics'
  | 'settings';

interface SidebarProps {
  currentTab: NavItemKey;
  onSelectTab: (tab: NavItemKey) => void;
  overdueCount: number;
  isOpenMobile: boolean;
  onCloseMobile: () => void;
  userName: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  overdueCount,
  isOpenMobile,
  onCloseMobile,
  userName
}) => {
  const { theme, toggleTheme } = useTheme();

  const navItems = [
    { key: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { key: 'planner', label: 'AI Planner', icon: CalendarClock, badge: 'Smart' },
    { key: 'tasks', label: 'My Tasks', icon: CheckSquare, alertCount: overdueCount },
    { key: 'focus', label: 'Study & Work', icon: Timer, highlight: true },
    { key: 'assistant', label: 'AI Assistant', icon: Bot },
    { key: 'habits', label: 'Habits', icon: Flame },
    { key: 'analytics', label: 'Analytics', icon: BarChart3 },
    { key: 'settings', label: 'Settings', icon: Settings },
  ] as const;

  return (
    <>
      {/* Mobile backdrop */}
      {isOpenMobile && (
        <div
          className="fixed inset-0 bg-black/40 backdrop-blur-xs z-40 md:hidden"
          onClick={onCloseMobile}
        />
      )}

      {/* Sidebar container */}
      <aside
        className={`fixed md:sticky top-0 left-0 h-screen z-50 flex flex-col justify-between w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 transition-transform duration-200 ease-in-out ${
          isOpenMobile ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        <div>
          {/* Logo & Brand Header */}
          <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100 dark:border-slate-800/80">
            <div className="flex items-center gap-2.5">
              <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-sky-400 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
                <Sparkles className="w-5 h-5 animate-pulse" />
              </div>
              <div>
                <span className="font-bold text-lg tracking-tight text-slate-900 dark:text-white">
                  Life<span className="text-blue-600 dark:text-blue-400">Pilot</span>
                </span>
                <span className="block text-[10px] uppercase font-semibold tracking-wider text-slate-400 dark:text-slate-500">
                  AI Daily Assistant
                </span>
              </div>
            </div>

            {/* Mobile close button */}
            <button
              onClick={onCloseMobile}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 md:hidden"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentTab === item.key;

              return (
                <button
                  key={item.key}
                  onClick={() => {
                    onSelectTab(item.key as NavItemKey);
                    onCloseMobile();
                  }}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 shadow-xs'
                      : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100/80 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-100'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon
                      className={`w-4 h-4 transition-colors ${
                        isActive
                          ? 'text-blue-600 dark:text-blue-400'
                          : 'text-slate-400 group-hover:text-slate-600 dark:text-slate-500'
                      }`}
                    />
                    <span>{item.label}</span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    {'badge' in item && item.badge && (
                      <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-md bg-blue-100 text-blue-700 dark:bg-blue-800/40 dark:text-blue-300">
                        {item.badge}
                      </span>
                    )}

                    {'alertCount' in item && typeof item.alertCount === 'number' && item.alertCount > 0 && (
                      <span className="flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-400">
                        <AlertCircle className="w-3 h-3" />
                        {item.alertCount}
                      </span>
                    )}
                  </div>
                </button>
              );
            })}
          </nav>
        </div>

        {/* User Card & Theme Switcher */}
        <div className="p-4 border-t border-slate-100 dark:border-slate-800/80 space-y-3">
          <div className="flex items-center justify-between bg-slate-50 dark:bg-slate-800/60 p-2.5 rounded-xl">
            <div className="flex items-center gap-2.5 overflow-hidden">
              <div className="w-8 h-8 rounded-full bg-blue-600/10 dark:bg-blue-400/10 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold text-xs shrink-0">
                {userName.charAt(0)}
              </div>
              <div className="truncate">
                <div className="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate">
                  {userName}
                </div>
                <div className="text-[10px] text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
                  Pilot Active
                </div>
              </div>
            </div>

            <button
              onClick={toggleTheme}
              title={theme === 'light' ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
              className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-white dark:hover:bg-slate-700 transition-colors shadow-2xs"
            >
              {theme === 'light' ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4 text-amber-400" />}
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};
