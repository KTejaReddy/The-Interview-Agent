interface ProgressBarProps {
  questionNumber: number;
  totalQuestions: number;
}

export function ProgressBar({ questionNumber, totalQuestions }: ProgressBarProps) {
  const percent =
    totalQuestions > 0 ? Math.min(100, Math.round((questionNumber / totalQuestions) * 100)) : 0;
  return (
    <div className="w-full">
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-base-700/80">
        <div
          className="h-full rounded-full bg-gradient-to-r from-accent-500 via-indigo-400 to-mint-400 transition-all duration-700 ease-out"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
