"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  Award,
  Calendar,
  CheckCircle2,
  Clock,
  Download,
  FileText,
  ListChecks,
  RotateCcw,
  Sparkles,
  TriangleAlert,
} from "lucide-react";
import { Candidate, FeedbackReport as FeedbackReportType } from "@/types";
import { useInterviewStore } from "@/lib/store";
import ScoreRing from "./ScoreRing";

interface FeedbackReportProps {
  feedback: FeedbackReportType;
  candidate: Candidate | null;
  questionsAsked: number;
  daysCovered: number[];
  startedAt: number | null;
}

const RECOMMENDATION_CONFIG: Record<
  string,
  { label: string; icon: string; text: string; border: string; bg: string }
> = {
  strong_hire: {
    label: "Strong Hire",
    icon: "⭐",
    text: "text-brand-emerald",
    border: "border-brand-emerald/40",
    bg: "bg-brand-emerald/10",
  },
  hire: {
    label: "Hire",
    icon: "✅",
    text: "text-brand-cyan",
    border: "border-brand-cyan/40",
    bg: "bg-brand-cyan/10",
  },
  consider: {
    label: "Consider",
    icon: "🔶",
    text: "text-brand-amber",
    border: "border-brand-amber/40",
    bg: "bg-brand-amber/10",
  },
  needs_growth: {
    label: "Needs Growth",
    icon: "📈",
    text: "text-brand-rose",
    border: "border-brand-rose/40",
    bg: "bg-brand-rose/10",
  },
};

// Confetti palette
const CONFETTI_COLORS = ["#7C3AED", "#06B6D4", "#10B981", "#F59E0B", "#F43F5E", "#9D6FEF"];

function topicBarColor(score: number): string {
  if (score >= 8) return "bg-brand-emerald";
  if (score >= 5) return "bg-brand-amber";
  return "bg-brand-rose";
}

export default function FeedbackReport({
  feedback,
  candidate,
  questionsAsked,
  daysCovered,
  startedAt,
}: FeedbackReportProps) {
  const router = useRouter();
  const reset = useInterviewStore((s) => s.reset);

  // ── Confetti pieces (memoized, one-shot on mount) ──────────────────────────
  const confetti = useMemo(
    () =>
      Array.from({ length: 60 }, (_, i) => ({
        id: i,
        left: Math.random() * 100,
        color: CONFETTI_COLORS[i % CONFETTI_COLORS.length],
        w: 6 + Math.random() * 6,
        h: 8 + Math.random() * 8,
        duration: 2.8 + Math.random() * 2.5,
        delay: Math.random() * 0.8,
      })),
    []
  );

  const recommendation = feedback.recommendation
    ? RECOMMENDATION_CONFIG[feedback.recommendation]
    : RECOMMENDATION_CONFIG.hire;

  // Session duration
  const durationLabel = useMemo(() => {
    if (!startedAt) return "—";
    const ms = Math.max(0, Date.now() - startedAt);
    const totalSec = Math.floor(ms / 1000);
    const mins = Math.floor(totalSec / 60);
    const secs = totalSec % 60;
    return `${mins}m ${secs}s`;
  }, [startedAt]);

  const interviewDate = useMemo(() => {
    if (!startedAt) return new Date().toLocaleDateString();
    return new Date(startedAt).toLocaleDateString(undefined, {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  }, [startedAt]);

  const handleDownload = () => {
    const lines = [
      "═══════════════════════════════════════════",
      "  AI INTERVIEW AGENT — FEEDBACK REPORT",
      "═══════════════════════════════════════════",
      `Candidate : ${candidate?.member.name ?? "—"}`,
      `Role      : ${candidate?.member.jobRole ?? "—"}`,
      `Date      : ${interviewDate}`,
      `Questions : ${questionsAsked}`,
      `Days      : ${daysCovered.length}`,
      `Duration  : ${durationLabel}`,
      `Score     : ${feedback.overallScore ?? "—"}/100`,
      `Hire Rec. : ${feedback.recommendation ?? "—"}`,
      "",
      "SUMMARY",
      "───────",
      feedback.summary,
      "",
      "STRENGTHS",
      "─────────",
      ...feedback.strengths.map((s, i) => `${i + 1}. ${s}`),
      "",
      "GAPS",
      "────",
      ...feedback.gaps.map((s, i) => `${i + 1}. ${s}`),
      "",
      "NEXT STEPS",
      "──────────",
      ...feedback.next.map((s, i) => `${i + 1}. ${s}`),
    ];
    const blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `interview-feedback-${candidate?.member.id ?? "report"}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleNewInterview = () => {
    reset();
    router.push("/");
  };

  return (
    <div className="relative mx-auto w-full max-w-5xl px-4 pb-20 pt-10 sm:px-6">
      {/* Confetti overlay */}
      <div className="pointer-events-none fixed inset-0 z-50 overflow-hidden">
        {confetti.map((c) => (
          <span
            key={c.id}
            className="confetti-piece"
            style={
              {
                left: `${c.left}%`,
                background: c.color,
                "--cw": `${c.w}px`,
                "--ch": `${c.h}px`,
                "--cd": `${c.duration}s`,
                "--c-delay": `${c.delay}s`,
              } as React.CSSProperties
            }
          />
        ))}
      </div>

      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-10 text-center"
      >
        <p className="mb-3 inline-flex items-center gap-1.5 rounded-full border border-brand-violet/30 bg-brand-violet/10 px-3 py-1 text-xs font-medium text-brand-violet-light">
          <Sparkles size={13} /> Interview Complete
        </p>
        <h1 className="font-display gradient-text text-4xl font-bold sm:text-5xl">
          🎉 Interview Complete
        </h1>
        <p className="mt-3 text-ink-secondary">
          {candidate?.member.name} · {candidate?.member.jobRole}
        </p>
        <p className="mt-1 flex items-center justify-center gap-1.5 text-xs text-ink-muted">
          <Calendar size={12} /> {interviewDate}
        </p>
      </motion.div>

      {/* Top metrics row */}
      <div className="grid gap-4 sm:grid-cols-3">
        {/* 1 — Overall score */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="glass-card flex flex-col items-center justify-center gap-2 p-6"
        >
          <ScoreRing score={feedback.overallScore ?? 0} label="Overall Score" />
        </motion.div>

        {/* 2 — Recommendation */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="glass-card flex flex-col items-center justify-center gap-4 p-6"
        >
          <p className="text-xs font-semibold uppercase tracking-widest text-ink-secondary">
            Recommendation
          </p>
          <div
            className={`flex items-center gap-2.5 rounded-2xl border ${recommendation.border} ${recommendation.bg} px-6 py-4`}
          >
            <span className="text-2xl">{recommendation.icon}</span>
            <span className={`text-xl font-bold ${recommendation.text}`}>
              {recommendation.label}
            </span>
          </div>
          <p className="text-center text-[11px] leading-snug text-ink-secondary">
            Based on overall score of {feedback.overallScore ?? "—"}/100 across covered topics
          </p>
        </motion.div>

        {/* 3 — Interview stats */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="glass-card flex flex-col items-center justify-center gap-4 p-6"
        >
          <p className="text-xs font-semibold uppercase tracking-widest text-ink-secondary">
            Interview Stats
          </p>
          <div className="flex w-full items-center justify-center gap-4">
            <div className="flex flex-col items-center rounded-xl border border-white/5 bg-white/[0.02] px-4 py-3">
              <p className="flex items-center gap-1 font-mono text-xl font-bold text-brand-violet-light">
                <ListChecks size={15} /> {questionsAsked}
              </p>
              <p className="text-[10px] uppercase tracking-wider text-ink-muted">Questions</p>
            </div>
            <div className="flex flex-col items-center rounded-xl border border-white/5 bg-white/[0.02] px-4 py-3">
              <p className="flex items-center gap-1 font-mono text-xl font-bold text-brand-cyan">
                <Award size={15} /> {daysCovered.length}
              </p>
              <p className="text-[10px] uppercase tracking-wider text-ink-muted">Days Covered</p>
            </div>
            <div className="flex flex-col items-center rounded-xl border border-white/5 bg-white/[0.02] px-4 py-3">
              <p className="flex items-center gap-1 font-mono text-xl font-bold text-brand-amber">
                <Clock size={15} /> {durationLabel}
              </p>
              <p className="text-[10px] uppercase tracking-wider text-ink-muted">Duration</p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Summary */}
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.35 }}
        className="glass-card mt-6 border-l-4 !border-l-brand-violet p-6"
      >
        <p className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-brand-violet-light">
          <FileText size={14} /> Summary
        </p>
        <blockquote className="text-lg leading-relaxed text-ink-primary">
          “{feedback.summary}”
        </blockquote>
      </motion.div>

      {/* Topic scores */}
      {feedback.topicScores && feedback.topicScores.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="glass-card mt-6 p-6"
        >
          <h3 className="mb-4 text-sm font-bold text-ink-primary">Topic Scores</h3>
          <div className="space-y-3.5">
            {feedback.topicScores.map((t, i) => (
              <div key={`${t.day}-${i}`} className="flex items-center gap-4">
                <span className="w-56 shrink-0 truncate text-xs font-medium text-ink-secondary">
                  <span className="font-mono text-brand-violet-light">Day {t.day}</span> · {t.topic.replace(/^Day \d+:?\s*/i, "")}
                </span>
                <div className="relative h-2.5 flex-1 overflow-hidden rounded-full bg-white/5">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min(100, t.score * 10)}%` }}
                    transition={{ duration: 0.9, delay: 0.5 + i * 0.08, ease: "easeOut" }}
                    className={`h-full rounded-full ${topicBarColor(t.score)}`}
                  />
                </div>
                <span
                  className={`w-8 shrink-0 text-right font-mono text-sm font-bold ${
                    t.score >= 8
                      ? "text-brand-emerald"
                      : t.score >= 5
                        ? "text-brand-amber"
                        : "text-brand-rose"
                  }`}
                >
                  {t.score}
                </span>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Strengths / Gaps */}
      <div className="mt-6 grid gap-6 md:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.45 }}
          className="glass-card p-6"
        >
          <h3 className="mb-4 flex items-center gap-2 text-sm font-bold text-brand-emerald">
            <CheckCircle2 size={16} /> Strengths
          </h3>
          <ul className="space-y-3">
            {feedback.strengths.map((s, i) => (
              <motion.li
                key={i}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.6 + i * 0.1 }}
                className="flex gap-2.5 text-sm leading-relaxed text-ink-secondary"
              >
                <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-emerald" />
                {s}
              </motion.li>
            ))}
          </ul>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.55 }}
          className="glass-card p-6"
        >
          <h3 className="mb-4 flex items-center gap-2 text-sm font-bold text-brand-amber">
            <TriangleAlert size={16} /> Gaps
          </h3>
          <ul className="space-y-3">
            {feedback.gaps.map((g, i) => (
              <motion.li
                key={i}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.7 + i * 0.1 }}
                className="flex gap-2.5 text-sm leading-relaxed text-ink-secondary"
              >
                <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-amber" />
                {g}
              </motion.li>
            ))}
          </ul>
        </motion.div>
      </div>

      {/* Next steps */}
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.65 }}
        className="glass-card mt-6 p-6"
      >
        <h3 className="mb-4 text-sm font-bold text-ink-primary">Next Steps</h3>
        <div className="space-y-3">
          {feedback.next.map((n, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.75 + i * 0.1 }}
              className="group flex items-start gap-4 rounded-xl border border-white/5 bg-white/[0.02] p-4 transition-colors hover:border-brand-violet/30"
            >
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-brand-violet to-brand-cyan font-mono text-sm font-bold text-white">
                {i + 1}
              </span>
              <p className="flex-1 text-sm leading-relaxed text-ink-primary">{n}</p>
              <ArrowRight
                size={16}
                className="mt-0.5 shrink-0 text-ink-muted transition-all group-hover:translate-x-1 group-hover:text-brand-violet-light"
              />
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Actions */}
      <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
        <button onClick={handleDownload} className="btn-primary inline-flex items-center gap-2">
          <Download size={16} /> Download Report
        </button>
        <button
          onClick={handleNewInterview}
          className="glass-card inline-flex cursor-pointer items-center gap-2 rounded-xl px-6 py-3 text-sm font-semibold text-ink-primary transition-all hover:border-brand-violet/40 hover:text-white"
        >
          <RotateCcw size={16} /> Start New Interview
        </button>
      </div>
    </div>
  );
}
