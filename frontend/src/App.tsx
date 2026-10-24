import React, { useState, useEffect, useCallback } from 'react';
import { api } from './api';
import {
  Task,
  DailySchedule,
  Habit,
  FocusSession,
  FocusStats,
  UserSettings,
  AnalyticsOverview,
  TaskCreateInput
} from './types';
import { Sidebar, NavItemKey } from './components/Sidebar';
import { Header } from './components/Header';
import { TaskModal } from './components/TaskModal';
import { GoalBreakdownModal } from './components/GoalBreakdownModal';
import { NotificationDrawer } from './components/NotificationDrawer';

import { DashboardPage } from './pages/DashboardPage';
import { PlannerPage } from './pages/PlannerPage';
import { TasksPage } from './pages/TasksPage';
import { FocusPage } from './pages/FocusPage';
import { AssistantPage } from './pages/AssistantPage';
import { HabitsPage } from './pages/HabitsPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { SettingsPage } from './pages/SettingsPage';
import { ThemeProvider } from './context/ThemeContext';
import { RefreshCw } from 'lucide-react';

export function AppContent() {
  const [currentTab, setCurrentTab] = useState<NavItemKey>('dashboard');
  const [tasks, setTasks] = useState<Task[]>([]);
  const [recommendedTask, setRecommendedTask] = useState<Task | null>(null);
  const [todaySchedule, setTodaySchedule] = useState<DailySchedule | null>(null);
  const [habits, setHabits] = useState<Habit[]>([]);
  const [focusStats, setFocusStats] = useState<FocusStats | null>(null);
  const [focusSessions, setFocusSessions] = useState<FocusSession[]>([]);
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);

  // Modals & Drawers state
  const [isAddTaskModalOpen, setIsAddTaskModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [isGoalBreakdownModalOpen, setIsGoalBreakdownModalOpen] = useState(false);
  const [isNotificationDrawerOpen, setIsNotificationDrawerOpen] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  // Active focus sprint task (when user clicks "Focus Now" from any view)
  const [activeFocusTask, setActiveFocusTask] = useState<Task | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isRegeneratingSchedule, setIsRegeneratingSchedule] = useState(false);

  const refreshAllData = useCallback(async () => {
    try {
      const [
        tasksData,
        recTaskData,
        scheduleData,
        habitsData,
        focusStatsData,
        focusSessionsData,
        settingsData,
        analyticsData
      ] = await Promise.all([
        api.getTasks(),
        api.getNextRecommendedTask(),
        api.getTodaySchedule(),
        api.getHabits(),
        api.getFocusStats(),
        api.getFocusSessions(),
        api.getSettings(),
        api.getAnalyticsOverview()
      ]);

      setTasks(tasksData);
      setRecommendedTask(recTaskData);
      setTodaySchedule(scheduleData);
      setHabits(habitsData);
      setFocusStats(focusStatsData);
      setFocusSessions(focusSessionsData);
      setSettings(settingsData);
      setAnalytics(analyticsData);
    } catch (err) {
      console.error('Failed to load application data:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshAllData();
  }, [refreshAllData]);

  // Task Actions
  const handleCreateOrUpdateTask = async (data: TaskCreateInput) => {
    if (editingTask) {
      await api.updateTask(editingTask.id, data);
      setEditingTask(null);
    } else {
      await api.createTask(data);
    }
    await refreshAllData();
  };

  const handleToggleTask = async (id: string) => {
    await api.toggleTask(id);
    await refreshAllData();
  };

  const handleDeleteTask = async (id: string) => {
    await api.deleteTask(id);
    await refreshAllData();
  };

  const handleStartFocusOnTask = (task: Task) => {
    setActiveFocusTask(task);
    setCurrentTab('focus');
  };

  // Schedule Regeneration
  const handleRegenerateSchedule = async () => {
    try {
      setIsRegeneratingSchedule(true);
      const res = await api.generateSchedule();
      setTodaySchedule(res);
      await refreshAllData();
    } finally {
      setIsRegeneratingSchedule(false);
    }
  };

  // Habit Actions
  const handleToggleHabitDay = async (id: string, date: string, completed?: boolean) => {
    await api.toggleHabitDay(id, date, completed);
    await refreshAllData();
  };

  const handleCreateHabit = async (habitData: any) => {
    await api.createHabit(habitData);
    await refreshAllData();
  };

  const handleDeleteHabit = async (id: string) => {
    await api.deleteHabit(id);
    await refreshAllData();
  };

  // Focus Session Record
  const handleRecordFocusSession = async (sessionData: any) => {
    await api.recordFocusSession(sessionData);
    await refreshAllData();
  };

  // Settings & Database Management
  const handleUpdateSettings = async (updates: Partial<UserSettings>) => {
    const updated = await api.updateSettings(updates);
    setSettings(updated);
    await refreshAllData();
  };

  const handleResetDemoData = async () => {
    await api.resetDemoData();
    await refreshAllData();
  };

  const handleClearUserData = async () => {
    await api.clearUserData();
    await refreshAllData();
  };

  const overdueCount = tasks.filter((t) => t.is_overdue && t.status !== 'completed').length;
  const engineUsed = todaySchedule?.engine_used || 'deterministic';

  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white space-y-3">
        <div className="w-10 h-10 rounded-2xl bg-blue-600 flex items-center justify-center text-white shadow-xl shadow-blue-500/20">
          <RefreshCw className="w-5 h-5 animate-spin" />
        </div>
        <p className="text-xs font-semibold text-slate-400">Loading AI LifePilot...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors">
      {/* Sidebar Navigation */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        overdueCount={overdueCount}
        isOpenMobile={isMobileSidebarOpen}
        onCloseMobile={() => setIsMobileSidebarOpen(false)}
        userName={settings?.user_name || 'User'}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 min-h-screen">
        {/* Header Bar */}
        <Header
          currentTab={currentTab}
          onOpenMobileSidebar={() => setIsMobileSidebarOpen(true)}
          onOpenAddTaskModal={() => {
            setEditingTask(null);
            setIsAddTaskModalOpen(true);
          }}
          onOpenGoalBreakdownModal={() => setIsGoalBreakdownModalOpen(true)}
          onToggleNotifications={() => setIsNotificationDrawerOpen((prev) => !prev)}
          overdueCount={overdueCount}
          engineUsed={engineUsed}
        />

        {/* Page Content Body */}
        <main className="flex-1 p-4 md:p-8 overflow-y-auto">
          {currentTab === 'dashboard' && (
            <DashboardPage
              tasks={tasks}
              recommendedTask={recommendedTask}
              todaySchedule={todaySchedule}
              habits={habits}
              focusStats={focusStats}
              onNavigateTab={setCurrentTab}
              onOpenAddTask={() => {
                setEditingTask(null);
                setIsAddTaskModalOpen(true);
              }}
              onOpenGoalBreakdown={() => setIsGoalBreakdownModalOpen(true)}
              onToggleTask={handleToggleTask}
              onStartFocusOnTask={handleStartFocusOnTask}
            />
          )}

          {currentTab === 'planner' && (
            <PlannerPage
              schedule={todaySchedule}
              tasks={tasks}
              onRegenerate={handleRegenerateSchedule}
              onOpenAddTask={() => {
                setEditingTask(null);
                setIsAddTaskModalOpen(true);
              }}
              onToggleTask={handleToggleTask}
              onStartFocusOnTask={handleStartFocusOnTask}
              isRegenerating={isRegeneratingSchedule}
            />
          )}

          {currentTab === 'tasks' && (
            <TasksPage
              tasks={tasks}
              onOpenAddTask={() => {
                setEditingTask(null);
                setIsAddTaskModalOpen(true);
              }}
              onEditTask={(task) => {
                setEditingTask(task);
                setIsAddTaskModalOpen(true);
              }}
              onDeleteTask={handleDeleteTask}
              onToggleTask={handleToggleTask}
              onStartFocus={handleStartFocusOnTask}
            />
          )}

          {currentTab === 'focus' && (
            <FocusPage
              tasks={tasks}
              recommendedTask={recommendedTask}
              activeFocusTask={activeFocusTask}
              focusStats={focusStats}
              focusSessions={focusSessions}
              onRecordFocusSession={handleRecordFocusSession}
              onToggleTaskComplete={handleToggleTask}
              workDuration={settings?.pomodoro_work_duration || 25}
              breakDuration={settings?.pomodoro_break_duration || 5}
              longBreakDuration={settings?.pomodoro_long_break_duration || 15}
            />
          )}

          {currentTab === 'assistant' && (
            <AssistantPage
              onNavigateTab={setCurrentTab}
              onOpenGoalBreakdown={() => setIsGoalBreakdownModalOpen(true)}
              userName={settings?.user_name || 'User'}
              onRefreshData={refreshAllData}
            />
          )}

          {currentTab === 'habits' && (
            <HabitsPage
              habits={habits}
              onToggleHabitDay={handleToggleHabitDay}
              onCreateHabit={handleCreateHabit}
              onDeleteHabit={handleDeleteHabit}
            />
          )}

          {currentTab === 'analytics' && (
            <AnalyticsPage analytics={analytics} />
          )}

          {currentTab === 'settings' && (
            <SettingsPage
              settings={settings}
              onUpdateSettings={handleUpdateSettings}
              onResetDemoData={handleResetDemoData}
              onClearUserData={handleClearUserData}
            />
          )}
        </main>
      </div>

      {/* Task Modal (Create / Edit) */}
      <TaskModal
        isOpen={isAddTaskModalOpen}
        onClose={() => {
          setIsAddTaskModalOpen(false);
          setEditingTask(null);
        }}
        onSubmit={handleCreateOrUpdateTask}
        initialTask={editingTask}
      />

      {/* Goal Breakdown Modal */}
      <GoalBreakdownModal
        isOpen={isGoalBreakdownModalOpen}
        onClose={() => setIsGoalBreakdownModalOpen(false)}
        onTasksImported={refreshAllData}
      />

      {/* Notification Drawer */}
      <NotificationDrawer
        isOpen={isNotificationDrawerOpen}
        onClose={() => setIsNotificationDrawerOpen(false)}
        tasks={tasks}
        onToggleTask={handleToggleTask}
        onStartFocus={handleStartFocusOnTask}
      />
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}
