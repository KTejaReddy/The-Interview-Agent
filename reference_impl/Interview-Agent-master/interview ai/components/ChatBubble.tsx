"use client";

import { motion } from "framer-motion";
import { InterviewMessage } from "@/types";
import clsx from "clsx";

const QUESTION_TYPE_LABELS: Record<string, string> = {
  opening: "Opening",
  technical: "Technical",
  follow_up: "Follow-up",
  probing: "Probing",
  synthesis: "Synthesis",
  closing: "Closing",
};

interface ChatBubbleProps {
  message: InterviewMessage;
}

export default function ChatBubble({ message }: ChatBubbleProps) {
  const isInterviewer = message.role === "interviewer";

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={clsx("flex items-end gap-3", isInterviewer ? "justify-start" : "justify-end")}
    >
      {isInterviewer && (
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand-violet to-brand-cyan text-sm shadow-glow">
          🤖
        </div>
      )}

      <div className={clsx("flex max-w-[75%] flex-col", isInterviewer ? "items-start" : "items-end")}>
        <div className={clsx("bubble-interviewer", !isInterviewer && "bubble-candidate")}>
          {isInterviewer && message.questionType && (
            <span className="mb-1.5 inline-block rounded-full border border-brand-violet/30 bg-brand-violet/10 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-brand-violet-light">
              {QUESTION_TYPE_LABELS[message.questionType] ?? message.questionType}
            </span>
          )}
          <p className="whitespace-pre-wrap text-[15px] leading-relaxed text-ink-primary">
            {message.content}
          </p>
        </div>
        <span className="mt-1.5 px-1 font-mono text-[10px] text-ink-muted">
          {new Date(message.timestamp).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
          {!isInterviewer && " · You"}
        </span>
      </div>

      {!isInterviewer && (
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white/8 text-sm">
          🧑‍💻
        </div>
      )}
    </motion.div>
  );
}
