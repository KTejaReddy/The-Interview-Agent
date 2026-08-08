import { useState, useMemo } from "react";
import { useInterview } from "../context/InterviewContext";
import type { CandidateSummary, Page } from "../types";
import { ErrorBanner } from "../components/ErrorBanner";
import { Navigation } from "../components/Navigation";
import { CandidateCard3D } from "../components/CandidateCard3D";
import { CandidateDrawer } from "../components/CandidateDrawer";
import {
  Search, Users, CalendarDays, MessageSquare, Zap,
  SlidersHorizontal, LayoutGrid, ChevronDown,
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
          <stop stopColor="#6366f1" /><stop offset="0.4" stopColor="#a78bfa" /><stop offset="0.7" stopColor="#22d3ee" /><stop offset="1" stopColor="#34d399" />
        </linearGradient>
        <linearGradient id="hg2" x1="0" y1="420" x2="1400" y2="0" gradientUnits="userSpaceOnUse">
          <stop stopColor="#fbbf24" /><stop offset="0.5" stopColor="#fb7185" /><stop offset="1" stopColor="#a78bfa" />
        </linearGradient>
        <linearGradient id="hg3" x1="700" y1="0" x2="700" y2="420" gradientUnits="userSpaceOnUse">
          <stop stopColor="#22d3ee" /><stop offset="1" stopColor="#6366f1" />
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
        stroke="url(#hg1)" strokeWidth="1.5" strokeOpacity="0.45" strokeDasharray="8 12" strokeLinecap="round"
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
        { cx: 100,  cy: 335, r: 3.5, c: "#6366f1", label: "Day 1" },
        { cx: 300,  cy: 360, r: 4,   c: "#a78bfa", label: "Day 7" },
        { cx: 500,  cy: 280, r: 5,   c: "#22d3ee", label: "Day 12" },
        { cx: 720,  cy: 220, r: 5,   c: "#22d3ee", label: "Day 16" },
        { cx: 920,  cy: 280, r: 4.5, c: "#a78bfa", label: "Day 22" },
        { cx: 1100, cy: 180, r: 5,   c: "#34d399", label: "Day 27" },
        { cx: 1300, cy: 130, r: 6,   c: "#34d399", label: "Day 31" },
      ].map(({ cx, cy, r, c, label }) => (
        <g key={label}>
          {/* Outer pulse ring */}
          <circle cx={cx} cy={cy} r={r + 5} fill={c} fillOpacity="0.08" />
          {/* Node */}
          <circle cx={cx} cy={cy} r={r} fill={c} fillOpacity="0.9" />
          {/* Label */}
          <text x={cx} y={cy - r - 5} textAnchor="middle" fill={c} fontSize="8" fontFamily="JetBrains Mono, monospace" fillOpacity="0.7">{label}</text>
        </g>
      ))}

      {/* Floating data fragments — scattered points */}
      {[
        [200, 100, "#a78bfa"], [450, 150, "#22d3ee"], [650, 80, "#6366f1"],
        [850, 120, "#34d399"], [1050, 90, "#fbbf24"], [1200, 70, "#a78bfa"],
        [1350, 110, "#22d3ee"], [80, 200, "#34d399"], [380, 60, "#fb7185"],
      ].map(([x, y, c], i) => (
        <circle key={i} cx={x as number} cy={y as number} r="2" fill={c as string} fillOpacity="0.35" />
      ))}
    </svg>
  );
}

// ─── METRIC CARD ─────────────────────────────────────────────
interface MetricProps {
  icon: React.ReactNode;
  value: string;
  label: string;
  accent: string;
  delay?: number;
}
function MetricCard({ icon, value, label, accent, delay = 0 }: MetricProps) {
  return (
    <div
      className="metric-card animate-fade-up"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-center gap-2 mb-2" style={{ color: accent }}>
        {icon}
        <span className="text-[24px] font-bold text-white leading-none tracking-tight">{value}</span>
      </div>
      <span className="text-[9px] font-bold uppercase tracking-[0.18em] text-slate-500">{label}</span>
    </div>
  );
}

// ─── MAIN PAGE ────────────────────────────────────────────────
export function Landing({ onNavigate }: LandingProps) {
  const { candidates, candidatesLoading, health, error, dismissError, startInterview } = useInterview();

  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<"all" | "strong" | "developing">("all");
  const [sortBy, setSortBy]   = useState<"readiness" | "name" | "missions">("readiness");
  const [dossierCandidate, setDossierCandidate] = useState<CandidateSummary | null>(null);

  const curriculumDaysTotal = health?.curriculumDays || 31;

  const filteredCandidates = useMemo(() => {
    let list = candidates.filter(c => {
      const q = search.toLowerCase();
      if (q && !c.name.toLowerCase().includes(q) && !c.role.toLowerCase().includes(q)) return false;
      const r = c.missionsCompleted ? (c.missionsCompleted / curriculumDaysTotal) * 100 : 0;
      if (filter === "strong"    && r < 70)  return false;
      if (filter === "developing" && r >= 70) return false;
      return true;
    });
    if (sortBy === "readiness" || sortBy === "missions") {
      list = [...list].sort((a, b) => (b.missionsCompleted ?? 0) - (a.missionsCompleted ?? 0));
    } else {
      list = [...list].sort((a, b) => a.name.localeCompare(b.name));
    }
    return list;
  }, [candidates, search, filter, sortBy, curriculumDaysTotal]);

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
    <div className="relative min-h-screen overflow-x-hidden" style={{ background: "#07090f" }}>

      {/* Grain overlay */}
      <div className="grain-overlay" />

      {/* Global atmospheric orbs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden" style={{ zIndex: 0 }}>
        <div className="bg-orb bg-orb-indigo animate-orb-drift"
          style={{ width: 600, height: 600, top: "-15%", left: "-8%", opacity: 0.12 }} />
        <div className="bg-orb bg-orb-cyan animate-orb-drift"
          style={{ width: 500, height: 500, top: "30%", right: "-10%", opacity: 0.09, animationDelay: "-7s" }} />
        <div className="bg-orb bg-orb-violet animate-orb-drift"
          style={{ width: 400, height: 400, bottom: "5%", left: "35%", opacity: 0.07, animationDelay: "-14s" }} />
      </div>

      {/* Navigation */}
      <Navigation />

      {/* ── HERO ─────────────────────────────────────────────── */}
      <section
        className="relative overflow-hidden mx-5 mt-2 mb-8 rounded-[24px]"
        style={{
          background: "linear-gradient(160deg, #0c1020 0%, #090d18 60%, #0a0f1a 100%)",
          border: "1px solid rgba(255,255,255,0.055)",
          minHeight: "340px",
        }}
      >
        {/* Journey art in the background */}
        <div className="absolute inset-0 pointer-events-none" style={{ opacity: 1 }}>
          <HeroJourneyArt />
        </div>

        {/* Ambient color wash */}
        <div className="absolute inset-0 pointer-events-none" style={{
          background: "radial-gradient(ellipse 60% 80% at 0% 50%, rgba(99,102,241,0.10) 0%, transparent 60%)",
        }} />
        <div className="absolute inset-0 pointer-events-none" style={{
          background: "radial-gradient(ellipse 50% 60% at 100% 30%, rgba(6,182,212,0.08) 0%, transparent 60%)",
        }} />

        {/* Content */}
        <div className="relative z-10 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-10 px-10 py-12">
          {/* Headline block */}
          <div className="max-w-[560px] animate-fade-up">
            {/* Eyebrow label */}
            <div
              className="inline-flex items-center gap-2 px-3 py-1 rounded-full mb-5 text-[10px] font-bold uppercase tracking-[0.2em]"
              style={{
                background: "rgba(99,102,241,0.12)",
                border: "1px solid rgba(99,102,241,0.25)",
                color: "#a78bfa",
              }}
            >
              <span
                className="w-1.5 h-1.5 rounded-full"
                style={{ background: "#a78bfa", boxShadow: "0 0 6px #a78bfa" }}
              />
              ABTalks AI Engineering Cohort · 31 Days
            </div>

            <h1
              className="text-white mb-4"
              style={{ fontSize: "clamp(32px, 4vw, 52px)", fontWeight: 800, lineHeight: 1.08, letterSpacing: "-0.03em" }}
            >
              Find the right candidate.
              <br />
              <span
                className="font-serif italic"
                style={{
                  fontSize: "0.82em",
                  fontWeight: 600,
                  background: "linear-gradient(135deg, #818cf8 0%, #a78bfa 40%, #22d3ee 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  backgroundClip: "text",
                }}
              >
                The interview already knows their journey.
              </span>
            </h1>

            <p className="text-slate-400 text-[14px] leading-relaxed max-w-[440px]">
              Select a candidate — the AI interviewer adapts every question
              to what they actually built, skipped, struggled with, and mastered
              across the cohort.
            </p>
          </div>

          {/* Metrics — staggered entrance */}
          <div className="flex flex-wrap lg:flex-nowrap items-start gap-3 shrink-0">
            <MetricCard icon={<Users className="w-4 h-4" />}          value={String(candidates.length || 20)} label="Candidates"      accent="#a78bfa" delay={100} />
            <MetricCard icon={<CalendarDays className="w-4 h-4" />}  value={String(curriculumDaysTotal)}       label="Curriculum Days" accent="#22d3ee" delay={175} />
            <MetricCard icon={<MessageSquare className="w-4 h-4" />} value="8–14"                              label="Questions / Interview" accent="#fb7185" delay={250} />
            <MetricCard icon={<Zap className="w-4 h-4" />}           value="<1s"                               label="First Reply"    accent="#fbbf24" delay={325} />
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
        <div className="flex flex-col md:flex-row items-center justify-between gap-3 mb-6 animate-fade-up" style={{ animationDelay: "200ms" }}>
          {/* Filter tabs */}
          <div
            className="flex items-center gap-1 p-1 rounded-[12px]"
            style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}
          >
            <button
              onClick={() => setFilter("all")}
              className={`filter-tab ${filter === "all" ? "active-all" : ""}`}
            >
              All Candidates
            </button>
            <button
              onClick={() => setFilter("strong")}
              className={`filter-tab ${filter === "strong" ? "active-strong" : ""}`}
            >
              Interview Ready
            </button>
            <button
              onClick={() => setFilter("developing")}
              className={`filter-tab ${filter === "developing" ? "active-needs" : ""}`}
            >
              Needs Practice
            </button>
          </div>

          {/* Right controls */}
          <div className="flex items-center gap-2.5">
            {/* Sort dropdown */}
            <label
              className="relative flex items-center gap-2 px-3 py-2 rounded-[10px] text-[12px] font-medium text-slate-400 cursor-pointer"
              style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)" }}
            >
              <SlidersHorizontal className="w-3.5 h-3.5" />
              <select
                value={sortBy}
                onChange={e => setSortBy(e.target.value as typeof sortBy)}
                className="bg-transparent text-slate-300 font-semibold outline-none cursor-pointer appearance-none pr-4"
              >
                <option value="readiness">Sort: Readiness</option>
                <option value="name">Sort: Name A–Z</option>
                <option value="missions">Sort: Most Missions</option>
              </select>
              <ChevronDown className="w-3 h-3 absolute right-2 pointer-events-none" />
            </label>

            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-600" />
              <input
                type="text"
                placeholder="Search name or role…"
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="w-52 pl-9 pr-3 py-2 rounded-[10px] text-[12px] text-white placeholder:text-slate-600 outline-none transition-all"
                style={{
                  background: "rgba(255,255,255,0.04)",
                  border: "1px solid rgba(255,255,255,0.06)",
                }}
                onFocus={e => { e.currentTarget.style.borderColor = "rgba(99,102,241,0.5)"; e.currentTarget.style.background = "rgba(99,102,241,0.06)"; }}
                onBlur={e  => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.06)"; e.currentTarget.style.background = "rgba(255,255,255,0.04)"; }}
              />
            </div>

            {/* Grid toggle */}
            <button
              className="p-2 rounded-[10px] text-white"
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
              <div
                key={i}
                className="rounded-[20px] animate-pulse"
                style={{ height: "540px", background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.04)" }}
              />
            ))}
          </div>
        ) : filteredCandidates.length === 0 ? (
          <div
            className="text-center py-24 rounded-[20px]"
            style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.05)" }}
          >
            <p className="text-slate-500 text-[15px]">No candidates match your criteria.</p>
            <button onClick={() => { setSearch(""); setFilter("all"); }} className="mt-4 text-indigo-400 text-sm underline">
              Clear filters
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pb-24" id="candidates">
            {filteredCandidates.map((candidate, i) => (
              <CandidateCard3D
                key={candidate.id}
                candidate={candidate}
                curriculumDaysTotal={curriculumDaysTotal}
                onStartInterview={handleStart}
                onViewDossier={handleDossier}
                animationDelay={Math.min(i * 60, 500)}
              />
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
