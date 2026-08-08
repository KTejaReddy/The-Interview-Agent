interface CoverageTrackerProps {
  daysCovered: string[];
  minDays?: number;
  totalQuestions?: number;
  minQuestions?: number;
}

/**
 * Live curriculum-coverage panel: every distinct day the interview has
 * reached, plus progress toward the minimum requirements (8 questions,
 * 4 curriculum days).
 */
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
    <div className="w-56 rounded-2xl border border-base-700 bg-base-800/70 p-4 backdrop-blur">
      <div className="flex items-center justify-between">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
          Curriculum coverage
        </p>
        <span
          className={`flex h-5 w-5 items-center justify-center rounded-full text-[11px] font-bold ${
            dayComplete
              ? "bg-mint-500/20 text-mint-400"
              : "bg-accent-500/15 text-accent-400"
          }`}
        >
          {dayCount}
        </span>
      </div>

      {/* Requirement meter */}
      <div className="mt-3 space-y-2">
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
      {daysCovered.length > 0 ? (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {daysCovered.map((day) => (
            <span
              key={day}
              title={day}
              className="inline-flex max-w-full items-center gap-1 rounded-full border border-mint-500/25 bg-mint-500/10 px-2 py-0.5 text-[11px] font-medium text-mint-300"
            >
              <span className="h-1 w-1 shrink-0 rounded-full bg-mint-400" />
              <span className="truncate">{day}</span>
            </span>
          ))}
        </div>
      ) : (
        <p className="mt-3 text-[11px] text-slate-500">
          No curriculum days reached yet.
        </p>
      )}
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
      <div className="mb-1 flex items-center justify-between text-[11px]">
        <span className="text-slate-400">{label}</span>
        <span className={complete ? "font-semibold text-mint-400" : "font-semibold text-slate-300"}>
          {value}/{target}
        </span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-base-700">
        <div
          className={`h-full rounded-full transition-all duration-700 ${
            complete
              ? "bg-gradient-to-r from-mint-500 to-emerald-400"
              : "bg-gradient-to-r from-accent-600 to-indigo-400"
          }`}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
