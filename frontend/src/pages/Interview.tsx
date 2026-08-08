import { useEffect, useRef, useState } from "react";
import { Brand } from "../components/Brand";
import { ChatMessage } from "../components/ChatMessage";
import { CoverageTracker } from "../components/CoverageTracker";
import { DayBadge } from "../components/DayBadge";
import { ErrorBanner } from "../components/ErrorBanner";
import { LoadingOverlay } from "../components/LoadingOverlay";
import { ProgressBar } from "../components/ProgressBar";
import { QuestionCounter } from "../components/QuestionCounter";
import { SessionIndicator } from "../components/SessionIndicator";
import { TypingIndicator } from "../components/TypingIndicator";
import { useInterview } from "../context/InterviewContext";
import { useAutoScroll } from "../hooks/useAutoScroll";
import type { Page } from "../types";

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
  const inputRef = useRef<HTMLInputElement>(null);

  useAutoScroll(transcriptRef, [messages.length, interviewerTyping]);

  // When the interview completes, let the user see the wrap-up then navigate.
  useEffect(() => {
    if (interviewComplete) {
      const timer = window.setTimeout(() => onNavigate("feedback"), 1600);
      return () => window.clearTimeout(timer);
    }
  }, [interviewComplete, onNavigate]);

  const canSend =
    !interviewerTyping &&
    !interviewComplete &&
    !loading &&
    state !== "DONE" &&
    Boolean(sessionId);

  const handleSubmit = async (event?: React.FormEvent) => {
    event?.preventDefault();
    const text = draft.trim();
    if (!text || !canSend) return;
    setDraft("");
    await sendMessage(text);
    inputRef.current?.focus();
  };

  return (
    <div className="flex h-screen flex-col">
      {/* Header */}
      <header className="border-b border-base-800 bg-base-900/80 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-6 py-4">
          <div className="flex items-center gap-4">
            <button onClick={() => onNavigate("landing")} aria-label="Back to landing">
              <Brand size="sm" />
            </button>
            <div className="hidden md:block">
              <QuestionCounter questionNumber={questionNumber} totalQuestions={totalQuestions} />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden lg:block w-44">
              <ProgressBar questionNumber={questionNumber} totalQuestions={totalQuestions} />
            </div>
            <SessionIndicator sessionId={sessionId} state={state} />
          </div>
        </div>
        <div className="mx-auto flex max-w-5xl items-center gap-4 px-6 pb-3 lg:hidden">
          <div className="flex-1">
            <ProgressBar questionNumber={questionNumber} totalQuestions={totalQuestions} />
          </div>
          <QuestionCounter questionNumber={questionNumber} totalQuestions={totalQuestions} />
        </div>
      </header>

      {/* Transcript + coverage sidebar */}
      <main ref={transcriptRef} className="flex-1 overflow-y-auto scroll-smooth">
        <div className="mx-auto flex max-w-5xl flex-col gap-6 px-6 py-8 lg:flex-row lg:items-start">
          <div className="mx-auto flex w-full max-w-3xl flex-col gap-5">
            {error && (
              <div className="sticky top-2 z-10">
                <ErrorBanner message={error} onDismiss={dismissError} />
              </div>
            )}

            {messages.length === 0 && !interviewerTyping ? (
              <EmptyState />
            ) : (
              messages.map((message, index) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                  isLast={index === messages.length - 1}
                />
              ))
            )}

            {interviewerTyping && <TypingIndicator />}
          </div>

          <aside className="hidden w-60 shrink-0 lg:block">
            <div className="sticky top-8">
              <CoverageTracker
                daysCovered={daysCovered}
                totalQuestions={questionNumber}
              />
            </div>
          </aside>
        </div>
      </main>

      {/* Input */}
      <footer className="border-t border-base-800 bg-base-900/80 backdrop-blur">
        <div className="mx-auto max-w-3xl px-6 py-4">
          {currentDay && (
            <div className="mb-3 flex items-center justify-between gap-3">
              <DayBadge day={currentDay} topic={currentTopic} />
              {interviewComplete && (
                <span className="text-xs font-medium text-mint-400 animate-fade-in">
                  Interview complete — preparing your feedback…
                </span>
              )}
            </div>
          )}
          <div className="mb-3 lg:hidden">
            <CoverageTracker daysCovered={daysCovered} totalQuestions={questionNumber} />
          </div>
          <form onSubmit={handleSubmit} className="flex items-center gap-3">
            <input
              ref={inputRef}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              disabled={!canSend}
              placeholder={
                interviewerTyping
                  ? "The interviewer is typing…"
                  : interviewComplete
                    ? "Interview finished"
                    : "Type your answer…"
              }
              className="flex-1 rounded-xl border border-base-700 bg-base-800/80 px-4 py-3.5 text-[15px] text-slate-100 placeholder-slate-500 outline-none transition focus:border-accent-500/60 focus:ring-2 focus:ring-accent-500/20 disabled:opacity-50"
              autoFocus
            />
            <button
              type="submit"
              disabled={!canSend || !draft.trim()}
              aria-label="Send answer"
              className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-accent-600 to-indigo-500 text-white shadow-lg shadow-accent-600/30 transition-all duration-200 hover:brightness-110 active:scale-95 disabled:opacity-40 disabled:hover:brightness-100"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <path d="M4 12h14m0 0-5-5m5 5-5 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </form>
        </div>
      </footer>

      {loading && <LoadingOverlay label="Connecting to the interviewer…" />}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-24 text-center animate-fade-in">
      <div className="flex h-16 w-16 items-center justify-center rounded-3xl bg-gradient-to-br from-accent-500 to-mint-500 shadow-xl shadow-accent-500/30">
        <svg width="30" height="30" viewBox="0 0 24 24" fill="none">
          <rect x="4" y="4" width="16" height="12" rx="3" fill="#0a0c1a" />
          <circle cx="9" cy="10" r="1.4" fill="#818cf8" />
          <circle cx="12" cy="10" r="1.4" fill="#818cf8" />
          <circle cx="15" cy="10" r="1.4" fill="#818cf8" />
          <path d="M4 19h16" stroke="#34d399" strokeWidth="2" strokeLinecap="round" />
        </svg>
      </div>
      <p className="text-slate-300">The interviewer is getting ready…</p>
    </div>
  );
}
