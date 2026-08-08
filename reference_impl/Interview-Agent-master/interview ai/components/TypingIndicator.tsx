"use client";

export default function TypingIndicator() {
  return (
    <div className="flex items-start gap-3 animate-in">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand-violet to-brand-cyan text-sm shadow-glow">
        🤖
      </div>
      <div
        className="bubble-interviewer !max-w-[75%]"
        style={{ padding: "14px 18px" }}
      >
        <div className="flex items-center gap-1.5">
          <span className="typing-dot" />
          <span className="typing-dot" />
          <span className="typing-dot" />
        </div>
      </div>
    </div>
  );
}
