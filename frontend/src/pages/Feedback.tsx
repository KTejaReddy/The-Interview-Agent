import { Brand } from "../components/Brand";
import { ScoreRing } from "../components/ScoreRing";
import { useInterview } from "../context/InterviewContext";
import type { Page } from "../types";

interface FeedbackProps {
  onNavigate: (page: Page) => void;
}

export function Feedback({ onNavigate }: FeedbackProps) {
  const { feedback, questionNumber, daysCovered, reset } = useInterview();

  if (!feedback) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-base-950">
        <p className="text-slate-400">No feedback available yet.</p>
        <button
          onClick={() => onNavigate("landing")}
          className="rounded-xl bg-accent-600 px-5 py-2.5 font-semibold text-white transition hover:brightness-110"
        >
          Back to start
        </button>
      </div>
    );
  }

  const handleRestart = () => {
    reset();
    onNavigate("landing");
  };

  return (
    <div className="relative min-h-screen overflow-hidden">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -top-24 left-1/2 h-[400px] w-[640px] -translate-x-1/2 rounded-full bg-mint-500/15 blur-[120px]" />
      </div>

      <div className="relative mx-auto max-w-3xl px-6 pb-24 pt-10">
        <header className="mb-10 flex items-center justify-between">
          <Brand />
          <button
            onClick={handleRestart}
            className="rounded-xl border border-base-700 bg-base-800 px-4 py-2 text-sm font-medium text-slate-300 transition hover:border-accent-500/40 hover:text-white"
          >
            ← Start another interview
          </button>
        </header>

        <div className="animate-fade-up">
          {/* Hero card */}
          <div className="rounded-3xl border border-mint-500/25 bg-gradient-to-br from-base-800 to-base-900 p-8 shadow-2xl shadow-black/40">
            <div className="mb-2 inline-flex flex-wrap items-center gap-2 rounded-full border border-mint-500/30 bg-mint-500/10 px-3 py-1 text-xs font-semibold text-mint-400">
              <span className="h-1.5 w-1.5 rounded-full bg-mint-400" />
              Interview complete · {questionNumber} questions ·{" "}
              {daysCovered.length} curriculum {daysCovered.length === 1 ? "day" : "days"}
            </div>
            <div className="mt-4 flex flex-col items-start gap-6 sm:flex-row sm:items-center">
              {typeof feedback.score === "number" && (
                <div className="shrink-0">
                  <ScoreRing score={feedback.score} />
                </div>
              )}
              <div className="min-w-0">
                <h1 className="text-3xl font-extrabold tracking-tight text-white md:text-4xl">
                  Your interview feedback
                </h1>
                <p className="mt-4 text-[15px] leading-relaxed text-slate-300">
                  {feedback.summary}
                </p>
              </div>
            </div>
          </div>

          {/* Strengths */}
          <FeedbackSection
            title="Strengths"
            tone="mint"
            icon="✓"
            items={feedback.strengths}
            delay={80}
          />

          {/* Gaps */}
          <FeedbackSection
            title="Areas to grow"
            tone="amber"
            icon="▲"
            items={feedback.gaps}
            delay={160}
          />

          {/* Next steps */}
          <FeedbackSection
            title="What to study next"
            tone="accent"
            icon="→"
            items={feedback.next}
            delay={240}
          />

          <div className="mt-10 flex justify-center">
            <button
              onClick={handleRestart}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-accent-600 to-indigo-500 px-8 py-3.5 font-semibold text-white shadow-lg shadow-accent-600/30 transition-all duration-200 hover:shadow-xl hover:brightness-110 active:scale-[0.98]"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M4 12a8 8 0 1 0 2.3-5.6M4 4v4h4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              Practice again
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

interface FeedbackSectionProps {
  title: string;
  tone: "mint" | "amber" | "accent";
  icon: string;
  items: string[];
  delay: number;
}

function FeedbackSection({ title, tone, icon, items, delay }: FeedbackSectionProps) {
  const tones = {
    mint: {
      border: "border-mint-500/25",
      iconBg: "bg-mint-500/15 text-mint-400",
      title: "text-mint-400",
    },
    amber: {
      border: "border-amber-400/25",
      iconBg: "bg-amber-400/15 text-amber-400",
      title: "text-amber-400",
    },
    accent: {
      border: "border-accent-500/25",
      iconBg: "bg-accent-500/15 text-accent-400",
      title: "text-accent-400",
    },
  }[tone];

  return (
    <div
      className={`mt-6 rounded-2xl border ${tones.border} bg-base-800/60 p-6 animate-fade-up`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <h2 className={`flex items-center gap-2.5 text-lg font-bold ${tones.title}`}>
        <span className={`flex h-7 w-7 items-center justify-center rounded-lg text-sm font-bold ${tones.iconBg}`}>
          {icon}
        </span>
        {title}
      </h2>
      <ul className="mt-4 space-y-3">
        {items.map((item, index) => (
          <li key={index} className="flex items-start gap-3 text-[15px] leading-relaxed text-slate-200">
            <span className={`mt-2 h-1.5 w-1.5 shrink-0 rounded-full ${tones.iconBg}`} />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
