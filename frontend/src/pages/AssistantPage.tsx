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
  RefreshCw
} from 'lucide-react';
import { api } from '../api';
import { ChatMessage } from '../types';

interface AssistantPageProps {
  onNavigateTab: (tab: any) => void;
  onOpenGoalBreakdown: () => void;
  userName: string;
}

export const AssistantPage: React.FC<AssistantPageProps> = ({
  onNavigateTab,
  onOpenGoalBreakdown,
  userName
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg-welcome',
      sender: 'assistant',
      text: `Hello ${userName}! I'm AI LifePilot, your intelligent productivity and daily planning copilot.\n\nI can help you prioritize conflicting deadlines, optimize your daily schedule, break down large milestones, or coach you through focused Pomodoro sprints.\n\nHow can I help simplify your day?`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      engine_used: 'smart_heuristic',
      suggested_actions: [
        { label: "View Today's Plan", route: 'planner' },
        { label: 'Start Focus Sprint', route: 'focus' },
        { label: 'Break Down Large Goal', action: 'open_breakdown_modal' }
      ]
    }
  ]);

  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const quickPrompts = [
    'How should I prioritize my tasks today?',
    'I feel overwhelmed with work. What should I drop?',
    'I only have 90 minutes of free time. What should I tackle?',
    'Help me build momentum with the Pomodoro technique'
  ];

  const handleSend = async (messageText?: string) => {
    const textToSend = (messageText || input).trim();
    if (!textToSend || isLoading) return;

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
      // Build conversation history format
      const history = messages.slice(-6).map((m) => ({
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
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        sender: 'assistant',
        text: `I encountered an issue connecting to the AI service: ${err.message || 'Please try again.'}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        engine_used: 'smart_heuristic'
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleActionClick = (action: { label: string; route?: string; action?: string }) => {
    if (action.action === 'open_breakdown_modal') {
      onOpenGoalBreakdown();
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
              Grounded on your actual schedule, deadlines, and habits
            </span>
          </div>
        </div>

        <button
          onClick={onOpenGoalBreakdown}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 hover:bg-indigo-100 border border-indigo-200/60 dark:border-indigo-800/40"
        >
          <Layers className="w-3.5 h-3.5 text-indigo-500" />
          <span>Decompose Goal</span>
        </button>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4">
        {messages.map((m) => {
          const isUser = m.sender === 'user';

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
                      : 'bg-slate-100 dark:bg-slate-800/80 text-slate-800 dark:text-slate-200 rounded-tl-xs border border-slate-200/60 dark:border-slate-700/50'
                  }`}
                >
                  {m.text}
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
                      {m.engine_used === 'gemini' ? 'Gemini 2.5 Flash' : 'Smart Heuristic Engine'}
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
              <span>Analyzing schedule & formulating strategy...</span>
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
            placeholder="Ask AI LifePilot to optimize schedule, break down goals, or tackle overload..."
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
