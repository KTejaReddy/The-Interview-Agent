import { useTypingEffect } from "../hooks/useTypingEffect";
import type { ChatMessage as ChatMessageType } from "../types";
import { DayBadge } from "./DayBadge";

interface ChatMessageProps {
  message: ChatMessageType;
  isLast: boolean;
}

export function ChatMessage({ message, isLast }: ChatMessageProps) {
  const isInterviewer = message.role === "interviewer";
  const revealed = useTypingEffect(message.text, isInterviewer && isLast, 12);

  return (
    <div
      className={`flex items-start gap-3 ${
        isInterviewer ? "animate-slide-in-left" : "animate-slide-in-right justify-end"
      }`}
    >
      {isInterviewer && (
        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-accent-500 to-mint-500 shadow-md shadow-accent-500/25">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <rect x="5" y="5" width="14" height="10" rx="2.5" fill="#0a0c1a" />
            <circle cx="9.5" cy="10" r="1.1" fill="#818cf8" />
            <circle cx="12" cy="10" r="1.1" fill="#818cf8" />
            <circle cx="14.5" cy="10" r="1.1" fill="#818cf8" />
            <path d="M5 18h14" stroke="#34d399" strokeWidth="1.8" strokeLinecap="round" />
          </svg>
        </div>
      )}

      <div className={`max-w-[80%] md:max-w-[70%] ${isInterviewer ? "" : "text-right"}`}>
        {message.isQuestion && isInterviewer && (
          <div className="mb-1.5">
            <DayBadge day={message.currentDay ?? null} topic={message.currentTopic} />
          </div>
        )}
        <div
          className={`rounded-2xl px-4 py-3 text-left text-[15px] leading-relaxed shadow-md ${
            isInterviewer
              ? "rounded-tl-sm border border-base-700 bg-base-800 text-slate-100"
              : "rounded-tr-sm border border-accent-500/30 bg-gradient-to-br from-accent-600/80 to-indigo-700/80 text-white"
          }`}
        >
          {isInterviewer && isLast ? (
            <>
              {revealed}
              {revealed.length < message.text.length && (
                <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-accent-400 align-middle" />
              )}
            </>
          ) : (
            message.text
          )}
        </div>
      </div>

      {!isInterviewer && (
        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-accent-500/40 bg-base-800 text-xs font-bold text-accent-400 shadow-md">
          You
        </div>
      )}
    </div>
  );
}
