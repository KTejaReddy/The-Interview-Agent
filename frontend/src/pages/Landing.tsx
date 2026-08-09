import { useState, useMemo, useRef } from "react";
import { useInterview } from "../context/InterviewContext";
import type { CandidateSummary, Page } from "../types";
import { ErrorBanner } from "../components/ErrorBanner";
import { Navigation } from "../components/Navigation";
import { CandidateCard3D } from "../components/CandidateCard3D";
import { CandidateDrawer } from "../components/CandidateDrawer";
import { useCountUp } from "../hooks/useCountUp";
import { useReveal } from "../hooks/useReveal";
import {
  Users, CalendarDays, MessageSquare, Zap,
  LayoutGrid, ArrowRight, ShieldCheck,
} from "lucide-react";

interface LandingProps {
  onNavigate: (page: Page) => void;
}

// ─── HERO BACKGROUND — cinematic SVG journey paths ──────────
function HeroJourneyArt() {
  return (
    <svg
      className="absolute inset-0 w-full h-full"
      viewBox="0 0 1400 420"
      fill="none"
      preserveAspectRatio="xMidYMid slice"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="hg1" x1="0" y1="0" x2="1400" y2="420" gradientUnits="userSpaceOnUse">
          <stop stopColor="#7c5cff" /><stop offset="0.4" stopColor="#a78bfa" /><stop offset="0.7" stopColor="#22d3ee" /><stop offset="1" stopColor="#14b8a6" />
        </linearGradient>
        <linearGradient id="hg2" x1="0" y1="420" x2="1400" y2="0" gradientUnits="userSpaceOnUse">
          <stop stopColor="#f59e0b" /><stop offset="0.5" stopColor="#fb7185" /><stop offset="1" stopColor="#a78bfa" />
        </linearGradient>
        <linearGradient id="hg3" x1="700" y1="0" x2="700" y2="420" gradientUnits="userSpaceOnUse">
          <stop stopColor="#22d3ee" /><stop offset="1" stopColor="#7c5cff" />
        </linearGradient>
        <filter id="softBlur">
          <feGaussianBlur stdDeviation="1.5" />
        </filter>
      </defs>

      {/* Faint grid */}
      <g opacity="0.04">
        {Array.from({ length: 14 }).map((_, i) => (
          <line key={`v${i}`} x1={i * 100} y1="0" x2={i * 100} y2="420" stroke="white" strokeWidth="1" />
        ))}
        {Array.from({ length: 5 }).map((_, i) => (
          <line key={`h${i}`} x1="0" y1={i * 105} x2="1400" y2={i * 105} stroke="white" strokeWidth="1" />
        ))}
      </g>

      {/* Main journey arc — primary path */}
      <path
        d="M-50,350 C150,280 300,380 500,280 C700,180 850,320 1100,180 C1200,130 1310,160 1450,100"
        stroke="url(#hg1)" strokeWidth="1.5" strokeOpacity="0.5" strokeDasharray="8 12" strokeLinecap="round"
        filter="url(#softBlur)"
      />
      {/* Secondary warm path */}
      <path
        d="M-50,400 C200,340 350,400 550,310 C750,220 900,360 1150,240 C1280,190 1380,220 1450,180"
        stroke="url(#hg2)" strokeWidth="1" strokeOpacity="0.25" strokeDasharray="5 15" strokeLinecap="round"
      />
      {/* Thin cyan path */}
      <path
        d="M200,420 C400,360 600,400 800,300 C1000,200 1200,280 1400,200"
        stroke="url(#hg3)" strokeWidth="0.8" strokeOpacity="0.2" strokeLinecap="round"
      />

      {/* Milestone nodes on the main path */}
      {[
        { cx: 100,  cy: 335, r: 3.5, c: "#7c5cff", label: "Day 1" },
        { cx: 300,  cy: 360, r: 4,   c: "#a78bfa", label: "Day 7" },
        { cx: 500,  cy: 280, r: 5,   c: "#22d3ee", label: "Day 12" },
        { cx: 720,  cy: 220, r: 5,   c: "#22d3ee", label: "Day 16" },
        { cx: 920,  cy: 280, r: 4.5, c: "#a78bfa", label: "Day 22" },
        { cx: 1100, cy: 180, r: 5,   c: "#14b8a6", label: "Day 27" },
        { cx: 1300, cy: 130, r: 6,   c: "#22c55e", label: "Day 31" },
      ].map(({ cx, cy, r, c, label }) => (
        <g key={label}>
          {/* Outer pulse ring */}
          <circle cx={cx} cy={cy} r={r + 5} fill={c} fillOpacity="0.08" />
          {/* Node */}
          <circle cx={cx} cy={cy} r={r} fill={c} fillOpacity="0.9" />
          {/* Label */}
          <text x={cx} y={cy - r - 5} textAnchor="middle" fill={c} fontSize="8" fontFamily="ui-monospace, monospace" fillOpacity="0.7">{label}</text>
        </g>
      ))}

      {/* Floating data fragments — scattered points */}
      {[
        [200, 100, "#a78bfa"], [450, 150, "#22d3ee"], [650, 80, "#7c5cff"],
        [850, 120, "#14b8a6"], [1050, 90, "#f59e0b"], [1200, 70, "#a78bfa"],
        [1350, 110, "#22d3ee"], [80, 200, "#14b8a6"], [380, 60, "#fb7185"],
      ].map(([x, y, c], i) => (
        <circle key={i} cx={x as number} cy={y as number} r="2" fill={c as string} fillOpacity="0.35" />
      ))}
    </svg>
  );
}

// ─── STAT (count-up enabled) ─────────────────────────────────
interface StatProps {
  icon: React.ReactNode;
  value: number;
  suffix?: string;
  label: string;
  accent: string;
  delay?: number;
  decimals?: number;
  staticValue?: string;
}
function StatCard({ icon, value, suffix = "", label, accent, delay = 0, decimals = 0, staticValue }: StatProps) {
  const animated = useCountUp(value, { start: true, decimals });
  return (
    <div className="metric-card animate-fade-up reveal" style={{ animationDelay: `${delay}ms` }}>
      <div className="flex items-center gap-2 mb-2" style={{ color: accent }}>
        {icon}
        <span className="stat-number text-[26px] font-extrabold text-white leading-none tracking-tight">
          {staticValue ?? animated}{suffix && <span className="text-[13px] font-bold text-slate-400 ml-0.5">{suffix}</span>}
        </span>
      </div>
      <span className="text-[9px] font-bold uppercase tracking-[0.18em] text-slate-500">{label}</span>
    </div>
  );
}

// ─── ATMOSPHERIC BACKDROP (shared layer system) ─────────────
function Backdrop() {
  const dots = useMemo(
    () => [
      { top: "12%", left: "8%", delay: "0s" },
      { top: "22%", left: "22%", delay: "-4s" },
      { top: "8%", left: "48%", delay: "-8s" },
      { top: "18%", left: "70%", delay: "-2s" },
      { top: "30%", left: "88%", delay: "-6s" },
      { top: "55%", left: "12%", delay: "-10s" },
      { top: "48%", left: "42%", delay: "-3s" },
      { top: "65%", left: "62%", delay: "-7s" },
      { top: "80%", left: "30%", delay: "-5s" },
      { top: "88%", left: "78%", delay: "-9s" },
    ],
    []
  );
  return (
    <div className="app-backdrop" aria-hidden="true">
      {/* Aurora color fields */}
      <div className="aurora-field" style={{ width: 700, height: 700, top: "-18%", left: "-12%", background: "radial-gradient(circle, rgba(124,92,255,0.16) 0%, transparent 65%)" }} />
      <div className="aurora-field" style={{ width: 620, height: 620, top: "22%", right: "-14%", background: "radial-gradient(circle, rgba(34,211,238,0.10) 0%, transparent 65%)", animationDelay: "-9s" }} />
      <div className="aurora-field" style={{ width: 520, height: 520, bottom: "-10%", left: "28%", background: "radial-gradient(circle, rgba(20,184,166,0.08) 0%, transparent 65%)", animationDelay: "-17s" }} />
      <div className="aurora-field" style={{ width: 420, height: 420, top: "40%", left: "-6%", background: "radial-gradient(circle, rgba(217,70,239,0.07) 0%, transparent 65%)", animationDelay: "-23s" }} />

      {/* Fine technical grid */}
      <div className="tech-grid" />

      {/* Drifting micro-dots */}
      <div className="micro-dots">
        {dots.map((d, i) => (
          <span key={i} className="micro-dot" style={{ top: d.top, left: d.left, animationDelay: d.delay }} />
        ))}
      </div>
    </div>
  );
}

// ─── MAIN PAGE ────────────────────────────────────────────────
export function Landing({ onNavigate }: LandingProps) {
  const { candidates, candidatesLoading, health, error, dismissError, startInterview } = useInterview();
  const rootRef = useRef<HTMLDivElement>(null);
  useReveal(rootRef, [candidatesLoading]);

  const [dossierCandidate, setDossierCandidate] = useState<CandidateSummary | null>(null);

  const curriculumDaysTotal = health?.curriculumDays || 31;
  const realCandidateCount = health?.candidates ?? candidates.length;

  const filteredCandidates = useMemo(() => {
    return [...candidates].sort((a, b) => (b.missionsCompleted ?? 0) - (a.missionsCompleted ?? 0));
  }, [candidates]);

  const handleStart = async (id: string) => {
    setDossierCandidate(null);
    await startInterview(id, "Hi! I'm ready to start.");
    onNavigate("interview");
  };
  const handleDossier = (id: string) => {
    const c = candidates.find(x => x.id === id);
    if (c) setDossierCandidate(c);
  };

  return (
    <div ref={rootRef} className="relative min-h-screen overflow-x-hidden" style={{ background: "var(--ink-900)" }}>
      <Backdrop />
      <div className="grain-overlay" />

      {/* Navigation */}
      <Navigation />

      {/* ── HERO ─────────────────────────────────────────────── */}
      <section
        id="top"
        className="relative overflow-hidden mx-5 mt-2 mb-8 rounded-[var(--radius-xl)] reveal revealed"
        style={{
          background: "linear-gradient(165deg, var(--ink-800) 0%, var(--ink-900) 60%, var(--ink-850) 100%)",
          border: "1px solid rgba(255,255,255,0.07)",
          minHeight: "360px",
          boxShadow: "var(--shadow-2)",
        }}
      >
        {/* Journey art in the background */}
        <div className="absolute inset-0 pointer-events-none" style={{ opacity: 0.9 }}>
          <HeroJourneyArt />
        </div>

        {/* Ambient color wash */}
        <div className="absolute inset-0 pointer-events-none" style={{
          background: "radial-gradient(ellipse 60% 80% at 0% 50%, rgba(124,92,255,0.12) 0%, transparent 60%)",
        }} />
        <div className="absolute inset-0 pointer-events-none" style={{
          background: "radial-gradient(ellipse 50% 60% at 100% 30%, rgba(34,211,238,0.08) 0%, transparent 60%)",
        }} />

        {/* Content */}
        <div className="relative z-10 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-10 px-10 py-12">
          {/* Headline block */}
          <div className="max-w-[600px] animate-fade-up">
            {/* Eyebrow label */}
            <div
              className="inline-flex items-center gap-2 px-3 py-1 rounded-full mb-6 text-[10px] font-bold uppercase tracking-[0.2em]"
              style={{
                background: "rgba(124,92,255,0.12)",
                border: "1px solid rgba(124,92,255,0.28)",
                color: "#b3a6ff",
              }}
            >
              <span className="w-1.5 h-1.5 rounded-full" style={{ background: "#7c5cff", boxShadow: "0 0 6px #7c5cff" }} />
              ABTalks AI Engineering Cohort
            </div>

            <h1
              className="text-white mb-5"
              style={{ fontSize: "clamp(34px, 4.2vw, 58px)", fontWeight: 800, lineHeight: 1.05, letterSpacing: "-0.03em" }}
            >
              Find the right candidate.
              <br />
              <span
                className="text-display-italic text-gradient-ivory"
                style={{ fontSize: "0.9em" }}
              >
                The interview already knows their journey.
              </span>
            </h1>

            <p className="text-slate-400 text-[14.5px] leading-relaxed max-w-[470px]">
              Every question is grounded in what each candidate actually built,
              skipped, struggled with, and mastered across the 31-day cohort —
              delivered by an interviewer that adapts in real time.
            </p>

            {/* CTA row */}
            <div className="flex flex-wrap items-center gap-3 mt-7">
              <a href="#candidates" className="btn btn-primary">
                Start an Interview
                <ArrowRight className="w-4 h-4" />
              </a>
            </div>

            {/* Integrity line */}
            <div className="flex items-center gap-2 mt-5 text-[11px] text-slate-500">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400/80" />
              Assessment integrity protection active
            </div>
          </div>

          {/* Stats — staggered entrance with count-up */}
          <div className="grid grid-cols-2 lg:flex lg:flex-wrap items-stretch gap-3 shrink-0 max-w-[340px] lg:max-w-none">
            <StatCard icon={<Users className="w-4 h-4" />} value={realCandidateCount} label="Candidates" accent="#b3a6ff" delay={100} />
            <StatCard icon={<CalendarDays className="w-4 h-4" />} value={curriculumDaysTotal} label="Curriculum Days" accent="#22d3ee" delay={175} />
            <StatCard icon={<MessageSquare className="w-4 h-4" />} value={10} staticValue="8–10" label="Questions / Interview" accent="#fb7185" delay={250} />
            <StatCard icon={<Zap className="w-4 h-4" />} value={1} staticValue="<1s" label="First Reply" accent="#f59e0b" delay={325} />
          </div>
        </div>
      </section>

      {/* ── MAIN CONTENT ─────────────────────────────────────── */}
      <main className="relative z-10 mx-5 max-w-[1490px]">
        {error && (
          <div className="mb-5">
            <ErrorBanner message={error} onDismiss={dismissError} />
          </div>
        )}

        {/* ── FILTERS & TOOLBAR ────────────────────────────── */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-3 mb-6 animate-fade-up reveal" style={{ animationDelay: "200ms" }}>
          {/* Title label instead of filters */}
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">ABTalks Engineering Cohort Candidates</h2>
          </div>

          {/* Right controls - grid toggle only */}
          <div className="flex items-center gap-2.5">
            <button
              aria-label="Grid view"
              className="p-2 rounded-[10px] text-white transition-all hover:-translate-y-0.5"
              style={{ background: "rgba(255,255,255,0.07)", border: "1px solid rgba(255,255,255,0.08)" }}
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Count line */}
        <p className="text-[11px] text-slate-600 mb-4 font-medium">
          {candidatesLoading ? "Loading candidates…" : `${filteredCandidates.length} candidate${filteredCandidates.length !== 1 ? "s" : ""}`}
        </p>

        {/* ── CANDIDATE GRID ──────────────────────────────── */}
        {candidatesLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(9)].map((_, i) => (
              <div key={i} className="skeleton" style={{ height: "540px" }} />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pb-24" id="candidates">
            {filteredCandidates.map((candidate, i) => (
              <div key={candidate.id} className={`reveal reveal-delay-${Math.min(i, 4)}`}>
                <CandidateCard3D
                  candidate={candidate}
                  curriculumDaysTotal={curriculumDaysTotal}
                  onStartInterview={handleStart}
                  onViewDossier={handleDossier}
                  animationDelay={Math.min(i * 60, 500)}
                />
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Dossier Drawer */}
      <CandidateDrawer
        candidate={dossierCandidate}
        isOpen={dossierCandidate !== null}
        onClose={() => setDossierCandidate(null)}
        onStartInterview={handleStart}
        curriculumDays={curriculumDaysTotal}
      />
    </div>
  );
}
