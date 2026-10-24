import React, { useState, useEffect, useRef } from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  Coffee,
  Brain,
  Briefcase,
  CheckCircle2,
  Clock,
  Sparkles,
  BookOpen,
  Volume2,
  VolumeX,
  Target
} from 'lucide-react';
import confetti from 'canvas-confetti';
import { Task, FocusSession, FocusStats } from '../types';

interface FocusPageProps {
  tasks: Task[];
  recommendedTask: Task | null;
  activeFocusTask: Task | null;
  focusStats: FocusStats | null;
  focusSessions: FocusSession[];
  onRecordFocusSession: (session: {
    task_id?: string | null;
    task_title: string;
    mode: 'study' | 'work';
    duration_minutes: number;
    notes?: string;
  }) => Promise<void>;
  onToggleTaskComplete: (taskId: string) => Promise<void>;
  workDuration: number;
  breakDuration: number;
  longBreakDuration: number;
}

type TimerStage = 'work' | 'short_break' | 'long_break';
type FocusMode = 'study' | 'work';

export const FocusPage: React.FC<FocusPageProps> = ({
  tasks,
  recommendedTask,
  activeFocusTask,
  focusStats,
  focusSessions,
  onRecordFocusSession,
  onToggleTaskComplete,
  workDuration,
  breakDuration,
  longBreakDuration
}) => {
  const [focusMode, setFocusMode] = useState<FocusMode>('work');
  const [timerStage, setTimerStage] = useState<TimerStage>('work');
  const [selectedTask, setSelectedTask] = useState<Task | null>(activeFocusTask || recommendedTask);
  const [sessionNotes, setSessionNotes] = useState('');
  const [soundEnabled, setSoundEnabled] = useState(true);

  // Time remaining in seconds
  const stageDurations: Record<TimerStage, number> = {
    work: (workDuration || 25) * 60,
    short_break: (breakDuration || 5) * 60,
    long_break: (longBreakDuration || 15) * 60
  };

  const [timeLeft, setTimeLeft] = useState<number>(stageDurations.work);
  const [isRunning, setIsRunning] = useState(false);
  const [completedCycles, setCompletedCycles] = useState(0);

  // Synchronize when activeFocusTask changes from parent
  useEffect(() => {
    if (activeFocusTask) {
      setSelectedTask(activeFocusTask);
      setTimerStage('work');
      setTimeLeft(stageDurations.work);
      setIsRunning(false);
    }
  }, [activeFocusTask]);

  // Audio chime using Web Audio API
  const playChime = () => {
    if (!soundEnabled) return;
    try {
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5
      osc.frequency.setValueAtTime(880, audioCtx.currentTime + 0.15); // A5
      gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.8);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.8);
    } catch {
      // AudioContext not supported
    }
  };

  // Timer Tick
  useEffect(() => {
    let interval: any = null;
    if (isRunning && timeLeft > 0) {
      interval = setInterval(() => {
        setTimeLeft((prev) => prev - 1);
      }, 1000);
    } else if (isRunning && timeLeft === 0) {
      handleStageCompleted();
    }
    return () => clearInterval(interval);
  }, [isRunning, timeLeft]);

  const handleStageCompleted = async () => {
    setIsRunning(false);
    playChime();

    if (timerStage === 'work') {
      confetti({
        particleCount: 70,
        spread: 60,
        origin: { y: 0.6 }
      });

      const minutesLogged = workDuration || 25;
      const title = selectedTask ? selectedTask.title : `${focusMode === 'study' ? 'Study' : 'Deep Work'} Session`;

      await onRecordFocusSession({
        task_id: selectedTask ? selectedTask.id : null,
        task_title: title,
        mode: focusMode,
        duration_minutes: minutesLogged,
        notes: sessionNotes
      });

      const nextCycles = completedCycles + 1;
      setCompletedCycles(nextCycles);

      // Auto switch to break
      if (nextCycles % 4 === 0) {
        setTimerStage('long_break');
        setTimeLeft(stageDurations.long_break);
      } else {
        setTimerStage('short_break');
        setTimeLeft(stageDurations.short_break);
      }
    } else {
      // Break completed, prompt next work block
      setTimerStage('work');
      setTimeLeft(stageDurations.work);
    }
  };

  const handleStartPause = () => {
    setIsRunning((prev) => !prev);
  };

  const handleReset = () => {
    setIsRunning(false);
    setTimeLeft(stageDurations[timerStage]);
  };

  const switchStage = (stage: TimerStage) => {
    setIsRunning(false);
    setTimerStage(stage);
    setTimeLeft(stageDurations[stage]);
  };

  const formatSeconds = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const totalStageSec = stageDurations[timerStage];
  const progressPercent = totalStageSec > 0 ? ((totalStageSec - timeLeft) / totalStageSec) * 100 : 0;

  const pendingTasks = tasks.filter((t) => t.status !== 'completed');

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Top Banner & Mode Toggle */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h2 className="text-base md:text-lg font-bold text-slate-900 dark:text-white">
              Smart Study & Work Mode
            </h2>
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300">
              Pomodoro Flow
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Scientifically optimized interval timers with cognitive recovery breaks.
          </p>
        </div>

        {/* Study Mode vs Work Mode Toggle */}
        <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl">
          <button
            onClick={() => setFocusMode('study')}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              focusMode === 'study'
                ? 'bg-white dark:bg-slate-700 text-indigo-600 dark:text-indigo-300 shadow-xs'
                : 'text-slate-500 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Study Mode</span>
          </button>

          <button
            onClick={() => setFocusMode('work')}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              focusMode === 'work'
                ? 'bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-300 shadow-xs'
                : 'text-slate-500 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            <Briefcase className="w-3.5 h-3.5" />
            <span>Work Mode</span>
          </button>
        </div>
      </div>

      {/* Main Focus Console */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Timer & Controls */}
        <div className="lg:col-span-2 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 md:p-8 shadow-xs flex flex-col items-center justify-between space-y-6">
          {/* Stage Tabs (Work, Short Break, Long Break) */}
          <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800/80 p-1 rounded-xl text-xs font-semibold">
            <button
              onClick={() => switchStage('work')}
              className={`px-4 py-1.5 rounded-lg transition-all ${
                timerStage === 'work'
                  ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-xs'
                  : 'text-slate-500 hover:text-slate-900 dark:text-slate-400'
              }`}
            >
              Focus ({workDuration || 25}m)
            </button>
            <button
              onClick={() => switchStage('short_break')}
              className={`px-4 py-1.5 rounded-lg transition-all ${
                timerStage === 'short_break'
                  ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-xs'
                  : 'text-slate-500 hover:text-slate-900 dark:text-slate-400'
              }`}
            >
              Short Break ({breakDuration || 5}m)
            </button>
            <button
              onClick={() => switchStage('long_break')}
              className={`px-4 py-1.5 rounded-lg transition-all ${
                timerStage === 'long_break'
                  ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-xs'
                  : 'text-slate-500 hover:text-slate-900 dark:text-slate-400'
              }`}
            >
              Long Break ({longBreakDuration || 15}m)
            </button>
          </div>

          {/* Circular Countdown Display */}
          <div className="relative flex items-center justify-center w-64 h-64 my-2">
            <svg className="w-full h-full -rotate-90 transform" viewBox="0 0 100 100">
              {/* Background circle */}
              <circle
                cx="50"
                cy="50"
                r="44"
                className="stroke-slate-100 dark:stroke-slate-800"
                strokeWidth="6"
                fill="transparent"
              />
              {/* Animated Progress circle */}
              <circle
                cx="50"
                cy="50"
                r="44"
                className={`transition-all duration-300 ${
                  timerStage === 'work'
                    ? focusMode === 'study'
                      ? 'stroke-indigo-600 dark:stroke-indigo-400'
                      : 'stroke-blue-600 dark:stroke-blue-400'
                    : 'stroke-emerald-500 dark:stroke-emerald-400'
                }`}
                strokeWidth="6"
                strokeDasharray="276.46"
                strokeDashoffset={276.46 - (276.46 * progressPercent) / 100}
                strokeLinecap="round"
                fill="transparent"
              />
            </svg>

            {/* Inner text countdown */}
            <div className="absolute flex flex-col items-center justify-center text-center">
              <span className="font-mono text-5xl md:text-6xl font-black tracking-tight text-slate-900 dark:text-white">
                {formatSeconds(timeLeft)}
              </span>
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 mt-1">
                {timerStage === 'work'
                  ? `${focusMode === 'study' ? 'Study' : 'Deep Work'} Sprint`
                  : timerStage === 'short_break'
                  ? 'Rest & Hydrate'
                  : 'Mental Recovery'}
              </span>
            </div>
          </div>

          {/* Action buttons (Play/Pause, Reset, Sound toggle) */}
          <div className="flex items-center gap-4">
            <button
              onClick={handleReset}
              className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              title="Reset Timer"
            >
              <RotateCcw className="w-5 h-5" />
            </button>

            <button
              onClick={handleStartPause}
              className={`px-8 py-3.5 rounded-2xl font-bold text-sm text-white shadow-lg flex items-center gap-2 active:scale-98 transition-all ${
                isRunning
                  ? 'bg-amber-600 hover:bg-amber-700 shadow-amber-500/20'
                  : timerStage === 'work'
                  ? focusMode === 'study'
                    ? 'bg-indigo-600 hover:bg-indigo-700 shadow-indigo-500/25'
                    : 'bg-blue-600 hover:bg-blue-700 shadow-blue-500/25'
                  : 'bg-emerald-600 hover:bg-emerald-700 shadow-emerald-500/25'
              }`}
            >
              {isRunning ? (
                <>
                  <Pause className="w-5 h-5 fill-current" />
                  <span>Pause Timer</span>
                </>
              ) : (
                <>
                  <Play className="w-5 h-5 fill-current" />
                  <span>{timeLeft < totalStageSec ? 'Resume' : 'Start Focus Session'}</span>
                </>
              )}
            </button>

            <button
              onClick={() => setSoundEnabled((prev) => !prev)}
              className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              title={soundEnabled ? 'Mute Chime' : 'Enable Chime'}
            >
              {soundEnabled ? <Volume2 className="w-5 h-5 text-blue-500" /> : <VolumeX className="w-5 h-5" />}
            </button>
          </div>

          {/* Session Notes input */}
          <div className="w-full max-w-md pt-2">
            <input
              type="text"
              value={sessionNotes}
              onChange={(e) => setSessionNotes(e.target.value)}
              placeholder="Session notes: e.g. Reviewed 3 chapters of Distributed Systems..."
              className="w-full px-3.5 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            />
          </div>
        </div>

        {/* Right Col: Task Selector & Focus Stats */}
        <div className="space-y-4">
          {/* Linked Task Selector */}
          <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                <Target className="w-4 h-4 text-blue-500" />
                Linked Priority Task
              </span>
              {selectedTask && (
                <button
                  onClick={() => setSelectedTask(null)}
                  className="text-[10px] text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                >
                  Clear
                </button>
              )}
            </div>

            {selectedTask ? (
              <div className="p-3.5 rounded-xl border border-blue-200 dark:border-blue-900 bg-blue-50/50 dark:bg-blue-950/20 space-y-2">
                <div className="font-semibold text-xs text-slate-900 dark:text-white">
                  {selectedTask.title}
                </div>
                <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400">
                  <span>{selectedTask.category}</span>
                  <span>{selectedTask.time_remaining_formatted}</span>
                </div>
                <button
                  onClick={() => onToggleTaskComplete(selectedTask.id)}
                  className="w-full py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white flex items-center justify-center gap-1.5 transition-colors"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Mark Task Complete</span>
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-xs text-slate-400">
                  Select a pending task to link with this focus sprint:
                </p>
                <div className="space-y-1.5 max-h-48 overflow-y-auto">
                  {pendingTasks.map((t) => (
                    <button
                      key={t.id}
                      onClick={() => setSelectedTask(t)}
                      className="w-full text-left p-2 rounded-lg text-xs border border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200 truncate flex items-center justify-between"
                    >
                      <span className="truncate">{t.title}</span>
                      <span className="text-[10px] text-slate-400 shrink-0 ml-1">
                        {t.estimated_duration}m
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Quick Focus Stats */}
          <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
            <span className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
              <Clock className="w-4 h-4 text-indigo-500" />
              Focus Log Summary
            </span>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60">
                <span className="text-slate-400 text-[10px] block">Today's Focus</span>
                <span className="text-lg font-bold text-slate-900 dark:text-white">
                  {focusStats ? focusStats.today_minutes : 0}m
                </span>
              </div>

              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60">
                <span className="text-slate-400 text-[10px] block">Weekly Total</span>
                <span className="text-lg font-bold text-slate-900 dark:text-white">
                  {focusStats ? focusStats.week_minutes : 0}m
                </span>
              </div>
            </div>

            <div className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center justify-between pt-1">
              <span>Study Mode: {focusStats ? focusStats.study_minutes : 0}m</span>
              <span>Work Mode: {focusStats ? focusStats.work_minutes : 0}m</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Focus Session Logs */}
      <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 shadow-xs space-y-4">
        <h3 className="font-bold text-sm text-slate-900 dark:text-white">
          Recent Focus Sessions
        </h3>

        {focusSessions.length > 0 ? (
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {focusSessions.slice(0, 5).map((session) => (
              <div
                key={session.id}
                className="py-3 flex items-center justify-between gap-3 text-xs"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-xl bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 shrink-0">
                    {session.mode === 'study' ? <BookOpen className="w-4 h-4" /> : <Briefcase className="w-4 h-4" />}
                  </div>
                  <div>
                    <div className="font-semibold text-slate-900 dark:text-white">
                      {session.task_title}
                    </div>
                    {session.notes && (
                      <div className="text-[11px] text-slate-400 mt-0.5">{session.notes}</div>
                    )}
                  </div>
                </div>

                <div className="text-right shrink-0">
                  <span className="font-bold text-slate-900 dark:text-white">
                    +{session.duration_minutes} mins
                  </span>
                  <div className="text-[10px] text-slate-400">
                    {new Date(session.completed_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="py-8 text-center text-slate-400 text-xs">
            No completed focus sessions yet today. Start your first sprint above!
          </div>
        )}
      </div>
    </div>
  );
};
