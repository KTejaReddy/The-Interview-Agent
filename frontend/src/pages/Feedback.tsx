import { Brand } from "../components/Brand";
import { ScoreRing } from "../components/ScoreRing";
import { useInterview } from "../context/InterviewContext";
import type { Page } from "../types";
import { ArrowLeft, RotateCcw, Award, Target, Compass } from "lucide-react";

interface FeedbackProps {
  onNavigate: (page: Page) => void;
}

export function Feedback({ onNavigate }: FeedbackProps) {
  const { feedback, questionNumber, daysCovered, reset } = useInterview();

  if (!feedback) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-background">
        <div className="w-16 h-16 rounded-full bg-surface-100 border border-white/5 flex items-center justify-center animate-pulse">
          <div className="w-8 h-8 rounded-full bg-accent-500/50" />
        </div>
        <p className="text-base-400 font-medium">No feedback available yet.</p>
        <button
          onClick={() => onNavigate("landing")}
          className="rounded-xl bg-surface-100 border border-white/5 px-6 py-3 font-semibold text-white transition hover:bg-surface-200"
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
    <div className="relative min-h-screen bg-background pb-32 text-gray-200">

      {/* Background Atmosphere */}
      <div className="absolute bg-orb-1 top-[-10%] left-[-10%] w-[600px] h-[600px] pointer-events-none" />
      <div className="absolute bg-orb-2 top-[30%] right-[-10%] w-[600px] h-[600px] pointer-events-none" />
      <div className="absolute inset-0 tech-grid opacity-60 pointer-events-none" />

      {/* Header */}
      <header className="relative z-20 border-b border-white/5 bg-surface-50/80 backdrop-blur-md sticky top-0 py-4">
        <div className="mx-auto flex w-full max-w-5xl items-center justify-between px-6">
          <Brand />
          <button
            onClick={handleRestart}
            className="btn btn-secondary text-xs"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Start another interview
          </button>
        </div>
      </header>

      <div className="relative z-10 mx-auto max-w-5xl px-6 pt-12 animate-fade-up">

        {/* Document Header */}
        <div className="text-center mb-12">
          <p className="text-eyebrow text-accent-400 mb-3">Assessment Report</p>
          <h1
            className="text-4xl md:text-5xl font-black text-white mb-6 tracking-tight"
            style={{ letterSpacing: "-0.03em" }}
          >
            Performance Report
          </h1>

          <div className="inline-flex items-center justify-center gap-6 border-y border-white/10 py-4 px-12 glass-card rounded-2xl">
            <div className="flex flex-col items-center">
              <span className="text-[10px] font-bold uppercase tracking-widest text-base-500">Questions</span>
              <span className="stat-number font-bold text-xl text-white">{questionNumber}</span>
            </div>
            <div className="w-px h-8 bg-white/10" />
            <div className="flex flex-col items-center">
              <span className="text-[10px] font-bold uppercase tracking-widest text-base-500">Curriculum Days</span>
              <span className="stat-number font-bold text-xl text-white">{daysCovered.length}</span>
            </div>
            <div className="w-px h-8 bg-white/10" />
            <div className="flex flex-col items-center">
              <span className="text-[10px] font-bold uppercase tracking-widest text-base-500">Verdict</span>
              <span className="font-bold text-xl text-mint-400">Completed</span>
            </div>
          </div>
        </div>

        {/* The Interviewer's Take (Summary) */}
        <div className="glass-card p-8 mb-12 rounded-2xl relative overflow-hidden flex flex-col md:flex-row items-center md:items-start gap-8">
          <div className="absolute top-0 left-0 w-1.5 h-full bg-gradient-to-b from-accent-500 to-accent-cyan" />
          <div className="absolute inset-0 pointer-events-none" style={{ background: "radial-gradient(ellipse 60% 50% at 100% 0%, rgba(124,92,255,0.06) 0%, transparent 70%)" }} />
          {typeof feedback.score === "number" && (
            <div className="shrink-0 flex flex-col items-center gap-3 bg-surface-50/50 p-6 rounded-2xl border border-white/5 relative">
              <ScoreRing score={feedback.score} />
              <span className="text-[10px] font-bold uppercase tracking-widest text-base-400">Overall Score</span>
            </div>
          )}
          <div className="pt-2 relative">
            <h2 className="flex items-center gap-2 text-xl font-bold text-white mb-4">
              <Award className="w-5 h-5 text-accent-400" />
              Interviewer's Take
            </h2>
            <p className="text-base-300 leading-relaxed text-sm">
              {feedback.summary}
            </p>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6 mb-12">
          {/* Strengths */}
          <FeedbackSection
            icon={<Target className="w-4 h-4" />}
            title="Strengths"
            tone="mint"
            items={feedback.strengths}
            delay={100}
          />

          {/* Gaps */}
          <FeedbackSection
            icon={<Target className="w-4 h-4" />}
            title="Areas to Grow"
            tone="amber"
            items={feedback.gaps}
            delay={200}
          />
        </div>

        {/* Next steps */}
        <FeedbackSection
          icon={<Compass className="w-4 h-4" />}
          title="What to Study Next"
          tone="accent"
          items={feedback.next}
          delay={300}
        />

        <div className="mt-16 flex justify-center border-t border-white/10 pt-10 animate-fade-up" style={{ animationDelay: '400ms' }}>
          <button
            onClick={handleRestart}
            className="btn btn-primary !px-8 !py-4 text-[14px]"
          >
            <RotateCcw className="w-5 h-5" />
            Start New Interview Session
          </button>
        </div>
      </div>
    </div>
  );
}

interface FeedbackSectionProps {
  icon: React.ReactNode;
  title: string;
  tone: "mint" | "amber" | "accent";
  items: string[];
  delay: number;
}

function FeedbackSection({ icon, title, tone, items, delay }: FeedbackSectionProps) {
  if (!items || items.length === 0) return null;

  const tones = {
    mint: {
      bullet: "bg-mint-400 shadow-[0_0_10px_#34d399]",
      titleColor: "text-mint-400",
    },
    amber: {
      bullet: "bg-amber-400 shadow-[0_0_10px_#fbbf24]",
      titleColor: "text-amber-400",
    },
    accent: {
      bullet: "bg-accent-400 shadow-[0_0_10px_#9d8cff]",
      titleColor: "text-accent-400",
    },
  }[tone];

  return (
    <div
      className="glass-card rounded-2xl p-6 animate-fade-up border-t border-white/10 relative overflow-hidden"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="absolute inset-0 pointer-events-none" style={{ background: "radial-gradient(ellipse 60% 40% at 0% 0%, rgba(255,255,255,0.03) 0%, transparent 70%)" }} />
      <h2 className={`flex items-center gap-2 text-lg font-bold ${tones.titleColor} mb-4`}>
        {icon}
        {title}
      </h2>
      <ul className="space-y-4">
        {items.map((item, index) => (
          <li key={index} className="flex items-start gap-3">
            <span className={`mt-2 h-1.5 w-1.5 shrink-0 rounded-full ${tones.bullet}`} />
            <span className="text-sm leading-relaxed text-base-300">
              {item}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
