import { Brand } from "../components/Brand";
import { ScoreRing } from "../components/ScoreRing";
import { useInterview } from "../context/InterviewContext";
import type { Page } from "../types";
import { ArrowLeft, CheckCircle2, AlertTriangle, ArrowRight, RotateCcw } from "lucide-react";

interface FeedbackProps {
  onNavigate: (page: Page) => void;
}

export function Feedback({ onNavigate }: FeedbackProps) {
  const { feedback, questionNumber, daysCovered, reset } = useInterview();

  if (!feedback) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-background">
        <div className="w-16 h-16 rounded-full bg-surface-200 border border-white/5 shadow-inner flex items-center justify-center animate-pulse">
          <div className="w-8 h-8 rounded-full bg-accent-500/50" />
        </div>
        <p className="text-slate-400 font-medium">No feedback available yet.</p>
        <button
          onClick={() => onNavigate("landing")}
          className="rounded-xl bg-surface-200 border border-white/10 px-6 py-3 font-semibold text-white transition hover:bg-surface-300 shadow-md"
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
    <div className="relative min-h-screen overflow-hidden bg-background">
      {/* Background Orbs */}
      <div className="bg-orb-1 top-[-10%] left-1/2 -translate-x-1/2 w-[800px] h-[800px] opacity-20" />
      
      <div className="relative z-10 mx-auto max-w-4xl px-6 pb-32 pt-8">
        <header className="mb-12 flex items-center justify-between backdrop-blur-md sticky top-0 py-4 z-50">
          <Brand />
          <button
            onClick={handleRestart}
            className="flex items-center gap-2 rounded-xl border border-white/10 bg-surface-100/50 px-5 py-2.5 text-sm font-semibold text-slate-300 transition-all hover:bg-surface-200 hover:text-white shadow-sm hover:shadow-md"
          >
            <ArrowLeft className="w-4 h-4" />
            Start another interview
          </button>
        </header>

        <div className="animate-fade-up">
          {/* Hero card */}
          <div className="rounded-[2rem] border border-white/10 bg-surface-100/60 p-8 md:p-12 shadow-2xl backdrop-blur-xl relative overflow-hidden group">
            <div className="absolute inset-0 bg-premium-gradient opacity-[0.02] group-hover:opacity-[0.04] transition-opacity duration-700" />
            
            <div className="relative z-10">
              <div className="mb-6 inline-flex flex-wrap items-center gap-2 rounded-lg border border-mint-500/20 bg-mint-500/10 px-3 py-1.5 text-[11px] font-bold tracking-wide uppercase text-mint-400 shadow-inner">
                <span className="h-1.5 w-1.5 rounded-full bg-mint-400 animate-pulse" />
                Interview complete
              </div>
              
              <div className="flex flex-col items-center text-center sm:flex-row sm:items-center sm:text-left gap-8 md:gap-12">
                {typeof feedback.score === "number" && (
                  <div className="shrink-0 scale-110">
                    <ScoreRing score={feedback.score} />
                  </div>
                )}
                <div className="min-w-0 flex-1">
                  <h1 className="text-4xl font-black tracking-tight text-white md:text-5xl mb-4">
                    Performance Report
                  </h1>
                  <p className="text-[15px] leading-relaxed text-slate-300 bg-surface-200/50 p-5 rounded-2xl border border-white/5 shadow-inner">
                    {feedback.summary}
                  </p>
                  
                  <div className="mt-6 flex flex-wrap gap-3">
                    <span className="px-3 py-1.5 rounded-lg bg-surface-200 border border-white/5 text-xs font-semibold text-slate-400">
                      {questionNumber} questions answered
                    </span>
                    <span className="px-3 py-1.5 rounded-lg bg-surface-200 border border-white/5 text-xs font-semibold text-slate-400">
                      {daysCovered.length} curriculum days covered
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-6 mt-8">
            {/* Strengths */}
            <FeedbackSection
              title="Key Strengths"
              tone="mint"
              icon={<CheckCircle2 className="w-5 h-5" />}
              items={feedback.strengths}
              delay={100}
            />

            {/* Gaps */}
            <FeedbackSection
              title="Areas for Growth"
              tone="amber"
              icon={<AlertTriangle className="w-5 h-5" />}
              items={feedback.gaps}
              delay={200}
            />
          </div>

          {/* Next steps */}
          <div className="mt-6">
            <FeedbackSection
              title="Actionable Next Steps"
              tone="accent"
              icon={<ArrowRight className="w-5 h-5" />}
              items={feedback.next}
              delay={300}
            />
          </div>

          <div className="mt-16 flex justify-center animate-fade-up" style={{ animationDelay: '400ms' }}>
            <button
              onClick={handleRestart}
              className="flex items-center gap-3 rounded-2xl bg-gradient-to-r from-accent-600 to-indigo-500 px-8 py-4 font-bold text-white shadow-xl shadow-accent-600/20 transition-all duration-300 hover:shadow-2xl hover:shadow-accent-600/40 hover:-translate-y-1 active:scale-95"
            >
              <RotateCcw className="w-5 h-5" />
              Start New Interview Session
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
  icon: React.ReactNode;
  items: string[];
  delay: number;
}

function FeedbackSection({ title, tone, icon, items, delay }: FeedbackSectionProps) {
  if (!items || items.length === 0) return null;

  const tones = {
    mint: {
      card: "border-mint-500/20 bg-gradient-to-br from-surface-100/80 to-mint-500/5",
      iconBg: "bg-mint-500/15 text-mint-400 border border-mint-500/20 shadow-inner",
      title: "text-mint-400",
      bullet: "bg-mint-500",
    },
    amber: {
      card: "border-amber-500/20 bg-gradient-to-br from-surface-100/80 to-amber-500/5",
      iconBg: "bg-amber-500/15 text-amber-400 border border-amber-500/20 shadow-inner",
      title: "text-amber-400",
      bullet: "bg-amber-500",
    },
    accent: {
      card: "border-accent-500/20 bg-gradient-to-br from-surface-100/80 to-accent-500/5",
      iconBg: "bg-accent-500/15 text-accent-400 border border-accent-500/20 shadow-inner",
      title: "text-accent-400",
      bullet: "bg-accent-500",
    },
  }[tone];

  return (
    <div
      className={`rounded-[1.5rem] border ${tones.card} p-8 animate-fade-up backdrop-blur-md shadow-lg`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <h2 className={`flex items-center gap-3 text-xl font-bold ${tones.title} mb-6`}>
        <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${tones.iconBg}`}>
          {icon}
        </span>
        {title}
      </h2>
      <ul className="space-y-4">
        {items.map((item, index) => (
          <li key={index} className="flex items-start gap-4">
            <span className={`mt-2 h-1.5 w-1.5 shrink-0 rounded-full ${tones.bullet} shadow-[0_0_8px_currentColor] opacity-70`} />
            <span className="text-[15px] leading-relaxed text-slate-300 font-medium">
              {item}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
