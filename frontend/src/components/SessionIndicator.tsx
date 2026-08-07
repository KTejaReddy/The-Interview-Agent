interface SessionIndicatorProps {
  sessionId: string | null;
  state: string;
}

const STATE_COLORS: Record<string, string> = {
  INTRODUCTION: "text-amber-400 border-amber-400/30 bg-amber-400/10",
  QUESTIONING: "text-accent-400 border-accent-500/30 bg-accent-500/10",
  FOLLOW_UP: "text-mint-400 border-mint-500/30 bg-mint-500/10",
  FINAL_QUESTION: "text-mint-400 border-mint-500/30 bg-mint-500/10",
  DONE: "text-mint-400 border-mint-500/30 bg-mint-500/10",
};

export function SessionIndicator({ sessionId, state }: SessionIndicatorProps) {
  const shortId = sessionId ? sessionId.slice(0, 8) : null;
  const color = STATE_COLORS[state] ?? "text-slate-300 border-slate-500/30 bg-slate-500/10";
  return (
    <div className="flex items-center gap-2">
      {sessionId && (
        <span
          title={`Session ${sessionId}`}
          className="hidden rounded-md border border-slate-600/40 bg-base-800 px-2 py-0.5 font-mono text-[11px] text-slate-400 sm:inline-block"
        >
          session:{shortId}
        </span>
      )}
      <span className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-[11px] font-semibold ${color}`}>
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current" />
        {state}
      </span>
    </div>
  );
}
