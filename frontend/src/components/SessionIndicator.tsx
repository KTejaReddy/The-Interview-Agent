interface SessionIndicatorProps {
  sessionId: string | null;
  state: string;
}

const STATE_COLORS: Record<string, string> = {
  INTRODUCTION: "text-amber-400 border-amber-500/20 bg-amber-500/10",
  QUESTIONING: "text-accent-400 border-accent-500/20 bg-accent-500/10",
  FOLLOW_UP: "text-mint-400 border-mint-500/20 bg-mint-500/10",
  FINAL_QUESTION: "text-mint-400 border-mint-500/20 bg-mint-500/10",
  DONE: "text-white border-white/20 bg-white/10",
};

export function SessionIndicator({ sessionId, state }: SessionIndicatorProps) {
  const shortId = sessionId ? sessionId.slice(0, 8) : null;
  const color = STATE_COLORS[state] ?? "text-slate-300 border-white/10 bg-surface-200";
  return (
    <div className="flex items-center gap-2">
      {sessionId && (
        <span
          title={`Session ${sessionId}`}
          className="hidden rounded-lg border border-white/5 bg-surface-200/50 px-2 py-1 font-mono text-[10px] text-slate-400 sm:inline-block shadow-inner"
        >
          {shortId}
        </span>
      )}
      <span className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-[10px] uppercase tracking-wider font-bold shadow-inner ${color}`}>
        {state !== "DONE" && <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current" />}
        {state.replace("_", " ")}
      </span>
    </div>
  );
}
