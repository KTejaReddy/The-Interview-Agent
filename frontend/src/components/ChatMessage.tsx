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
    <div className={`flex flex-col gap-2 ${isInterviewer ? "animate-fade-in" : "animate-fade-in opacity-90"}`}>
      <div className="flex items-center gap-2">
        {isInterviewer ? (
          <div className="flex items-center gap-2">
            <span className="font-serif font-bold text-base-900 text-sm">Alex</span>
            <span className="text-[10px] text-base-400 uppercase tracking-widest font-semibold">Interviewer</span>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <span className="font-serif font-bold text-accent-600 text-sm">You</span>
            <span className="text-[10px] text-base-400 uppercase tracking-widest font-semibold">Candidate</span>
          </div>
        )}
      </div>
      
      <div className="pl-0">
        <p className={`text-[15px] leading-[1.7] ${isInterviewer ? "text-base-900 font-medium" : "text-base-700"}`}>
          {isInterviewer && isLast ? (
            <>
              {revealed}
              {revealed.length < message.text.length && (
                <span className="ml-0.5 inline-block h-4 w-1.5 animate-pulse bg-accent-400 align-middle" />
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
