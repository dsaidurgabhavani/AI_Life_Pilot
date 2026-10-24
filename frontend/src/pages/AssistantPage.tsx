import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Bot,
  User,
  Sparkles,
  Layers,
  ArrowRight,
  Clock,
  CheckCircle2,
  Calendar,
  Cpu,
  RefreshCw,
  Trash2,
  RotateCcw,
  AlertTriangle
} from 'lucide-react';
import { api } from '../api';
import { ChatMessage } from '../types';

interface AssistantPageProps {
  onNavigateTab: (tab: any) => void;
  onOpenGoalBreakdown: () => void;
  userName: string;
  onRefreshData?: () => Promise<void>;
}

export const AssistantPage: React.FC<AssistantPageProps> = ({
  onNavigateTab,
  onOpenGoalBreakdown,
  userName,
  onRefreshData
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [failedPrompt, setFailedPrompt] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const defaultWelcomeMessage: ChatMessage = {
    id: 'msg-welcome',
    sender: 'assistant',
    text: `Hello ${userName || 'there'}! I'm your AI Productivity Copilot.\n\nI can help you:\n• **Plan your day with constraints:** e.g., *"Plan my day. I have classes from 9 AM to 1 PM and need two hours for Java practice."*\n• **Create and schedule tasks:** e.g., *"Create a task to finish my project report tomorrow"*\n• **Prioritize deadlines & decompose goals:** e.g., *"Break down my thesis into actionable subtasks"*\n• **Guide Pomodoro study/work sprints**\n\nHow can I help you take action today?`,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    engine_used: 'real_action_engine',
    suggested_actions: [
      { label: "View Today's Plan", route: 'planner' },
      { label: 'Start Focus Sprint', route: 'focus' },
      { label: 'Decompose Large Goal', action: 'open_breakdown_modal' }
    ]
  };

  // Load conversation history from database on mount
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const history = await api.getChatHistory();
        if (history && history.length > 0) {
          setMessages(history);
        } else {
          setMessages([defaultWelcomeMessage]);
        }
      } catch {
        setMessages([defaultWelcomeMessage]);
      }
    };
    loadHistory();
  }, [userName]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const quickPrompts = [
    'Plan my day. I have classes from 9 AM to 1 PM and need two hours for Java practice.',
    'Create a task to finish my project report tomorrow',
    'What should I prioritize right now?',
    'I feel overwhelmed with work. What should I tackle first?'
  ];

  const handleSend = async (messageText?: string) => {
    const textToSend = (messageText || input).trim();
    if (!textToSend || isLoading) return;

    setFailedPrompt(null);
    const userMsg: ChatMessage = {
      id: `usr-${Date.now()}`,
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      // Build conversation history format for API
      const history = messages.slice(-8).map((m) => ({
        role: m.sender === 'user' ? 'user' : 'model',
        content: m.text
      }));

      const res = await api.sendChatMessage(textToSend, history);

      const aiMsg: ChatMessage = {
        id: `ai-${Date.now()}`,
        sender: 'assistant',
        text: res.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        engine_used: res.engine_used,
        suggested_actions: res.suggested_actions
      };

      setMessages((prev) => [...prev, aiMsg]);

      // If a real task was created or schedule updated, refresh application data instantly!
      if (res.action_executed && onRefreshData) {
        await onRefreshData();
      }
    } catch (err: any) {
      setFailedPrompt(textToSend);
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        sender: 'assistant',
        text: `⚠️ **Service Error**: ${err.message || 'Failed to communicate with AI Copilot.'}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        engine_used: 'system_error'
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearChat = async () => {
    if (window.confirm('Clear all conversation history?')) {
      try {
        await api.clearChatHistory();
        setMessages([defaultWelcomeMessage]);
      } catch (err: any) {
        console.error('Failed to clear chat:', err);
      }
    }
  };

  const handleActionClick = (action: { label: string; route?: string; action?: string }) => {
    if (action.action === 'open_breakdown_modal') {
      onOpenGoalBreakdown();
    } else if (action.action === 'retry' && failedPrompt) {
      handleSend(failedPrompt);
    } else if (action.route) {
      onNavigateTab(action.route);
    }
  };

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-140px)] flex flex-col rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs overflow-hidden">
      {/* Header bar */}
      <div className="p-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-indigo-600 text-white flex items-center justify-center">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900 dark:text-white">
              AI Productivity Copilot
            </h2>
            <span className="text-[10px] text-slate-400 block">
              Grounded on your actual database tasks, working hours, and deadlines
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onOpenGoalBreakdown}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 hover:bg-indigo-100 border border-indigo-200/60 dark:border-indigo-800/40"
          >
            <Layers className="w-3.5 h-3.5 text-indigo-500" />
            <span className="hidden sm:inline">Decompose Goal</span>
          </button>

          <button
            onClick={handleClearChat}
            title="Clear Conversation History"
            className="p-1.5 rounded-xl text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 border border-transparent hover:border-rose-200 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4">
        {messages.map((m) => {
          const isUser = m.sender === 'user';
          const isError = m.engine_used === 'system_error';

          return (
            <div
              key={m.id}
              className={`flex gap-3 max-w-[88%] md:max-w-[80%] ${
                isUser ? 'ml-auto flex-row-reverse' : ''
              }`}
            >
              {/* Avatar */}
              <div
                className={`w-7 h-7 rounded-xl flex items-center justify-center text-xs shrink-0 ${
                  isUser
                    ? 'bg-blue-600 text-white'
                    : isError
                    ? 'bg-rose-100 text-rose-600 dark:bg-rose-950/60'
                    : 'bg-indigo-600/10 dark:bg-indigo-400/10 text-indigo-600 dark:text-indigo-400'
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              {/* Message Bubble */}
              <div className="space-y-2">
                <div
                  className={`p-4 rounded-2xl text-xs md:text-sm leading-relaxed whitespace-pre-wrap ${
                    isUser
                      ? 'bg-blue-600 text-white rounded-tr-xs'
                      : isError
                      ? 'bg-rose-50 dark:bg-rose-950/30 text-rose-800 dark:text-rose-200 rounded-tl-xs border border-rose-200 dark:border-rose-900/40'
                      : 'bg-slate-100 dark:bg-slate-800/80 text-slate-800 dark:text-slate-200 rounded-tl-xs border border-slate-200/60 dark:border-slate-700/50'
                  }`}
                >
                  {m.text}

                  {isError && failedPrompt && (
                    <div className="mt-2 pt-2 border-t border-rose-200/60 dark:border-rose-900/40">
                      <button
                        onClick={() => handleSend(failedPrompt)}
                        className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold bg-rose-600 text-white hover:bg-rose-700 shadow-2xs"
                      >
                        <RotateCcw className="w-3 h-3" />
                        <span>Retry</span>
                      </button>
                    </div>
                  )}
                </div>

                {/* Engine indicator & timestamp */}
                <div
                  className={`flex items-center gap-2 text-[10px] text-slate-400 ${
                    isUser ? 'justify-end' : 'justify-start'
                  }`}
                >
                  <span>{m.timestamp}</span>
                  {!isUser && m.engine_used && (
                    <span className="inline-flex items-center gap-1 font-medium text-slate-400">
                      •
                      <Cpu className="w-3 h-3 text-emerald-500" />
                      {m.engine_used === 'gemini'
                        ? 'Gemini 1.5 Flash'
                        : m.engine_used === 'real_action_engine'
                        ? 'Real Action Engine'
                        : m.engine_used === 'deterministic_engine'
                        ? 'Deterministic Engine'
                        : 'Notice'}
                    </span>
                  )}
                </div>

                {/* Suggested Action Chips */}
                {!isUser && m.suggested_actions && m.suggested_actions.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {m.suggested_actions.map((action, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleActionClick(action)}
                        className="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:border-blue-500 hover:text-blue-600 transition-colors flex items-center gap-1 shadow-2xs"
                      >
                        <span>{action.label}</span>
                        <ArrowRight className="w-3 h-3 text-slate-400" />
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {isLoading && (
          <div className="flex gap-3 max-w-[80%]">
            <div className="w-7 h-7 rounded-xl bg-indigo-600/10 text-indigo-600 flex items-center justify-center shrink-0">
              <Bot className="w-4 h-4" />
            </div>
            <div className="p-3.5 rounded-2xl rounded-tl-xs bg-slate-100 dark:bg-slate-800 text-xs text-slate-500 flex items-center gap-2">
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-indigo-500" />
              <span>Analyzing request & coordinating database operations...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Prompts Bar */}
      <div className="px-4 py-2 bg-slate-50 dark:bg-slate-800/40 border-t border-slate-100 dark:border-slate-800 flex items-center gap-2 overflow-x-auto">
        <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider shrink-0">
          Try:
        </span>
        {quickPrompts.map((prompt, i) => (
          <button
            key={i}
            onClick={() => handleSend(prompt)}
            className="text-[11px] px-2.5 py-1 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 shrink-0 whitespace-nowrap"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Input box */}
      <div className="p-3 bg-white dark:bg-slate-900 border-t border-slate-100 dark:border-slate-800">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type instructions (e.g. 'Plan my day. I have classes from 9 AM to 1 PM and need two hours for Java practice')..."
            className="flex-1 px-4 py-2.5 text-xs md:text-sm rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
          />

          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs flex items-center gap-1.5 shadow-xs disabled:opacity-40 transition-all"
          >
            <span>Send</span>
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>
      </div>
    </div>
  );
};
