import { useTypingEffect } from "../hooks/useTypingEffect";
import type { ChatMessage as ChatMessageType } from "../types";

interface ChatMessageProps {
  message: ChatMessageType;
  isLast: boolean;
}

export function ChatMessage({ message, isLast }: ChatMessageProps) {
  const isInterviewer = message.role === "interviewer";
  const revealed = useTypingEffect(message.text, isInterviewer && isLast, 15);

  return (
    <div className={`flex flex-col gap-1.5 ${isInterviewer ? "animate-fade-in" : "animate-fade-in opacity-90"}`}>
      <div className="flex items-center gap-2">
        {isInterviewer ? (
          <div className="flex items-center gap-2">
            <span className="font-bold text-white text-sm">Alex</span>
            <span className="text-[9px] text-base-500 uppercase tracking-widest font-bold">Interviewer</span>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <span className="font-bold text-accent-400 text-sm">You</span>
            <span className="text-[9px] text-base-500 uppercase tracking-widest font-bold">Candidate</span>
          </div>
        )}
      </div>
      
      <div className={`p-4 rounded-xl border ${isInterviewer ? 'bg-surface-50/50 border-white/5' : 'bg-accent-500/10 border-accent-500/20'}`}>
        <p className={`text-[14px] leading-relaxed ${isInterviewer ? "text-gray-200 font-medium" : "text-gray-300"}`}>
          {isInterviewer && isLast ? (
            <>
              {revealed}
              {revealed.length < message.text.length && (
                <span className="ml-0.5 inline-block h-4 w-1.5 animate-pulse bg-accent-500 align-middle" />
              )}
            </>
          ) : (
            message.text
          )}
        </p>
      </div>
    </div>
  );
}
