interface DayBadgeProps {
  day: string | null;
  topic?: string | null;
}

export function DayBadge({ day, topic }: DayBadgeProps) {
  if (!day) return null;
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <span className="rounded-md border border-mint-500/30 bg-mint-500/10 px-2 py-0.5 text-[11px] font-semibold text-mint-400">
        {day}
      </span>
      {topic && (
        <span className="rounded-md border border-slate-500/30 bg-slate-500/10 px-2 py-0.5 font-mono text-[11px] text-slate-300">
          {topic}
        </span>
      )}
    </div>
  );
}
