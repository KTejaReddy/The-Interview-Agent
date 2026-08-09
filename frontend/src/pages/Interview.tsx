import { useEffect, useRef, useState } from "react";
import { Brand } from "../components/Brand";
import { ChatMessage } from "../components/ChatMessage";
import { DayBadge } from "../components/DayBadge";
import { ErrorBanner } from "../components/ErrorBanner";
import { LoadingOverlay } from "../components/LoadingOverlay";
import { SessionIndicator } from "../components/SessionIndicator";
import { InterviewerCharacter } from "../components/InterviewerCharacter";
import { RealisticAvatar } from "../components/CandidateCharacter";
import { useInterview } from "../context/InterviewContext";
import { useAutoScroll } from "../hooks/useAutoScroll";
import type { Page } from "../types";
import { Send } from "lucide-react";
import { SecurityIndicator } from "../components/SecurityIndicator";
import { useInterviewSecurity } from "../security/useInterviewSecurity";

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
    candidateId,
    candidates,
  } = useInterview();

  const [draft, setDraft] = useState("");
  const [warningMsg, setWarningMsg] = useState("");
  const transcriptRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useInterviewSecurity({
    enabled: !interviewComplete && state !== "DONE",
    onWarning: (msg) => {
      setWarningMsg(msg);
      setTimeout(() => setWarningMsg(""), 6000);
    }
  });

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

  let interviewerState: 'idle' | 'thinking' | 'speaking' | 'listening' | 'frustrated' = 'idle';
  if (interviewerTyping) interviewerState = 'thinking';
  else if (messages.length > 0 && messages[messages.length - 1].role === 'candidate') interviewerState = 'listening';
  
  const idkCount = messages.filter(m => m.role === 'candidate' && m.text.toLowerCase().includes("don't know")).length;
  if (idkCount > 1 && interviewerTyping) interviewerState = 'frustrated';

  const activeCandidate = candidates.find(c => c.id === candidateId);
  const candidateName = activeCandidate?.name || "Candidate";
  const candidateRole = activeCandidate?.role || "Your Profile";

  return (
    <div className={`flex h-screen flex-col bg-background relative overflow-hidden font-sans text-gray-200 ${!interviewComplete && state !== 'DONE' ? 'interview-locked-content' : ''}`}>
      
      {/* Background Atmosphere */}
      <div className="absolute bg-orb-1 top-[10%] left-[-10%] w-[800px] h-[800px] pointer-events-none" />
      <div className="absolute bg-orb-2 bottom-[20%] right-[-10%] w-[600px] h-[600px] pointer-events-none" />

      {/* Header */}
      <header className="relative z-20 border-b border-white/5 bg-surface-50/80 backdrop-blur-xl">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-8">
            <button onClick={() => onNavigate("landing")} aria-label="Back to landing" className="hover:opacity-80 transition-opacity">
              <Brand size="sm" />
            </button>
            <div className="hidden md:flex h-6 w-px bg-white/10" />
            
            <div className="hidden md:flex items-center gap-6">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold uppercase tracking-widest text-base-500">Progress</span>
                <span className="font-bold text-white text-sm">Q{questionNumber} <span className="text-base-500 font-medium text-xs">/ {totalQuestions}</span></span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold uppercase tracking-widest text-base-500">Coverage</span>
                <span className="font-bold text-white text-sm">{daysCovered.length} <span className="text-base-500 font-medium text-xs">days</span></span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            {!interviewComplete && state !== "DONE" && <SecurityIndicator />}
            <SessionIndicator sessionId={sessionId} state={state} />
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex-1 flex overflow-hidden relative z-10 max-w-7xl mx-auto w-full">
        
        {/* Left Sidebar: Profiles */}
        <aside className="hidden lg:flex w-72 flex-col p-6 overflow-y-auto border-r border-white/5">
          
          {/* Interviewer */}
          <div className="mb-10 text-center glass-card rounded-2xl p-6">
            <div className="w-24 h-24 mx-auto bg-surface-200/50 rounded-full border border-white/10 mb-4 flex items-center justify-center pt-2 overflow-hidden shadow-inner">
              <InterviewerCharacter state={interviewerState} />
            </div>
            <h3 className="text-lg font-bold text-white">Alex</h3>
            <p className="text-[9px] font-bold uppercase tracking-widest text-accent-400 mt-1">Technical Interviewer</p>
          </div>

          {/* Candidate */}
          <div className="glass-card-intense rounded-2xl p-5 border border-white/10 shadow-glow-cyan/20">
            <h4 className="text-[10px] font-bold uppercase tracking-widest text-cyan-400 mb-4 border-b border-white/10 pb-2">Candidate</h4>
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 bg-surface-200/50 rounded-full border border-cyan-400/30 flex items-center justify-center overflow-hidden shrink-0 shadow-glow-cyan">
                <RealisticAvatar name={candidateName} />
              </div>
              <div>
                <p className="font-bold text-white text-sm">{candidateName}</p>
                <p className="text-[9px] font-bold text-mint-400 uppercase mt-0.5 tracking-widest">{candidateRole}</p>
              </div>
            </div>
          </div>
        </aside>

        {/* Right Panel: Conversation */}
        <main className="flex-1 flex flex-col relative">
          
          {/* Transcript Area */}
          <div ref={transcriptRef} className="flex-1 overflow-y-auto px-4 py-8 md:px-12 scroll-smooth">
            <div className="max-w-2xl mx-auto flex flex-col gap-8 pb-10">
              
              {error && (
                <div className="sticky top-0 z-30 mb-8">
                  <ErrorBanner message={error} onDismiss={dismissError} />
                </div>
              )}

              {warningMsg && (
                <div className="sticky top-0 z-30 mb-4 mx-auto w-fit">
                  <div className="bg-amber-500/10 border border-amber-500/30 text-amber-200 px-4 py-2 rounded-lg backdrop-blur-md shadow-lg text-sm font-medium">
                    {warningMsg}
                  </div>
                </div>
              )}

              {messages.length === 0 && !interviewerTyping ? (
                <div className="py-20 text-center opacity-70">
                  <h3 className="text-xl font-bold text-white mb-2">The interview is starting</h3>
                  <p className="text-base-400 text-sm">Alex is reviewing your journey.</p>
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
                  <span className="text-[10px] font-bold uppercase tracking-widest text-base-500">Alex is typing</span>
                  <div className="flex items-center gap-1.5 h-6">
                    <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-accent-500" style={{ animationDelay: "0ms" }} />
                    <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-accent-500" style={{ animationDelay: "150ms" }} />
                    <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-accent-500" style={{ animationDelay: "300ms" }} />
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Input Area */}
          <footer className="bg-surface-50/50 backdrop-blur-md p-4 md:px-12 border-t border-white/5">
            <div className="max-w-2xl mx-auto">
              
              {currentDay && (
                <div className="mb-3 flex items-center justify-between px-1">
                  <div className="flex items-center gap-3">
                    <span className="text-[9px] font-bold uppercase tracking-widest text-accent-400">Current Topic</span>
                    <DayBadge day={currentDay} topic={currentTopic} />
                  </div>
                  {interviewComplete && (
                    <span className="text-xs font-semibold text-mint-400">
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
                  className="w-full resize-none rounded-xl border border-white/10 bg-surface-100 px-5 py-4 pr-16 text-sm leading-relaxed text-white placeholder:text-base-500 focus:outline-none focus:border-accent-500 focus:ring-1 focus:ring-accent-500 transition-all shadow-inner min-h-[90px] max-h-[300px]"
                  autoFocus
                />
                
                <div className="absolute right-3 bottom-3 flex items-center gap-2">
                  <div className="hidden sm:flex flex-col items-end gap-0.5 text-[8px] text-base-500 font-semibold mr-1 uppercase tracking-widest">
                    <span>Enter ↵</span>
                    <span>Shift+Enter ↵</span>
                  </div>
                  <button
                    type="submit"
                    disabled={!canSend || !draft.trim()}
                    className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-premium-gradient text-white transition-all hover:scale-105 active:scale-95 disabled:opacity-30 shadow-glow-accent shadow-accent-600/40"
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
