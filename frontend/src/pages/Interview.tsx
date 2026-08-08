import { useEffect, useRef, useState } from "react";
import { Brand } from "../components/Brand";
import { ChatMessage } from "../components/ChatMessage";
import { DayBadge } from "../components/DayBadge";
import { ErrorBanner } from "../components/ErrorBanner";
import { LoadingOverlay } from "../components/LoadingOverlay";
import { SessionIndicator } from "../components/SessionIndicator";
import { TypingIndicator } from "../components/TypingIndicator";
import { useInterview } from "../context/InterviewContext";
import { useAutoScroll } from "../hooks/useAutoScroll";
import type { Page } from "../types";
import { Send, Circle, Bot } from "lucide-react";

interface InterviewProps {
  onNavigate: (page: Page) => void;
}

export function Interview({ onNavigate }: InterviewProps) {
  const {
    messages,
    sessionId,
    state,
    questionNumber,
    totalQuestions,
    currentDay,
    currentTopic,
    daysCovered,
    interviewerTyping,
    interviewComplete,
    loading,
    error,
    sendMessage,
    dismissError,
  } = useInterview();

  const [draft, setDraft] = useState("");
  const transcriptRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useAutoScroll(transcriptRef, [messages.length, interviewerTyping]);

  useEffect(() => {
    if (interviewComplete) {
      const timer = window.setTimeout(() => onNavigate("feedback"), 1600);
      return () => window.clearTimeout(timer);
    }
  }, [interviewComplete, onNavigate]);

  const canSend = !interviewerTyping && !interviewComplete && !loading && state !== "DONE" && Boolean(sessionId);

  const handleSubmit = async (event?: React.FormEvent) => {
    event?.preventDefault();
    const text = draft.trim();
    if (!text || !canSend) return;
    setDraft("");
    await sendMessage(text);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // Find the candidate name if we can
  // The candidate name isn't directly in the session context unfortunately, but we can try to find it from candidates list if the session object had it.
  // Actually, wait, session state might not have candidateName without a refetch, but we can just use "Candidate"
  
  return (
    <div className="flex h-screen flex-col bg-background relative overflow-hidden">
      {/* Background Orbs */}
      <div className="bg-orb-1 top-[-20%] left-[-10%] w-[600px] h-[600px] opacity-10" />
      <div className="bg-orb-2 bottom-[-20%] right-[-10%] w-[600px] h-[600px] opacity-10" />

      {/* Header */}
      <header className="relative z-20 border-b border-white/5 bg-surface-100/60 backdrop-blur-md">
        <div className="mx-auto flex w-full max-w-5xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-6">
            <button onClick={() => onNavigate("landing")} aria-label="Back to landing" className="hover:opacity-80 transition-opacity">
              <Brand size="sm" />
            </button>
            <div className="hidden md:flex h-6 w-px bg-white/10" />
            
            {/* Live Interview Status */}
            <div className="hidden md:flex items-center gap-4">
              <div className="flex items-center gap-2 text-xs font-semibold">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-mint-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-mint-500"></span>
                </span>
                <span className="text-mint-400 tracking-wider uppercase">Live Interview</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-400 font-medium">
                <span className="px-2 py-1 rounded-md bg-surface-200 border border-white/5">
                  Question {questionNumber} / {totalQuestions}
                </span>
                <span className="px-2 py-1 rounded-md bg-surface-200 border border-white/5">
                  {daysCovered.length} days covered
                </span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <SessionIndicator sessionId={sessionId} state={state} />
          </div>
        </div>
      </header>

      {/* Transcript */}
      <main ref={transcriptRef} className="relative z-10 flex-1 overflow-y-auto scroll-smooth custom-scrollbar">
        <div className="mx-auto flex max-w-4xl flex-col gap-6 px-4 py-8 md:px-8">
          {error && (
            <div className="sticky top-2 z-30 animate-fade-in">
              <ErrorBanner message={error} onDismiss={dismissError} />
            </div>
          )}

          {messages.length === 0 && !interviewerTyping ? (
            <EmptyState />
          ) : (
            <div className="flex flex-col gap-8 pb-10">
              {messages.map((message, index) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                  isLast={index === messages.length - 1}
                />
              ))}
              {interviewerTyping && <TypingIndicator />}
            </div>
          )}
        </div>
      </main>

      {/* Input Footer */}
      <footer className="relative z-20 border-t border-white/5 bg-surface-100/60 backdrop-blur-md pb-6 pt-4 px-4 md:px-8">
        <div className="mx-auto max-w-4xl">
          {currentDay && (
            <div className="mb-3 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-accent-purple">Current Topic</span>
                <div className="h-3 w-px bg-white/10" />
                <DayBadge day={currentDay} topic={currentTopic} />
              </div>
              
              {interviewComplete && (
                <span className="text-xs font-medium text-mint-400 animate-fade-in flex items-center gap-1">
                  <Circle className="w-3 h-3 fill-current" />
                  Interview complete — preparing your feedback…
                </span>
              )}
            </div>
          )}
          
          <form onSubmit={handleSubmit} className="relative group">
            <textarea
              ref={inputRef}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={handleKeyDown}
              disabled={!canSend}
              rows={1}
              placeholder={
                interviewerTyping
                  ? "Alex is thinking..."
                  : interviewComplete
                    ? "Interview finished."
                    : "Explain your approach..."
              }
              className="w-full resize-none rounded-2xl border border-white/10 bg-surface-200/50 px-5 py-4 text-[15px] text-slate-100 placeholder-slate-500 outline-none transition-all focus:border-accent-500/50 focus:bg-surface-200 focus:ring-4 focus:ring-accent-500/10 disabled:opacity-50 min-h-[60px] max-h-[200px] shadow-inner"
              autoFocus
            />
            
            <div className="absolute right-3 bottom-3 flex items-center gap-3">
              <span className="hidden sm:flex items-center gap-1 text-[10px] text-slate-500 font-medium">
                <kbd className="font-sans px-1.5 py-0.5 rounded bg-surface-300 border border-white/5">Shift</kbd> + <kbd className="font-sans px-1.5 py-0.5 rounded bg-surface-300 border border-white/5">Enter</kbd> to add a new line
              </span>
              <button
                type="submit"
                disabled={!canSend || !draft.trim()}
                aria-label="Send message"
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-premium-gradient text-white shadow-lg shadow-accent-600/30 transition-all hover:brightness-110 active:scale-95 disabled:opacity-40 disabled:hover:brightness-100"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </form>
        </div>
      </footer>

      {loading && <LoadingOverlay label="Connecting to your interviewer..." />}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center gap-5 py-32 text-center animate-fade-in">
      <div className="w-16 h-16 rounded-full bg-surface-200 flex items-center justify-center border border-white/5 shadow-inner">
        <Bot className="w-8 h-8 text-accent-500" />
      </div>
      <div>
        <h3 className="text-lg font-semibold text-white mb-1">Alex is preparing your first question</h3>
        <p className="text-sm text-slate-400 max-w-sm mx-auto">
          The interviewer is reviewing your cohort journey and will be with you shortly.
        </p>
      </div>
    </div>
  );
}
