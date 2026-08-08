import { useTypingEffect } from "../hooks/useTypingEffect";
import type { ChatMessage as ChatMessageType } from "../types";
import { DayBadge } from "./DayBadge";
import { User } from "lucide-react";

interface ChatMessageProps {
  message: ChatMessageType;
  isLast: boolean;
}

export function ChatMessage({ message, isLast }: ChatMessageProps) {
  const isInterviewer = message.role === "interviewer";
  const revealed = useTypingEffect(message.text, isInterviewer && isLast, 15);

  return (
    <div
      className={`flex items-start gap-4 ${
        isInterviewer ? "animate-slide-in-left" : "animate-slide-in-right justify-end"
      }`}
    >
      {isInterviewer && (
        <div className="mt-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-surface-200 border border-white/10 shadow-lg shadow-black/20">
          <div className="w-full h-full rounded-full bg-gradient-to-br from-accent-600/20 to-accent-purple/20 flex items-center justify-center">
            <span className="font-bold text-accent-400 text-sm">A</span>
          </div>
        </div>
      )}

      <div className={`flex flex-col gap-1 max-w-[85%] md:max-w-[75%] ${isInterviewer ? "" : "items-end"}`}>
        {isInterviewer && (
          <div className="flex items-center gap-2 pl-1 mb-0.5">
            <span className="text-xs font-semibold text-white">Alex</span>
            <span className="text-[10px] text-slate-500 font-medium">Technical Interviewer</span>
          </div>
        )}
        
        {message.isQuestion && isInterviewer && (
          <div className="mb-2">
            <DayBadge day={message.currentDay ?? null} topic={message.currentTopic} />
          </div>
        )}
        
        <div
          className={`rounded-2xl px-5 py-3.5 text-[15px] leading-relaxed shadow-lg backdrop-blur-sm ${
            isInterviewer
              ? "rounded-tl-sm border border-white/5 bg-surface-100/80 text-slate-100"
              : "rounded-tr-sm border border-white/10 bg-surface-300 text-white"
          }`}
        >
          {isInterviewer && isLast ? (
            <>
              {revealed}
              {revealed.length < message.text.length && (
                <span className="ml-0.5 inline-block h-4 w-1 animate-pulse bg-accent-400 align-middle rounded-full" />
              )}
            </>
          ) : (
            message.text
          )}
        </div>
      </div>

      {!isInterviewer && (
        <div className="mt-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-surface-200 border border-white/10 shadow-lg shadow-black/20">
          <User className="w-5 h-5 text-slate-400" />
        </div>
      )}
    </div>
  );
}
