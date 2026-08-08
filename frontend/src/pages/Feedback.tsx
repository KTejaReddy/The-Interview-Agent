import { Brand } from "../components/Brand";
import { ScoreRing } from "../components/ScoreRing";
import { useInterview } from "../context/InterviewContext";
import type { Page } from "../types";
import { ArrowLeft, RotateCcw } from "lucide-react";

interface FeedbackProps {
  onNavigate: (page: Page) => void;
}

export function Feedback({ onNavigate }: FeedbackProps) {
  const { feedback, questionNumber, daysCovered, reset } = useInterview();

  if (!feedback) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-background">
        <div className="w-16 h-16 rounded-full bg-surface-100 border border-surface-200 shadow-inner flex items-center justify-center animate-pulse">
          <div className="w-8 h-8 rounded-full bg-accent-500/50" />
        </div>
        <p className="text-base-500 font-medium">No feedback available yet.</p>
        <button
          onClick={() => onNavigate("landing")}
          className="rounded-xl bg-surface-100 border border-surface-200 px-6 py-3 font-semibold text-base-900 transition hover:bg-surface-200 shadow-sm"
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
    <div className="relative min-h-screen bg-background pb-32">
      <div className="absolute inset-0 bg-paper-texture opacity-50 pointer-events-none" />
      
      {/* Editorial Header */}
      <header className="relative z-20 border-b border-surface-200 bg-surface-50/80 backdrop-blur-md sticky top-0 py-4">
        <div className="mx-auto flex w-full max-w-4xl items-center justify-between px-6">
          <Brand />
          <button
            onClick={handleRestart}
            className="flex items-center gap-2 rounded-xl bg-white border border-surface-200 px-5 py-2.5 text-sm font-semibold text-base-700 transition-all hover:bg-surface-50 editorial-shadow"
          >
            <ArrowLeft className="w-4 h-4" />
            Start another interview
          </button>
        </div>
      </header>

      <div className="relative z-10 mx-auto max-w-4xl px-6 pt-12 animate-fade-up">
        
        {/* Document Header */}
        <div className="text-center mb-12">
          <p className="text-xs font-bold uppercase tracking-widest text-base-400 mb-4">Final Evaluation Document</p>
          <h1 className="font-serif text-5xl font-black text-base-900 mb-6">Performance Report</h1>
          
          <div className="inline-flex items-center gap-6 border-y border-surface-200 py-3">
            <div className="flex flex-col items-center">
              <span className="text-[10px] font-bold uppercase tracking-widest text-base-400">Questions</span>
              <span className="font-serif font-bold text-lg text-base-900">{questionNumber}</span>
            </div>
            <div className="w-px h-8 bg-surface-200" />
            <div className="flex flex-col items-center">
              <span className="text-[10px] font-bold uppercase tracking-widest text-base-400">Curriculum Days</span>
              <span className="font-serif font-bold text-lg text-base-900">{daysCovered.length}</span>
            </div>
            <div className="w-px h-8 bg-surface-200" />
            <div className="flex flex-col items-center">
              <span className="text-[10px] font-bold uppercase tracking-widest text-base-400">Verdict</span>
              <span className="font-serif font-bold text-lg text-base-900">Completed</span>
            </div>
          </div>
        </div>

        {/* The Interviewer's Take (Summary) */}
        <div className="editorial-card p-10 mb-12 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-2 h-full bg-accent-500" />
          <div className="flex flex-col sm:flex-row items-center sm:items-start gap-8">
            {typeof feedback.score === "number" && (
              <div className="shrink-0 flex flex-col items-center gap-2">
                <ScoreRing score={feedback.score} />
                <span className="text-[10px] font-bold uppercase tracking-widest text-base-400">Overall Score</span>
              </div>
            )}
            <div>
              <h2 className="font-serif text-2xl font-bold text-base-900 mb-4">Interviewer's Take</h2>
              <p className="text-base-700 leading-[1.8] text-[15px]">
                {feedback.summary}
              </p>
            </div>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-8 mb-12">
          {/* Strengths */}
          <FeedbackSection
            title="Strengths"
            tone="mint"
            items={feedback.strengths}
            delay={100}
          />

          {/* Gaps */}
          <FeedbackSection
            title="Areas to Grow"
            tone="amber"
            items={feedback.gaps}
            delay={200}
          />
        </div>

        {/* Next steps */}
        <FeedbackSection
          title="What to Study Next"
          tone="accent"
          items={feedback.next}
          delay={300}
        />

        <div className="mt-16 flex justify-center border-t border-surface-200 pt-10 animate-fade-up" style={{ animationDelay: '400ms' }}>
          <button
            onClick={handleRestart}
            className="flex items-center gap-3 rounded-xl bg-base-900 px-10 py-4 font-bold text-white transition-all duration-300 hover:bg-base-800 hover:-translate-y-0.5 shadow-lg"
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
  title: string;
  tone: "mint" | "amber" | "accent";
  items: string[];
  delay: number;
}

function FeedbackSection({ title, tone, items, delay }: FeedbackSectionProps) {
  if (!items || items.length === 0) return null;

  const tones = {
    mint: {
      bullet: "bg-mint-500",
      titleColor: "text-base-900",
    },
    amber: {
      bullet: "bg-amber-500",
      titleColor: "text-base-900",
    },
    accent: {
      bullet: "bg-accent-500",
      titleColor: "text-base-900",
    },
  }[tone];

  return (
    <div
      className="animate-fade-up"
      style={{ animationDelay: `${delay}ms` }}
    >
      <h2 className={`font-serif text-xl font-bold ${tones.titleColor} mb-4 border-b border-surface-200 pb-2`}>
        {title}
      </h2>
      <ul className="space-y-4 mt-4">
        {items.map((item, index) => (
          <li key={index} className="flex items-start gap-4">
            <span className={`mt-2 h-2 w-2 shrink-0 rounded-full ${tones.bullet}`} />
            <span className="text-[15px] leading-relaxed text-base-700">
              {item}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
