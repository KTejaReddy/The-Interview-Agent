import { useEffect, useRef, useState } from "react";
import { Brand } from "../components/Brand";
import { ChatMessage } from "../components/ChatMessage";
import { DayBadge } from "../components/DayBadge";
import { ErrorBanner } from "../components/ErrorBanner";
import { LoadingOverlay } from "../components/LoadingOverlay";
import { SessionIndicator } from "../components/SessionIndicator";
import { InterviewerCharacter } from "../components/InterviewerCharacter";
import { CandidateCharacter } from "../components/CandidateCharacter";
import { useInterview } from "../context/InterviewContext";
import { useAutoScroll } from "../hooks/useAutoScroll";
import type { Page } from "../types";
import { Send } from "lucide-react";

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

  // Determine interviewer state
  let interviewerState: 'idle' | 'thinking' | 'speaking' | 'listening' | 'frustrated' = 'idle';
  if (interviewerTyping) interviewerState = 'thinking';
  else if (messages.length > 0 && messages[messages.length - 1].role === 'candidate') interviewerState = 'listening';
  
  // A subtle heuristic for "frustration" - if the candidate says "I don't know" multiple times
  const idkCount = messages.filter(m => m.role === 'candidate' && m.text.toLowerCase().includes("don't know")).length;
  if (idkCount > 1 && interviewerTyping) interviewerState = 'frustrated';

  return (
    <div className="flex h-screen flex-col bg-background relative overflow-hidden font-sans">
      <div className="absolute inset-0 bg-paper-texture opacity-30 pointer-events-none" />

      {/* Header */}
      <header className="relative z-20 border-b border-surface-200 bg-surface-50/80 backdrop-blur-md">
        <div className="mx-auto flex w-full items-center justify-between px-8 py-4">
          <div className="flex items-center gap-8">
            <button onClick={() => onNavigate("landing")} aria-label="Back to landing" className="hover:opacity-80 transition-opacity">
              <Brand size="sm" />
            </button>
            <div className="hidden md:flex h-6 w-px bg-surface-200" />
            
            <div className="hidden md:flex items-center gap-6">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold uppercase tracking-widest text-base-500">Progress</span>
                <span className="font-serif font-bold text-base-900">Q{questionNumber} <span className="text-base-400 font-sans text-xs">/ {totalQuestions}</span></span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold uppercase tracking-widest text-base-500">Coverage</span>
                <span className="font-serif font-bold text-base-900">{daysCovered.length} <span className="text-base-400 font-sans text-xs">days</span></span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <SessionIndicator sessionId={sessionId} state={state} />
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex-1 flex overflow-hidden relative z-10">
        
        {/* Left Sidebar: Interviewer & Candidate Status */}
        <aside className="hidden lg:flex w-80 border-r border-surface-200 bg-surface-50 flex-col p-6 overflow-y-auto">
          
          {/* Interviewer Profile */}
          <div className="mb-10 text-center">
            <div className="w-32 h-32 mx-auto bg-surface-100 rounded-2xl border border-surface-200 mb-4 overflow-hidden relative">
              <div className="absolute inset-0 bg-paper-texture opacity-50" />
              <InterviewerCharacter state={interviewerState} />
            </div>
            <h3 className="font-serif text-xl font-bold text-base-900">Alex</h3>
            <p className="text-xs font-semibold uppercase tracking-widest text-base-500 mt-1">Technical Interviewer</p>
          </div>

          <hr className="border-surface-200 mb-8" />

          {/* Candidate Profile summary (mocking candidate details) */}
          <div className="mb-6">
            <h4 className="text-[10px] font-bold uppercase tracking-widest text-base-500 mb-4">Candidate</h4>
            <div className="flex items-center gap-4 mb-4">
              <div className="w-16 h-16 bg-surface-100 rounded-xl border border-surface-200 overflow-hidden relative shrink-0">
                <CandidateCharacter name="Candidate" role="Applicant" readiness={80} />
              </div>
              <div>
                <p className="font-serif font-bold text-base-900 leading-tight">Your Profile</p>
                <p className="text-[10px] font-semibold text-base-500 uppercase mt-1">Ready for review</p>
              </div>
            </div>
          </div>

        </aside>

        {/* Right Panel: Transcript & Input */}
        <main className="flex-1 flex flex-col bg-white relative">
          
          {/* Transcript Area */}
          <div ref={transcriptRef} className="flex-1 overflow-y-auto px-6 py-10 md:px-16 scroll-smooth">
            <div className="max-w-3xl mx-auto flex flex-col gap-10 pb-10">
              
              {error && (
                <div className="sticky top-0 z-30 mb-8">
                  <ErrorBanner message={error} onDismiss={dismissError} />
                </div>
              )}

              {messages.length === 0 && !interviewerTyping ? (
                <div className="py-20 text-center">
                  <h3 className="font-serif text-2xl font-bold text-base-900 mb-2">The interview is starting</h3>
                  <p className="text-base-500">Alex is reviewing your journey.</p>
                </div>
              ) : (
                messages.map((message, index) => (
                  <ChatMessage
                    key={message.id}
                    message={message}
                    isLast={index === messages.length - 1}
                  />
                ))
              )}

              {interviewerTyping && (
                <div className="flex flex-col gap-2 animate-fade-in pl-14">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-base-400">Alex is thinking</span>
                  <div className="flex items-center gap-1.5 h-6">
                    <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-accent-400" style={{ animationDelay: "0ms" }} />
                    <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-accent-400" style={{ animationDelay: "150ms" }} />
                    <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-accent-400" style={{ animationDelay: "300ms" }} />
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Input Area */}
          <footer className="border-t border-surface-200 bg-surface-50 p-6 md:px-16">
            <div className="max-w-3xl mx-auto">
              
              {currentDay && (
                <div className="mb-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-accent-500">Current Topic</span>
                    <DayBadge day={currentDay} topic={currentTopic} />
                  </div>
                  {interviewComplete && (
                    <span className="text-xs font-semibold text-mint-500">
                      Interview complete — preparing report...
                    </span>
                  )}
                </div>
              )}
              
              <form onSubmit={handleSubmit} className="relative">
                <textarea
                  ref={inputRef}
                  value={draft}
                  onChange={(event) => setDraft(event.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={!canSend}
                  rows={2}
                  placeholder={
                    interviewerTyping
                      ? "Alex is typing..."
                      : interviewComplete
                        ? "Interview concluded."
                        : "Explain your approach..."
                  }
                  className="w-full resize-none rounded-2xl border border-surface-300 bg-white px-6 py-5 pr-20 text-[15px] leading-relaxed text-base-900 placeholder:text-base-400 focus:outline-none focus:border-accent-500 focus:ring-4 focus:ring-accent-500/10 transition-all editorial-shadow min-h-[100px] max-h-[300px]"
                  autoFocus
                />
                
                <div className="absolute right-4 bottom-4 flex items-center gap-3">
                  <div className="hidden sm:flex flex-col items-end gap-0.5 text-[9px] text-base-400 font-medium mr-2">
                    <span><kbd className="font-sans px-1 rounded bg-surface-100 border border-surface-200">Enter</kbd> to send</span>
                    <span><kbd className="font-sans px-1 rounded bg-surface-100 border border-surface-200">Shift</kbd> + <kbd className="font-sans px-1 rounded bg-surface-100 border border-surface-200">Enter</kbd> for line</span>
                  </div>
                  <button
                    type="submit"
                    disabled={!canSend || !draft.trim()}
                    className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-base-900 text-white transition-all hover:bg-base-800 active:scale-95 disabled:opacity-40"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              </form>
            </div>
          </footer>
          
        </main>
      </div>

      {loading && <LoadingOverlay label="Connecting to the interviewer..." />}
    </div>
  );
}
