import React, { useState } from 'react';
import {
  Settings,
  User,
  Clock,
  Sparkles,
  Sun,
  Moon,
  Bell,
  Key,
  RotateCcw,
  Trash2,
  Check,
  AlertCircle
} from 'lucide-react';
import confetti from 'canvas-confetti';
import { UserSettings } from '../types';
import { useTheme } from '../context/ThemeContext';

interface SettingsPageProps {
  settings: UserSettings | null;
  onUpdateSettings: (updates: Partial<UserSettings>) => Promise<void>;
  onResetDemoData: () => Promise<void>;
  onClearUserData: () => Promise<void>;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({
  settings,
  onUpdateSettings,
  onResetDemoData,
  onClearUserData
}) => {
  const { theme, setTheme } = useTheme();

  const [userName, setUserName] = useState(settings?.user_name || 'Alex Morgan');
  const [workStart, setWorkStart] = useState(settings?.work_start_time || '09:00');
  const [workEnd, setWorkEnd] = useState(settings?.work_end_time || '18:00');
  const [bufferMins, setBufferMins] = useState(settings?.buffer_minutes || 15);
  const [pomodoroWork, setPomodoroWork] = useState(settings?.pomodoro_work_duration || 25);
  const [pomodoroBreak, setPomodoroBreak] = useState(settings?.pomodoro_break_duration || 5);
  const [pomodoroLongBreak, setPomodoroLongBreak] = useState(settings?.pomodoro_long_break_duration || 15);
  const [geminiApiKey, setGeminiApiKey] = useState(settings?.gemini_api_key || '');
  const [notifications, setNotifications] = useState(settings?.notifications_enabled ?? true);

  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsSaving(true);
      setError(null);
      await onUpdateSettings({
        user_name: userName.trim(),
        work_start_time: workStart,
        work_end_time: workEnd,
        buffer_minutes: Number(bufferMins),
        pomodoro_work_duration: Number(pomodoroWork),
        pomodoro_break_duration: Number(pomodoroBreak),
        pomodoro_long_break_duration: Number(pomodoroLongBreak),
        notifications_enabled: notifications,
        gemini_api_key: geminiApiKey.trim()
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to update settings');
    } finally {
      setIsSaving(false);
    }
  };

  const handleResetDemo = async () => {
    if (window.confirm('Reset all tasks, habits, and focus logs to realistic demo data?')) {
      await onResetDemoData();
      confetti({
        particleCount: 50,
        spread: 60,
        origin: { y: 0.6 }
      });
    }
  };

  const handleClear = async () => {
    if (window.confirm('Warning: This will clear all tasks, habits, and focus logs. Continue?')) {
      await onClearUserData();
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Top Banner */}
      <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-1">
        <h2 className="text-base md:text-lg font-bold text-slate-900 dark:text-white">
          Settings & Preferences
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Personalize your daily schedule parameters, focus intervals, appearance, and AI engine settings.
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {saveSuccess && (
          <div className="p-3.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 text-xs flex items-center gap-2">
            <Check className="w-4 h-4 shrink-0" />
            <span>Settings successfully saved and applied!</span>
          </div>
        )}

        {error && (
          <div className="p-3.5 rounded-xl bg-rose-50 text-rose-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Profile & Name */}
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
          <div className="flex items-center gap-2 text-slate-900 dark:text-white font-bold text-sm">
            <User className="w-4 h-4 text-blue-500" />
            <span>User Profile</span>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
              Display Name
            </label>
            <input
              type="text"
              value={userName}
              onChange={(e) => setUserName(e.target.value)}
              className="w-full max-w-md px-3.5 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            />
          </div>
        </div>

        {/* Schedule & Working Hours */}
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
          <div className="flex items-center gap-2 text-slate-900 dark:text-white font-bold text-sm">
            <Clock className="w-4 h-4 text-indigo-500" />
            <span>Daily Schedule Hours & Buffers</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Work Window Start
              </label>
              <input
                type="time"
                value={workStart}
                onChange={(e) => setWorkStart(e.target.value)}
                className="w-full px-3.5 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Work Window End
              </label>
              <input
                type="time"
                value={workEnd}
                onChange={(e) => setWorkEnd(e.target.value)}
                className="w-full px-3.5 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Buffer Between Tasks (Minutes)
              </label>
              <input
                type="number"
                min="0"
                max="60"
                value={bufferMins}
                onChange={(e) => setBufferMins(Number(e.target.value))}
                className="w-full px-3.5 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
              />
            </div>
          </div>
        </div>

        {/* Pomodoro Timer Configuration */}
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
          <div className="flex items-center gap-2 text-slate-900 dark:text-white font-bold text-sm">
            <Sparkles className="w-4 h-4 text-emerald-500" />
            <span>Focus & Pomodoro Timer Durations</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Focus Sprint (Minutes)
              </label>
              <input
                type="number"
                min="5"
                max="120"
                value={pomodoroWork}
                onChange={(e) => setPomodoroWork(Number(e.target.value))}
                className="w-full px-3.5 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Short Break (Minutes)
              </label>
              <input
                type="number"
                min="1"
                max="30"
                value={pomodoroBreak}
                onChange={(e) => setPomodoroBreak(Number(e.target.value))}
                className="w-full px-3.5 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Long Break (Minutes)
              </label>
              <input
                type="number"
                min="5"
                max="60"
                value={pomodoroLongBreak}
                onChange={(e) => setPomodoroLongBreak(Number(e.target.value))}
                className="w-full px-3.5 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
              />
            </div>
          </div>
        </div>

        {/* Theme & Notifications */}
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
          <div className="flex items-center gap-2 text-slate-900 dark:text-white font-bold text-sm">
            <Sun className="w-4 h-4 text-amber-500" />
            <span>Appearance & Notifications</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Theme
              </label>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setTheme('light')}
                  className={`flex-1 py-2 rounded-xl text-xs font-semibold border flex items-center justify-center gap-1.5 transition-colors ${
                    theme === 'light'
                      ? 'border-blue-500 bg-blue-50 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                      : 'border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400'
                  }`}
                >
                  <Sun className="w-4 h-4 text-amber-500" />
                  <span>Light Mode</span>
                </button>

                <button
                  type="button"
                  onClick={() => setTheme('dark')}
                  className={`flex-1 py-2 rounded-xl text-xs font-semibold border flex items-center justify-center gap-1.5 transition-colors ${
                    theme === 'dark'
                      ? 'border-blue-500 bg-blue-50 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                      : 'border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400'
                  }`}
                >
                  <Moon className="w-4 h-4 text-indigo-400" />
                  <span>Dark Mode</span>
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                In-App Notifications
              </label>
              <label className="flex items-center gap-2.5 p-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60 cursor-pointer">
                <input
                  type="checkbox"
                  checked={notifications}
                  onChange={(e) => setNotifications(e.target.checked)}
                  className="rounded text-blue-600 focus:ring-blue-500 w-4 h-4"
                />
                <span className="text-xs font-medium text-slate-800 dark:text-slate-200">
                  Notify on urgent deadlines and overload
                </span>
              </label>
            </div>
          </div>
        </div>

        {/* AI Provider Settings */}
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-slate-900 dark:text-white font-bold text-sm">
              <Key className="w-4 h-4 text-purple-500" />
              <span>AI Provider Configuration</span>
            </div>
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400">
              Reliable Fallback Enabled
            </span>
          </div>

          <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
            AI LifePilot features a built-in <strong>Smart Heuristic Engine</strong> that runs locally with zero external dependencies. You can optionally supply your Google Gemini API key below to unlock generative LLM capabilities.
          </p>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
              Google Gemini API Key (Optional)
            </label>
            <input
              type="password"
              value={geminiApiKey}
              onChange={(e) => setGeminiApiKey(e.target.value)}
              placeholder="AIzaSy..."
              className="w-full px-3.5 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            />
          </div>
        </div>

        {/* Save Changes button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isSaving}
            className="px-6 py-2.5 rounded-xl font-semibold text-xs bg-blue-600 hover:bg-blue-700 text-white shadow-xs shadow-blue-500/20 disabled:opacity-50"
          >
            {isSaving ? 'Saving Changes...' : 'Save Preferences'}
          </button>
        </div>
      </form>

      {/* Demo Data Management */}
      <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
        <h3 className="font-bold text-sm text-slate-900 dark:text-white">
          Demo Data & Database Management
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Reset demo data to preview AI LifePilot with rich sample tasks, active habit streaks, and focus sessions, or clear all data to start with a clean slate.
        </p>

        <div className="flex flex-wrap items-center gap-3 pt-2">
          <button
            type="button"
            onClick={handleResetDemo}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 hover:bg-indigo-100 border border-indigo-200/60 dark:border-indigo-800/40"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Realistic Demo Data</span>
          </button>

          <button
            type="button"
            onClick={handleClear}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300 hover:bg-rose-100 border border-rose-200/60 dark:border-rose-900/40"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear All User Data</span>
          </button>
        </div>
      </div>
    </div>
  );
};
