"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Bot,
  FileText,
  MessagesSquare,
  Users,
  Zap,
} from "lucide-react";
import { getAllCandidates } from "@/lib/candidates";
import { useInterviewStore } from "@/lib/store";
import CandidateCard from "@/components/CandidateCard";

const PARTICLES = [
  { color: "#7C3AED", size: 4 },
  { color: "#06B6D4", size: 3 },
  { color: "#10B981", size: 3 },
  { color: "#9D6FEF", size: 5 },
  { color: "#22D3EE", size: 2 },
];

const HOW_IT_WORKS = [
  {
    icon: Users,
    title: "Pick a profile",
    body: "Choose from 20 real cohort journeys — each one maps to the missions that candidate actually completed across the 31-day program.",
  },
  {
    icon: MessagesSquare,
    title: "Meet Alex",
    body: "A multi-turn technical interview that asks about the candidate's actual work — tools, objectives, and the topics they struggled with.",
  },
  {
    icon: FileText,
    title: "Read the report",
    body: "A structured verdict: overall score, strengths, gaps, and concrete next steps, ready to download.",
  },
];

const STATS = [
  { value: "20", label: "candidate profiles" },
  { value: "31", label: "curriculum days" },
  { value: "8–14", label: "questions per interview" },
  { value: "<1s", label: "first token at Groq speed" },
];

export default function LandingPage() {
  const candidates = useMemo(() => getAllCandidates(), []);
  const setCandidate = useInterviewStore((s) => s.setCandidate);
  const reset = useInterviewStore((s) => s.reset);

  const particles = useMemo(
    () =>
      Array.from({ length: 22 }, (_, i) => {
        const p = PARTICLES[i % PARTICLES.length];
        return {
          id: i,
          left: Math.random() * 100,
          color: p.color,
          size: p.size,
          duration: 10 + Math.random() * 14,
          delay: -Math.random() * 20, // negative delay so particles are mid-flight on load
          opacity: 0.25 + Math.random() * 0.45,
        };
      }),
    []
  );

  const handleSelect = (candidate: (typeof candidates)[number]) => {
    // Fresh session every time a candidate is picked
    reset();
    setCandidate(candidate);
  };

  return (
    <main className="animated-bg min-h-screen">
      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <section className="relative flex flex-col items-center justify-center overflow-hidden px-6 pb-16 pt-20 text-center sm:pb-20 sm:pt-28">
        {/* Floating particles */}
        <div className="pointer-events-none absolute inset-0">
          {particles.map((p) => (
            <span
              key={p.id}
              className="particle"
              style={
                {
                  left: `${p.left}%`,
                  width: p.size,
                  height: p.size,
                  "--p-color": p.color,
                  "--p-duration": `${p.duration}s`,
                  "--p-delay": `${p.delay}s`,
                  "--p-opacity": p.opacity,
                } as React.CSSProperties
              }
            />
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="relative z-10 flex max-w-3xl flex-col items-center"
        >
          <span className="mb-6 inline-flex items-center gap-2 rounded-full border border-brand-violet/30 bg-brand-violet/10 px-4 py-1.5 text-xs font-medium text-brand-violet-light">
            <Zap size={13} className="text-brand-cyan" />
            ABTalks AI Cohort · Technical Assessment
          </span>

          <h1 className="font-display gradient-text animated-gradient-text text-5xl font-bold leading-[1.05] tracking-tight sm:text-7xl">
            The interview that already read their work.
          </h1>

          <p className="mt-6 max-w-xl text-sm leading-relaxed text-ink-secondary sm:text-base">
            Meet <span className="font-semibold text-ink-primary">Alex</span> — an AI
            interviewer who asks about the missions each candidate actually
            completed, probes the topics they struggled with, and closes with a
            structured, score-backed report. Powered by Groq.
          </p>

          {/* Stats strip */}
          <div className="mt-10 grid w-full max-w-2xl grid-cols-2 gap-3 sm:grid-cols-4">
            {STATS.map((s) => (
              <div
                key={s.label}
                className="glass-card flex flex-col items-center gap-0.5 px-3 py-4"
              >
                <span className="font-display text-2xl font-bold text-ink-primary">
                  {s.value}
                </span>
                <span className="text-center text-[10px] uppercase tracking-wider text-ink-muted">
                  {s.label}
                </span>
              </div>
            ))}
          </div>

          <a
            href="#profiles"
            className="btn-primary group mt-10 inline-flex items-center gap-2"
          >
            Start an interview
            <ArrowRight size={16} className="transition-transform group-hover:translate-x-0.5" />
          </a>
        </motion.div>
      </section>

      {/* ── How it works ─────────────────────────────────────────────────── */}
      <section className="relative z-10 mx-auto w-full max-w-6xl px-4 pb-20 sm:px-6">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="mb-8 text-center"
        >
          <h2 className="font-display text-2xl font-bold text-ink-primary sm:text-3xl">
            How it works
          </h2>
          <p className="mx-auto mt-2 max-w-md text-sm text-ink-secondary">
            Three steps from profile to verdict — the whole loop runs in your
            browser at Groq speed.
          </p>
        </motion.div>

        <div className="grid gap-5 sm:grid-cols-3">
          {HOW_IT_WORKS.map((step, i) => (
            <motion.div
              key={step.title}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.45, delay: i * 0.1 }}
              className="glass-card group relative flex flex-col gap-3 p-6 transition-colors hover:border-brand-violet/30"
            >
              <span className="font-mono text-xs font-semibold text-brand-violet-light">
                0{i + 1}
              </span>
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-brand-violet/20 to-brand-cyan/10 text-brand-violet-light ring-1 ring-brand-violet/20 transition-transform duration-300 group-hover:scale-110">
                <step.icon size={20} />
              </div>
              <h3 className="font-display text-lg font-semibold text-ink-primary">
                {step.title}
              </h3>
              <p className="text-sm leading-relaxed text-ink-secondary">{step.body}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── Candidate grid ───────────────────────────────────────────────── */}
      <section id="profiles" className="relative z-10 mx-auto w-full max-w-7xl scroll-mt-8 px-4 pb-24 sm:px-6">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.15 }}
          className="mb-8 flex items-center gap-4"
        >
          <div>
            <h2 className="font-display text-2xl font-bold text-ink-primary">
              Select a Candidate Profile
            </h2>
            <p className="mt-1 text-sm text-ink-secondary">
              Pick a journey — the interview adapts to what they actually built.
            </p>
          </div>
          <span className="hidden h-px flex-1 bg-gradient-to-r from-brand-violet/50 to-transparent sm:block" />
          <span className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 font-mono text-xs text-ink-secondary">
            {candidates.length} candidates
          </span>
        </motion.div>

        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {candidates.map((candidate, i) => (
            <div key={candidate.member.id} onClick={() => handleSelect(candidate)}>
              <CandidateCard candidate={candidate} index={i} />
            </div>
          ))}
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────────────── */}
      <footer className="border-t border-white/5 bg-bg-secondary/60 px-6 py-10">
        <div className="mx-auto flex w-full max-w-7xl flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="flex items-center gap-2 text-sm text-ink-secondary">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-brand-violet to-brand-cyan">
              <Bot size={14} className="text-white" />
            </span>
            AI Interview Agent
          </div>
          <p className="text-center text-xs text-ink-muted">
            Built for the ABTalks AI Cohort hackathon · llama-3.3-70b-versatile on Groq ·
            All candidate data is synthetic
          </p>
        </div>
      </footer>
    </main>
  );
}
