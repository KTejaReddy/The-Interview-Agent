interface DayBadgeProps {
  day: string | null;
  topic?: string | null;
}

export function DayBadge({ day, topic }: DayBadgeProps) {
  if (!day) return null;
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="rounded-lg border border-accent-purple/30 bg-accent-purple/10 px-2.5 py-1 text-[11px] font-bold text-accent-purple shadow-inner">
        {day}
      </span>
      {topic && (
        <span className="rounded-lg border border-white/10 bg-surface-200/50 px-2.5 py-1 text-[11px] font-medium text-slate-300 shadow-inner">
          {topic}
        </span>
      )}
    </div>
  );
}
