interface CoverageTrackerProps {
  daysCovered: string[];
  minDays?: number;
  totalQuestions?: number;
  minQuestions?: number;
}

export function CoverageTracker({
  daysCovered,
  minDays = 4,
  totalQuestions = 0,
  minQuestions = 8,
}: CoverageTrackerProps) {
  const dayCount = daysCovered.length;
  const dayComplete = dayCount >= minDays;
  const questionComplete = totalQuestions >= minQuestions;

  return (
    <div className="w-56 glass-card rounded-2xl p-5 shadow-lg relative overflow-hidden group">
      <div className="absolute inset-0 bg-premium-gradient opacity-0 group-hover:opacity-5 transition-opacity duration-500" />
      
      <div className="flex items-center justify-between mb-4 relative z-10">
        <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
          Curriculum coverage
        </p>
        <span
          className={`flex h-6 w-6 items-center justify-center rounded-full text-[10px] font-bold shadow-inner border ${
            dayComplete
              ? "bg-mint-500/10 text-mint-400 border-mint-500/20"
              : "bg-surface-300 text-slate-300 border-white/5"
          }`}
        >
          {dayCount}
        </span>
      </div>

      {/* Requirement meter */}
      <div className="space-y-4 relative z-10">
        <RequirementMeter
          label={`${minDays} curriculum days`}
          value={Math.min(dayCount, minDays)}
          target={minDays}
          complete={dayComplete}
        />
        <RequirementMeter
          label={`${minQuestions} questions`}
          value={Math.min(totalQuestions, minQuestions)}
          target={minQuestions}
          complete={questionComplete}
        />
      </div>

      {/* Day chips */}
      <div className="mt-5 relative z-10">
        {daysCovered.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {daysCovered.map((day) => (
              <span
                key={day}
                title={day}
                className="inline-flex max-w-full items-center gap-1.5 rounded-md border border-white/5 bg-surface-200/80 px-2 py-1 text-[10px] font-semibold text-slate-300 shadow-inner"
              >
                <span className="h-1 w-1 shrink-0 rounded-full bg-accent-400" />
                <span className="truncate">{day}</span>
              </span>
            ))}
          </div>
        ) : (
          <p className="text-[10px] text-slate-500 italic">
            No curriculum days reached yet.
          </p>
        )}
      </div>
    </div>
  );
}

interface RequirementMeterProps {
  label: string;
  value: number;
  target: number;
  complete: boolean;
}

function RequirementMeter({ label, value, target, complete }: RequirementMeterProps) {
  const percent = Math.min(100, (value / target) * 100);
  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between text-[11px]">
        <span className="text-slate-400 font-medium">{label}</span>
        <span className={complete ? "font-bold text-mint-400" : "font-semibold text-slate-300"}>
          {value}/{target}
        </span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-surface-300/50 shadow-inner">
        <div
          className={`h-full rounded-full transition-all duration-1000 ${
            complete
              ? "bg-mint-400 shadow-[0_0_8px_rgba(52,211,153,0.5)]"
              : "bg-accent-400 shadow-[0_0_8px_rgba(129,140,248,0.5)]"
          }`}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
