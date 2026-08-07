interface QuestionCounterProps {
  questionNumber: number;
  totalQuestions: number;
}

export function QuestionCounter({ questionNumber, totalQuestions }: QuestionCounterProps) {
  const label =
    totalQuestions > 0
      ? `Question ${questionNumber} / ${totalQuestions}`
      : "Preparing…";
  return (
    <div className="flex items-center gap-2 rounded-full border border-accent-500/30 bg-accent-500/10 px-3 py-1.5">
      <span className="h-1.5 w-1.5 rounded-full bg-accent-400" />
      <span className="text-xs font-semibold tracking-wide text-accent-400">
        {label}
      </span>
    </div>
  );
}
