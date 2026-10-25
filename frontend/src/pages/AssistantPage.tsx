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
  AlertTriangle,
  CloudSun,
  Search,
  Check,
  Paperclip,
  FileText,
  ExternalLink,
  Bell
} from 'lucide-react';
import { api } from '../api';
import { ChatMessage, ToolExecution } from '../types';

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
  const [isUploadingDoc, setIsUploadingDoc] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const defaultWelcomeMessage: ChatMessage = {
    id: 'msg-welcome',
    sender: 'assistant',
    text: `Hello ${userName || 'there'}! I'm your real-time AI Productivity Copilot.\n\nI can execute real operations and retrieve live data:\n• **Create & schedule database tasks:** *"Create a task to finish my Java assignment tomorrow"*\n• **Real-time live weather:** *"What is the weather in Vijayawada right now?"*\n• **Live web search & news:** *"Search for the latest AI developments"*\n• **Time-blocked daily planning:** *"Plan my day. I have classes from 9 AM to 1 PM and need two hours for Java practice"*\n• **Real-time scheduled reminders:** *"Remind me in 30 minutes to review code"*\n• **Document summarization:** Attach any file or notes below for structured takeaways\n\nWhat would you like to accomplish?`,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    engine_used: 'real_action_engine',
    suggested_actions: [
      { label: "What is the weather in Vijayawada?", action: 'run_prompt_weather' },
      { label: 'Create Java Assignment Task', action: 'run_prompt_task' },
      { label: 'Search Latest AI News', action: 'run_prompt_search' },
      { label: "View Today's Plan", route: 'planner' }
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
    'Create a task to finish my Java assignment tomorrow',
    'What is the weather in Vijayawada right now?',
    'Search for the latest AI developments',
    'Plan my day. I have classes from 9 AM to 1 PM and need two hours for Java practice.',
    'Remind me in 30 minutes to review code',
    'What should I prioritize right now?'
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
        suggested_actions: res.suggested_actions,
        tool_executions: res.tool_executions,
        action_executed: res.action_executed
      };

      setMessages((prev) => [...prev, aiMsg]);

      // If a real task or schedule was altered, refresh all application data immediately!
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

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploadingDoc(true);
    try {
      const uploaded = await api.uploadDocument(file);
      const summarizePrompt = `Please summarize the uploaded document "${uploaded.filename}" and extract any key actionable tasks from it.`;
      await handleSend(summarizePrompt);
    } catch (err: any) {
      alert(`Document upload failed: ${err.message}`);
    } finally {
      setIsUploadingDoc(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleActionClick = (action: { label: string; route?: string; action?: string }) => {
    if (action.action === 'open_breakdown_modal') {
      onOpenGoalBreakdown();
    } else if (action.action === 'retry' && failedPrompt) {
      handleSend(failedPrompt);
    } else if (action.action === 'run_prompt_weather') {
      handleSend('What is the weather in Vijayawada right now?');
    } else if (action.action === 'run_prompt_task') {
      handleSend('Create a task to finish my Java assignment tomorrow');
    } else if (action.action === 'run_prompt_search') {
      handleSend('Search for the latest AI developments');
    } else if (action.route) {
      onNavigateTab(action.route);
    }
  };

  // Helper to format markdown text with clickable links
  const renderFormattedText = (text: string) => {
    // Replace [label](url) with clickable links
    const linkRegex = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g;
    const parts = [];
    let lastIdx = 0;
    let match;

    while ((match = linkRegex.exec(text)) !== null) {
      if (match.index > lastIdx) {
        parts.push(text.substring(lastIdx, match.index));
      }
      parts.push(
        <a
          key={match.index}
          href={match[2]}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 dark:text-blue-400 font-semibold underline hover:text-blue-800 dark:hover:text-blue-300 inline-flex items-center gap-0.5"
        >
          <span>{match[1]}</span>
          <ExternalLink className="w-3 h-3 inline" />
        </a>
      );
      lastIdx = match.index + match[0].length;
    }

    if (lastIdx < text.length) {
      parts.push(text.substring(lastIdx));
    }

    return parts;
  };

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-140px)] flex flex-col rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs overflow-hidden">
      {/* Header bar */}
      <div className="p-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-indigo-600 text-white flex items-center justify-center shadow-xs">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-slate-900 dark:text-white">
                AI Productivity Copilot
              </h2>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-200/60 dark:border-emerald-800/40">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Live Tool Execution Active
              </span>
            </div>
            <span className="text-[10px] text-slate-400 block">
              Grounded on SQLite database, live Open-Meteo weather, and real web search
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Hidden File Input for document upload */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            className="hidden"
            accept=".txt,.md,.json,.pdf,.csv,.doc,.docx"
          />

          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploadingDoc}
            title="Upload Document or Notes for AI Summarization"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 transition-colors"
          >
            {isUploadingDoc ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-500" />
            ) : (
              <Paperclip className="w-3.5 h-3.5 text-slate-500" />
            )}
            <span className="hidden sm:inline">Upload Doc</span>
          </button>

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
                {/* Tool execution badge chips */}
                {!isUser && m.tool_executions && m.tool_executions.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pb-1">
                    {m.tool_executions.map((tool, tIdx) => (
                      <div
                        key={tIdx}
                        className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[10px] font-semibold bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800"
                      >
                        <Check className="w-3 h-3 text-emerald-600" />
                        <span>Tool Executed: <code className="font-mono">{tool.tool_name}</code></span>
                      </div>
                    ))}
                  </div>
                )}

                <div
                  className={`p-4 rounded-2xl text-xs md:text-sm leading-relaxed whitespace-pre-wrap ${
                    isUser
                      ? 'bg-blue-600 text-white rounded-tr-xs shadow-xs'
                      : isError
                      ? 'bg-rose-50 dark:bg-rose-950/30 text-rose-800 dark:text-rose-200 rounded-tl-xs border border-rose-200 dark:border-rose-900/40'
                      : 'bg-slate-100 dark:bg-slate-800/80 text-slate-800 dark:text-slate-200 rounded-tl-xs border border-slate-200/60 dark:border-slate-700/50'
                  }`}
                >
                  {renderFormattedText(m.text)}

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
                        ? 'Gemini 3.1 Flash Lite'
                        : m.engine_used === 'real_action_engine'
                        ? 'Real Action Engine (Verified)'
                        : m.engine_used === 'deterministic_engine'
                        ? 'Deterministic Action Engine'
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
              <span>Contacting real-time services and executing verified actions...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Prompts Bar */}
      <div className="px-4 py-2 bg-slate-50 dark:bg-slate-800/40 border-t border-slate-100 dark:border-slate-800 flex items-center gap-2 overflow-x-auto">
        <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider shrink-0">
          Try Live:
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
            placeholder="Instruct me (e.g., 'What is the weather in Vijayawada right now?' or 'Create a task to finish my Java assignment tomorrow')..."
            className="flex-1 px-4 py-2.5 text-xs md:text-sm rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
          />

          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs flex items-center gap-1.5 shadow-xs disabled:opacity-40 transition-all shrink-0"
          >
            <span>Send</span>
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>
      </div>
    </div>
  );
};
