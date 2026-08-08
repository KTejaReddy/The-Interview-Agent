import { useState, useMemo } from "react";
import { useInterview } from "../context/InterviewContext";
import type { CandidateSummary, Page } from "../types";
import { ErrorBanner } from "../components/ErrorBanner";
import { Navigation } from "../components/Navigation";
import { CandidateCard3D } from "../components/CandidateCard3D";
import { CandidateDrawer } from "../components/CandidateDrawer";
import { Search, Users, CalendarDays, MessageSquare, Zap, SlidersHorizontal, LayoutGrid } from "lucide-react";

interface LandingProps {
  onNavigate: (page: Page) => void;
}

export function Landing({ onNavigate }: LandingProps) {
  const { candidates, candidatesLoading, health, error, dismissError, startInterview } = useInterview();

  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<"all" | "strong" | "developing">("all");
  const [sortBy, setSortBy] = useState<"readiness" | "name" | "missions">("readiness");
  const [dossierCandidate, setDossierCandidate] = useState<CandidateSummary | null>(null);

  const curriculumDaysTotal = health?.curriculumDays || 31;

  const filteredCandidates = useMemo(() => {
    let list = candidates.filter(c => {
      if (search && !c.name.toLowerCase().includes(search.toLowerCase()) && !c.role.toLowerCase().includes(search.toLowerCase())) {
        return false;
      }
      const readiness = c.missionsCompleted ? (c.missionsCompleted / curriculumDaysTotal) * 100 : 0;
      if (filter === "strong" && readiness < 70) return false;
      if (filter === "developing" && readiness >= 70) return false;
      return true;
    });

    // Sort
    if (sortBy === "readiness") {
      list = [...list].sort((a, b) => (b.missionsCompleted ?? 0) - (a.missionsCompleted ?? 0));
    } else if (sortBy === "name") {
      list = [...list].sort((a, b) => a.name.localeCompare(b.name));
    } else if (sortBy === "missions") {
      list = [...list].sort((a, b) => (b.missionsCompleted ?? 0) - (a.missionsCompleted ?? 0));
    }

    return list;
  }, [candidates, search, filter, sortBy, curriculumDaysTotal]);

  const handleStart = async (candidateId: string) => {
    setDossierCandidate(null);
    await startInterview(candidateId, "Hi! I'm ready to start.");
    onNavigate("interview");
  };

  const handleDossier = (candidateId: string) => {
    const c = candidates.find(x => x.id === candidateId);
    if (c) setDossierCandidate(c);
  };

  return (
    <div className="relative min-h-screen bg-[#080b12] selection:bg-indigo-500/30 overflow-x-hidden text-gray-200">

      {/* Rich atmospheric background */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        {/* Subtle grain */}
        <div className="absolute inset-0 opacity-[0.025]" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
          backgroundSize: "180px 180px",
        }} />
        {/* Atmospheric orbs */}
        <div className="absolute top-[-20%] left-[-5%] w-[700px] h-[700px] rounded-full opacity-[0.07] blur-[120px]" style={{ background: "radial-gradient(circle, #6366f1, transparent 70%)" }} />
        <div className="absolute top-[20%] right-[-10%] w-[600px] h-[600px] rounded-full opacity-[0.06] blur-[100px]" style={{ background: "radial-gradient(circle, #06b6d4, transparent 70%)" }} />
        <div className="absolute bottom-[5%] left-[30%] w-[500px] h-[500px] rounded-full opacity-[0.05] blur-[100px]" style={{ background: "radial-gradient(circle, #a78bfa, transparent 70%)" }} />
      </div>

      <Navigation />

      <main className="relative z-10 mx-auto max-w-[1500px] px-5 py-6">
        {error && (
          <div className="mb-6">
            <ErrorBanner message={error} onDismiss={dismissError} />
          </div>
        )}

        {/* ── HERO ─────────────────────────────────────────────────── */}
        <section className="relative mb-10 rounded-[28px] overflow-hidden border border-white/[0.04]"
          style={{ background: "linear-gradient(135deg, #0d1117 0%, #111827 100%)" }}>
          {/* Journey arc SVG */}
          <div className="absolute inset-0 pointer-events-none opacity-[0.12]">
            <svg className="absolute right-0 top-0 w-full h-full" viewBox="0 0 800 300" fill="none" preserveAspectRatio="xMidYMid slice">
              <path d="M800,280 C700,200 600,270 500,180 C400,90 300,160 200,80 C100,0 50,40 0,20"
                stroke="url(#heroGrad1)" strokeWidth="1.5" strokeDasharray="5 5" fill="none" />
              <path d="M800,240 C680,170 580,230 480,150 C380,70 280,130 180,60 C80,-10 30,30 0,10"
                stroke="url(#heroGrad2)" strokeWidth="1" strokeDasharray="3 7" fill="none" />
              <circle cx="500" cy="180" r="4" fill="#6366f1" opacity="0.8" />
              <circle cx="300" cy="160" r="5" fill="#06b6d4" opacity="0.8" />
              <circle cx="200" cy="80" r="3.5" fill="#a78bfa" opacity="0.8" />
              <circle cx="700" cy="200" r="3" fill="#34d399" opacity="0.7" />
              <defs>
                <linearGradient id="heroGrad1" x1="800" y1="280" x2="0" y2="20" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#6366f1" /><stop offset="0.5" stopColor="#06b6d4" /><stop offset="1" stopColor="#34d399" />
                </linearGradient>
                <linearGradient id="heroGrad2" x1="800" y1="240" x2="0" y2="10" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#a78bfa" /><stop offset="1" stopColor="#6366f1" />
                </linearGradient>
              </defs>
            </svg>
          </div>

          <div className="relative z-10 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-10 px-10 py-12">
            <div className="max-w-xl">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-indigo-500/20 bg-indigo-500/10 text-indigo-400 text-[11px] font-bold uppercase tracking-widest mb-5">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
                AI Engineering Cohort · 31 Days
              </div>
              <h1 className="text-4xl md:text-[48px] font-bold text-white leading-[1.08] tracking-tight mb-4">
                Find the right candidate.<br />
                <span className="text-slate-400 font-normal text-[0.85em]">The interview already knows their journey.</span>
              </h1>
              <p className="text-[14px] text-slate-500 leading-relaxed">
                Select a candidate — the AI interviewer adapts every question to what they actually built, skipped, struggled with, and accomplished across the cohort.
              </p>
            </div>

            <div className="flex flex-wrap lg:flex-nowrap items-center gap-3 shrink-0">
              <MetricCard icon={<Users className="w-4 h-4" />} value={String(candidates.length || 20)} label="Candidates" color="#6366f1" />
              <MetricCard icon={<CalendarDays className="w-4 h-4" />} value={String(curriculumDaysTotal)} label="Curriculum Days" color="#06b6d4" />
              <MetricCard icon={<MessageSquare className="w-4 h-4" />} value="8–14" label="Questions" color="#a78bfa" />
              <MetricCard icon={<Zap className="w-4 h-4" />} value="<1s" label="First Reply" color="#f59e0b" />
            </div>
          </div>
        </section>

        {/* ── TOOLBAR ──────────────────────────────────────────────── */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-3 mb-8 px-1">
          {/* Filters */}
          <div className="flex items-center gap-1 p-1 rounded-xl border border-white/[0.06] bg-white/[0.03] backdrop-blur-sm">
            {[
              { id: "all" as const, label: "All Candidates" },
              { id: "strong" as const, label: "Interview Ready" },
              { id: "developing" as const, label: "Needs Practice" },
            ].map(f => (
              <button
                key={f.id}
                onClick={() => setFilter(f.id)}
                className={`px-4 py-2 rounded-lg text-[12px] font-semibold whitespace-nowrap transition-all duration-200 ${filter === f.id
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-white hover:bg-white/[0.06]"
                  }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          {/* Right side controls */}
          <div className="flex items-center gap-3">
            {/* Sort */}
            <div className="flex items-center gap-2 px-3 py-2 rounded-xl border border-white/[0.06] bg-white/[0.03] text-[12px] text-slate-400">
              <SlidersHorizontal className="w-3.5 h-3.5" />
              <select
                value={sortBy}
                onChange={e => setSortBy(e.target.value as typeof sortBy)}
                className="bg-transparent text-slate-300 font-medium outline-none cursor-pointer"
              >
                <option value="readiness">Sort: Readiness</option>
                <option value="name">Sort: Name</option>
                <option value="missions">Sort: Missions</option>
              </select>
            </div>

            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-500" />
              <input
                type="text"
                placeholder="Search candidates..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="w-48 pl-8 pr-3 py-2 bg-white/[0.04] border border-white/[0.06] rounded-xl text-[12px] text-white placeholder:text-slate-600 focus:outline-none focus:border-indigo-500/50 focus:bg-white/[0.06] transition-all"
              />
            </div>

            <div className="flex items-center gap-1 p-1 rounded-xl border border-white/[0.06] bg-white/[0.03]">
              <button className="p-1.5 bg-white/[0.08] rounded-lg text-white">
                <LayoutGrid className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        {/* ── CANDIDATE GRID ───────────────────────────────────────── */}
        <section id="candidates">
          {candidatesLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(9)].map((_, i) => (
                <div key={i} className="h-[520px] rounded-[22px] bg-white/[0.03] animate-pulse border border-white/[0.04]" />
              ))}
            </div>
          ) : filteredCandidates.length === 0 ? (
            <div className="text-center py-24 rounded-[22px] border border-white/[0.05] bg-white/[0.02]">
              <p className="text-slate-500 text-[15px]">No candidates match your search criteria.</p>
            </div>
          ) : (
            <>
              <p className="text-[11px] text-slate-600 mb-4 px-1">
                {filteredCandidates.length} candidate{filteredCandidates.length !== 1 ? "s" : ""} found
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pb-24">
                {filteredCandidates.map(candidate => (
                  <CandidateCard3D
                    key={candidate.id}
                    candidate={candidate}
                    curriculumDaysTotal={curriculumDaysTotal}
                    onStartInterview={handleStart}
                    onViewDossier={handleDossier}
                  />
                ))}
              </div>
            </>
          )}
        </section>
      </main>

      {/* Dossier drawer */}
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

function MetricCard({ icon, value, label, color }: { icon: React.ReactNode; value: string; label: string; color: string }) {
  return (
    <div className="flex flex-col items-center px-5 py-4 rounded-[16px] border border-white/[0.05] bg-white/[0.03] backdrop-blur-sm min-w-[100px]">
      <div className="flex items-center gap-2 mb-1.5" style={{ color }}>
        {icon}
        <span className="text-[22px] font-bold text-white leading-none">{value}</span>
      </div>
      <span className="text-[10px] font-semibold text-slate-600 uppercase tracking-widest">{label}</span>
    </div>
  );
}
